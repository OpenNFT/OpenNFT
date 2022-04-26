import numpy as np
import multiprocessing as mp
import nibabel as nib
import cv2
import pydicom
from scipy import linalg
from rtspm import spm_imatrix, spm_matrix, spm_slice_vol
from opennft.conversions import img2d_vol3d, vol3d_img2d, get_mosaic_dim
from opennft.mapimagewidget import MapImageThresholdsCalculator, RgbaMapImage, Thresholds


class VolViewFormation(mp.Process):

    def __init__(self, input, output):
        mp.Process.__init__(self)
        self.str_param = dict([])

        self.input_data = input
        self.output_data = output

        self.thr_calculator = MapImageThresholdsCalculator(no_value=0.0)
        self.pos_image = RgbaMapImage(colormap='hot', no_value=0.0)
        self.neg_image = RgbaMapImage(colormap='Blues_r', no_value=0.0)

        self.mat_epi = self.input_data["mat"]
        self.dim = self.input_data["dim"]

        self.xdim, self.ydim, self.img2d_dimx, self.img2d_dimy = get_mosaic_dim(self.dim)
        self.output_data["mosaic_templ"] = np.zeros((self.img2d_dimx, self.img2d_dimy))
        self.output_data["mosaic_pos_overlay"] = None
        self.output_data["mosaic_neg_overlay"] = None

        if not (self.input_data["anat_volume"] is None):
            anat_name = self.input_data["anat_volume"]
            anat_data = nib.load(anat_name, mmap=False)
            self.anat_volume = np.array(anat_data.get_fdata(), order="F")
            self.mat_anat = anat_data.affine

        epi_name = self.input_data["epi_volume"]

        if self.input_data["epi_volume_type"] == "nii":
            self.epi_volume = np.array(nib.load(epi_name, mmap=False).get_fdata(), order="F")
        else:
            epi_volume = np.array(pydicom.dcmread(epi_name).pixel_array, order='F')
            if epi_volume.ndim == 2:
                xdim_img_number, ydim_img_number, img2d_dimx, img2d_dimy = get_mosaic_dim(self.dim)
                self.epi_volume = np.array(img2d_vol3d(epi_volume, xdim_img_number, ydim_img_number, self.dim), order='F')
            else:
                self.epi_volume = epi_volume


        # ROIs
        if self.input_data["is_ROI"]:
            self.ROI_vols = np.array(self.input_data["ROI_vols"], order='F')
            self.ROI_mats = np.array(self.input_data["ROI_mats"], order='F')
        else:
            self.ROI_vols = []
            self.ROI_mats = []

        self.prepare_orth_view(self.mat_epi, self.dim)

    def run(self):

        np.seterr(divide='ignore', invalid='ignore')

        while not self.input_data["is_stopped"]:

            ready = self.input_data["ready"]
            
            if ready:

                if self.input_data["view_mode"] == 0:

                    img_vol = np.array(np.memmap(self.input_data["memmap_volume"], dtype=np.float64, shape=self.dim, order='F'))
                    max_vol = np.max(img_vol)
                    min_vol = np.min(img_vol)
                    img_vol = (img_vol - min_vol) / (max_vol - min_vol)
                    self.output_data["mosaic_templ"] = vol3d_img2d(img_vol, self.xdim, self.ydim,
                                                                   self.img2d_dimx, self.img2d_dimy, self.dim)

                    self.input_data["done_mosaic_templ"] = True

                    if self.input_data["overlay_ready"]:
                        if self.input_data["is_rtqa"]:
                            overlay_vol = self.input_data["rtQA_volume"]
                            overlay_img = vol3d_img2d(overlay_vol, self.xdim, self.ydim,
                                                      self.img2d_dimx, self.img2d_dimy, self.dim)
                            overlay_img = (overlay_img / np.max(overlay_img)) * 255
                        else:
                            filename = self.input_data["stat_volume"]
                            overlay_vol = np.memmap(filename, dtype=np.float64, shape=self.input_data["dim"], offset=0, order='F')
                            overlay_img = vol3d_img2d(overlay_vol, self.xdim, self.ydim,
                                                      self.img2d_dimx, self.img2d_dimy, self.dim)
                            overlay_img = (overlay_img / np.max(overlay_img)) * 255

                            if self.input_data["is_neg"]:
                                neg_overlay_vol = np.memmap(filename, dtype=np.float64, shape=self.input_data["dim"],
                                                            offset=overlay_vol.size * overlay_vol.data.itemsize, order='F')
                                neg_overlay_img = vol3d_img2d(neg_overlay_vol, self.xdim, self.ydim,
                                                              self.img2d_dimx, self.img2d_dimy, self.dim)
                                neg_overlay_img = (neg_overlay_img / np.max(neg_overlay_img)) * 255

                        if self.input_data["auto_thr_pos"]:
                            pos_thr = self.thr_calculator(overlay_img)
                            if pos_thr.lower < 0:
                                pos_thr = Thresholds(0, pos_thr.upper)
                            self.output_data["pos_thresholds"] = pos_thr
                        else:
                            pos_thr = self.output_data["pos_thresholds"]
                        self.output_data["mosaic_pos_overlay"] = self.pos_image(overlay_img, pos_thr, 1.0)

                        if self.input_data["is_neg"]:
                            if self.input_data["auto_thr_neg"]:
                                neg_thr = self.thr_calculator(neg_overlay_img)
                                if neg_thr.lower < 0:
                                    neg_thr = Thresholds(0, neg_thr.upper)
                                self.output_data["neg_thresholds"] = neg_thr
                            else:
                                neg_thr = self.output_data["neg_thresholds"]
                            self.output_data["mosaic_neg_overlay"] = self.neg_image(neg_overlay_img, neg_thr, 1.0)

                        self.input_data["done_mosaic_overlay"] = True


                else:

                    flags = [self.input_data["bg_type"], self.input_data["is_rtqa"],
                             self.input_data["is_neg"], self.input_data["is_ROI"]]

                    # background
                    if flags[0] == "bgEPI":
                        back_volume = self.epi_volume
                        mat = self.mat_epi
                    else:
                        back_volume = self.anat_volume
                        mat = self.mat_anat

                    # overlay (pos/neg stat or rtQA)
                    if flags[1]:
                        overlay_vol = self.input_data["rtQA_volume"]
                        neg_overlay_vol = []
                    else:
                        filename = self.input_data["stat_volume"]
                        overlay_vol = np.memmap(filename, dtype=np.float64, shape=self.input_data["dim"],
                                                        offset=0, order='F')
                        if flags[2]:
                            neg_overlay_vol = np.memmap(filename, dtype=np.float64, shape=self.input_data["dim"],
                                                        offset=overlay_vol.size*overlay_vol.data.itemsize, order='F')
                        else:
                            neg_overlay_vol = []

                    ROI_vols = self.ROI_vols
                    ROI_mats = self.ROI_mats

                    cursor_pos = self.input_data["cursor_pus"]
                    flags_planes = self.input_data["flags_planes"]

                    proj = np.nonzero(flags_planes)

                    new_coord = np.array([[0, 0],[0, 0],[0, 0]])
                    new_coord[proj,:] = cursor_pos

                    self.str_param['centre'] = self.findcent(new_coord, flags_planes)
                    # Display modes: [Background + Stat + ROIs, Background + Stat, Background + ROIs]
                    self.str_param['mode_displ'] = [1, 0, 0]

                    [self.output_data["back_t"], self.output_data["back_c"], self.output_data["back_s"],
                     self.output_data["overlay_t"], self.output_data["overlay_c"], self.output_data["overlay_s"],
                     self.output_data["neg_overlay_t"], self.output_data["neg_overlay_c"], self.output_data["neg_overlay_s"],
                     self.output_data["ROI_t"], self.output_data["ROI_c"], self.output_data["ROI_s"]
                    ] = self.update_orth_view(back_volume, mat, overlay_vol, neg_overlay_vol, ROI_vols, ROI_mats, flags)

                    pos_maps_values = np.array(self.output_data["overlay_t"].ravel(), dtype=np.uint8)
                    pos_maps_values = np.append(pos_maps_values, self.output_data["overlay_c"].ravel())
                    pos_maps_values = np.append(pos_maps_values, self.output_data["overlay_s"].ravel())
                    if self.input_data["auto_thr_pos"]:
                        pos_thr = self.thr_calculator(pos_maps_values)
                        if (not pos_thr is None) and pos_thr.lower < 0:
                            pos_thr = Thresholds(0, pos_thr.upper)
                        self.output_data["pos_thresholds"] = pos_thr
                    else:
                        pos_thr = self.output_data["pos_thresholds"]
                    self.output_data["overlay_t"] = self.pos_image(self.output_data["overlay_t"], pos_thr, 1.0)
                    self.output_data["overlay_c"] = self.pos_image(self.output_data["overlay_c"], pos_thr, 1.0)
                    self.output_data["overlay_s"] = self.pos_image(self.output_data["overlay_s"], pos_thr, 1.0)

                    if self.input_data["is_neg"]:
                        neg_maps_values = np.array(self.output_data["neg_overlay_t"].ravel(), dtype=np.uint8)
                        neg_maps_values = np.append(neg_maps_values, self.output_data["neg_overlay_c"].ravel())
                        neg_maps_values = np.append(neg_maps_values, self.output_data["neg_overlay_s"].ravel())
                        if self.input_data["auto_thr_neg"]:
                            neg_thr = self.thr_calculator(neg_maps_values)
                            if (not neg_thr is None) and neg_thr.lower < 0:
                                neg_thr = Thresholds(0, neg_thr.upper)
                            self.output_data["neg_thresholds"] = neg_thr
                        else:
                            neg_thr = self.output_data["neg_thresholds"]
                        self.output_data["neg_overlay_t"] = self.neg_image(self.output_data["neg_overlay_t"],
                                                                           neg_thr, 1.0)
                        self.output_data["neg_overlay_c"] = self.neg_image(self.output_data["neg_overlay_c"],
                                                                           neg_thr, 1.0)
                        self.output_data["neg_overlay_s"] = self.neg_image(self.output_data["neg_overlay_s"],
                                                                           neg_thr, 1.0)

                    self.input_data["done_orth"] = True

                self.input_data["ready"] = False

    def prepare_orth_view(self, mat, dim):
        # set structure for Display and draw a first overlay
        self.str_param = {'n': 0, 'bb': [], 'space': np.eye(4, 4), 'centre': np.zeros((1, 3)), 'mode': 1,
                     'area': np.array([0, 0, 1, 1]), 'premul': np.eye(4, 4), 'hld': 1, 'mode_displ': np.zeros((1, 3))}

        temp = np.array([0, 0, 0, 0, np.pi, -np.pi / 2])
        self.str_param['space'] = spm_matrix(temp) @ self.str_param['space']

        # get bounding box and resolution
        if len(self.str_param['bb']) == 0:
            self.str_param['max_bb'] = self.max_bb(mat, dim, self.str_param['space'], self.str_param['premul'])
            self.str_param['bb'] = self.str_param['max_bb']

        self.str_param['space'], self.str_param['bb'] = self.resolution(mat, self.str_param['space'], self.str_param['bb'])

        # Draw at initial location, center of bounding box
        temp = np.vstack((self.str_param['max_bb'].T, [1, 1]))
        mmcentre = np.mean(self.str_param['space'] @ temp, 1)
        self.str_param['centre'] = mmcentre[0:3]
        # Display modes: [Background + Stat + ROIs, Background + Stat, Background + ROIs]
        self.str_param['mode_displ'] = np.array([0, 0, 1])

    def update_orth_view(self, vol, mat, overlay_vol, neg_overlay_vol, ROI_vols, ROI_mats, flags):

        bb = self.str_param['bb']
        dims = np.squeeze(np.round(np.diff(bb, axis=0).T + 1))
        _is = np.linalg.inv(self.str_param['space'])
        cent = _is[0:3, 0:3] @ self.str_param['centre'] + _is[0:3, 3]

        m = np.array(np.linalg.solve(self.str_param['space'], self.str_param['premul']) @ mat, order='F')
        tm0 = np.array([
            [1, 0, 0, -bb[0, 0] + 1],
            [0, 1, 0, -bb[0, 1] + 1],
            [0, 0, 1, -cent[2]],
            [0, 0, 0, 1],

        ])
        td = np.array([dims[0], dims[1]], dtype=int, order='F')

        cm0 = np.array([
            [1, 0, 0, -bb[0, 0] + 1],
            [0, 0, 1, -bb[0, 2] + 1],
            [0, 1, 0, -cent[1]],
            [0, 0, 0, 1],
        ])
        cd = np.array([dims[0], dims[2]], dtype=int, order='F')

        if self.str_param['mode'] == 0:
            sm0 = np.array([
                [0, 0, 1, -bb[0, 2] + 1],
                [0, 1, 0, -bb[0, 1] + 1],
                [1, 0, 0, -cent[0]],
                [0, 0, 0, 1],
            ])
            sd = np.array([dims[2], dims[1]], dtype=int, order='F')
        else:
            sm0 = np.array([
                [0, -1, 0, +bb[1, 1] + 1],
                [0, 0, 1, -bb[0, 2] + 1],
                [1, 0, 0, -cent[0]],
                [0, 0, 0, 1],
            ])
            sd = np.array([dims[1], dims[2]], dtype=int, order='F')

        coord_param = {'tm0': tm0, 'cm0': cm0, 'sm0': sm0, 'td': td, 'cd': cd, 'sd': sd}

        back_imgt, back_imgc, back_imgs = self.get_orth_vol(coord_param, vol, m)

        back_imgt = np.nan_to_num(back_imgt)
        back_imgt[back_imgt < 0] = 0

        back_imgc = np.nan_to_num(back_imgc)
        back_imgc[back_imgc < 0] = 0

        back_imgs = np.nan_to_num(back_imgs)
        back_imgs[back_imgs < 0] = 0

        back_imgt = ((back_imgt / np.max(back_imgt)) * 255)
        back_imgc = ((back_imgc / np.max(back_imgc)) * 255)
        back_imgs = ((back_imgs / np.max(back_imgs)) * 255)

        if flags[0] != "bgEPI":
            m = np.array(np.linalg.solve(self.str_param['space'], self.str_param['premul']) @ self.mat_epi, order='F')

        overlay_imgt, overlay_imgc, overlay_imgs = self.get_orth_vol(coord_param, overlay_vol, m)
        overlay_imgt = np.nan_to_num(overlay_imgt)
        overlay_imgc = np.nan_to_num(overlay_imgc)
        overlay_imgs = np.nan_to_num(overlay_imgs)
        overlay_imgt = ((overlay_imgt / np.max(overlay_imgt)) * 255)
        overlay_imgc = ((overlay_imgc / np.max(overlay_imgc)) * 255)
        overlay_imgs = ((overlay_imgs / np.max(overlay_imgs)) * 255)

        if flags[3]:
            neg_overlay_imgt, neg_overlay_imgc, neg_overlay_imgs = self.get_orth_vol(coord_param, neg_overlay_vol, m)
            neg_overlay_imgt = np.nan_to_num(neg_overlay_imgt)
            neg_overlay_imgc = np.nan_to_num(neg_overlay_imgc)
            neg_overlay_imgs = np.nan_to_num(neg_overlay_imgs)
            neg_overlay_imgt = ((neg_overlay_imgt / np.max(neg_overlay_imgt)) * 255)
            neg_overlay_imgc = ((neg_overlay_imgc / np.max(neg_overlay_imgc)) * 255)
            neg_overlay_imgs = ((neg_overlay_imgs / np.max(neg_overlay_imgs)) * 255)

        else:
            neg_overlay_imgt = None
            neg_overlay_imgc = None
            neg_overlay_imgs = None

        nrROIs = self.input_data["nr_ROIs"]
        ROI_t = [None]*nrROIs
        ROI_c = [None]*nrROIs
        ROI_s = [None]*nrROIs

        if bool(self.str_param["mode_displ"]) and flags[3]:

            for j in range(nrROIs):

                vol = np.array(np.squeeze(ROI_vols[j,:,:,:]), order='F')
                mat = np.array(np.squeeze(ROI_mats[j,:,:]), order='F')
                m = np.array(np.linalg.solve(self.str_param['space'], self.str_param['premul']) @ mat, order='F')
                temp_t, temp_c, temp_s = self.get_orth_vol(coord_param, vol, m)

                ROI_t[j] = self.roi_boundaries(temp_t)
                ROI_c[j] = self.roi_boundaries(temp_c)
                ROI_s[j] = self.roi_boundaries(temp_s)

        return back_imgt, back_imgc, back_imgs, overlay_imgt, overlay_imgc, overlay_imgs, neg_overlay_imgt, neg_overlay_imgc, neg_overlay_imgs, ROI_t, ROI_c, ROI_s

    def roi_boundaries(self, roi):
        roi[np.isnan(roi)] = 0
        contours, _ = cv2.findContours(roi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            boundaries = [None] * len(contours)
            for i in range(len(contours)):
                boundaries[i] = contours[i].squeeze()
        else:
            boundaries = np.array([])

        return boundaries

    def get_orth_vol(self, coord_param, vol, m):
        temp = np.array([0, np.nan], order='F')

        mat_t = np.array(linalg.inv(coord_param['tm0'] @ m), order='F')
        imgt = np.zeros((coord_param['td'][0], coord_param['td'][1]), order='F')
        spm_slice_vol(vol, imgt, mat_t, temp)
        imgt = imgt.T

        mat_c = np.array(linalg.inv(coord_param['cm0'] @ m), order='F')
        imgc = np.zeros((coord_param['cd'][0], coord_param['cd'][1]), order='F')
        spm_slice_vol(vol, imgc, mat_c, temp)
        imgc = imgc.T

        mat_s = np.array(linalg.inv(coord_param['sm0'] @ m), order='F')
        imgs = np.zeros((coord_param['sd'][0], coord_param['sd'][1]), order='F')
        spm_slice_vol(vol, imgs, mat_s, temp)
        imgs = np.fliplr(imgs.T)

        return imgt, imgc, imgs

    def findcent(self, coord_loc, flags_planes):

        centre = np.array([])
        cent = np.array([])
        cp = np.array([])

        for j in range(3):
            if flags_planes[j]: # new coordinates on Transverse
                cp = np.array(coord_loc[j,:],ndmin=2)
            if cp.size > 0:
                cp = cp[0,0:2]
                _is = np.linalg.inv(self.str_param['space'])
                cent = _is[0:3, 0:3] @ self.str_param['centre'] + _is[0:3, 3]
                if j == 0: # click was on Transverse: s and t need to change
                    cent[0] = cp[0] + self.str_param['bb'][0,0] - 1
                    cent[1] = cp[1] + self.str_param['bb'][0,1] - 1
                elif j == 1: # click was on Saggital: t and c need to change
                    cent[0] = cp[0] + self.str_param['bb'][0,0] - 1
                    cent[2] = cp[1] + self.str_param['bb'][0,2] - 1
                elif j == 2: # click was on Coronal: t and s need to change
                    if self.str_param['mode'] == 0:
                        cent[2] = cp[0] + self.str_param['bb'][0,2] - 1
                        cent[1] = cp[1] + self.str_param['bb'][0,1] - 1
                    else:
                        cent[1] = cp[0] - self.str_param['bb'][1,1] - 1
                        cent[2] = cp[1] + self.str_param['bb'][0,2] - 1
                break

        if cent.size>0:
            centre = self.str_param['space'][0:3,0:3] @ cent[:] + self.str_param['space'][0:3,3]

        return centre

    def max_bb(self, mat, dim, space, premul):

        mn = np.array([np.inf] * 3, ndmin=2)
        mx = -mn
        premul = np.linalg.solve(space, premul)
        bb, vx = self.get_bbox(mat, dim, premul)
        mx = np.vstack((bb, mx)).max(0)
        mn = np.vstack((bb, mx)).min(0)
        bb = np.vstack((mn, mx))

        return bb

    def get_bbox(self, mat, dim, premul):
        p = spm_imatrix(mat)
        vx = p[6:9]

        corners = np.array([
            [1, 1, 1, 1],
            [1, 1, dim[2], 1],
            [1, dim[1], 1, 1],
            [1, dim[1], dim[2], 1],
            [dim[0], 1, 1, 1],
            [dim[0], 1, dim[2], 1],
            [dim[0], dim[1], 1, 1],
            [dim[0], dim[1], dim[2], 1],

        ]).T

        xyz = mat[0:3, :] @ corners

        xyz = premul[0:3, :] @ np.vstack((xyz, np.ones((1, xyz.shape[1]))))

        bb = np.array([
            np.min(xyz, axis=1).T,
            np.max(xyz, axis=1).T
        ])

        return bb, vx

    def resolution(self, mat, space, bb):
        res_default = 1

        temp = (np.sum((mat[0:3, 0:3]) ** 2, axis=0) ** .5)
        res = np.min(np.hstack((res_default, temp)))

        u, s, v = np.linalg.svd(space[0:3, 0:3])
        temp = np.mean(s)
        res = res / temp

        mat = np.diag([res, res, res, 1])

        space = space @ mat
        bb = bb / res

        return space, bb
