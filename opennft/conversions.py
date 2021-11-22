import numpy as np


def img2d_vol3d(img2d, xdim_img_number, ydim_img_number, dim3d):
    sl = 0
    vol3d = np.zeros(dim3d)
    for sy in range(0, ydim_img_number):
        for sx in range(0, xdim_img_number):
            if sl > dim3d[2]:
                break
            else:
                vol3d[:, :, sl] = img2d[sy * dim3d[0]: (sy + 1) * dim3d[0], sx * dim3d[0]: (sx + 1) * dim3d[0]]
            vol3d[:, :, sl] = np.rot90(vol3d[:, :, sl], 3)
            sl += 1

    return vol3d


def vol3d_img2d(vol3d, sl_nr_img2d_dimx, sl_nr_img2d_dimy, xdim_img_number, ydim_img_number, dim3d):
    sl = 0
    img2d = np.zeros((ydim_img_number, xdim_img_number))

    for sy in range(0, sl_nr_img2d_dimy):
        for sx in range(0, sl_nr_img2d_dimx):
            if sl > dim3d[2]:
                break
            else:
                img2d[sy * dim3d[1]:(sy + 1) * dim3d[1], sx * dim3d[0]:(sx + 1) * dim3d[0]] = np.rot90(vol3d[:, :, sl])
            sl += 1

    return img2d


def get_mosaic_dim(dim3d):
    xdim_img_number = round(np.sqrt(dim3d[2]))
    tmp_dim = dim3d[2] - xdim_img_number ** 2

    if tmp_dim == 0:
        ydim_img_number = xdim_img_number
    else:
        if tmp_dim > 0:
            ydim_img_number = xdim_img_number
            xdim_img_number += 1
        else:
            xdim_img_number = xdim_img_number
            ydim_img_number = xdim_img_number

    img2d_dimx = xdim_img_number * dim3d[0]
    img2d_dimy = ydim_img_number * dim3d[0]

    return xdim_img_number, ydim_img_number, img2d_dimx, img2d_dimy
