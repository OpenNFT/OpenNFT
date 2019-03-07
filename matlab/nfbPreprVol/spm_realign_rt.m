function [P, A0, x1, x2, x3, wt, deg, b, nrIter] = ...
   spm_realign_rt(P,flags, indVol, indFirstVol, A0, x1, x2, x3, wt, deg, b)
% Estimation of within modality rigid body movement parameters
% FORMAT P = spm_realign(P,flags)
%
% P     - char array of filenames
%         All operations are performed relative to the first image.
%         ie. Coregistration is to the first image, and resampling
%         of images is into the space of the first image.
%         For multiple sessions, P should be a cell array, where each
%         cell should be a matrix of filenames.
%
% flags - a structure containing various options.  The fields are:
%         quality  - Quality versus speed trade-off.  Highest quality (1)
%                    gives most precise results, whereas lower qualities
%                    gives faster realignment.
%                    The idea is that some voxels contribute little to
%                    the estimation of the realignment parameters.
%                    This parameter is involved in selecting the number
%                    of voxels that are used.
%
%         fwhm     - The FWHM of the Gaussian smoothing kernel (mm) applied
%                    to the images before estimating the realignment
%                    parameters.
%
%         sep      - the default separation (mm) to sample the images.
%
%         rtm      - Register to mean.  If field exists then a two pass
%                    procedure is to be used in order to register the
%                    images to the mean of the images after the first
%                    realignment.
%
%         wrap     - Directions in the volume whose values should wrap
%                    around in. For example, in MRI scans, the images wrap
%                    around in the phase encode direction, so (e.g.) the
%                    subject's nose may poke into the back of the subject's
%                    head.
%
%         PW       -  a filename of a weighting image (reciprocal of
%                    standard deviation).  If field does not exist, then
%                    no weighting is done.
%
%         interp   - B-spline degree used for interpolation
%
%         graphics - display coregistration outputs
%                    default: ~spm('CmdLine')
%
%__________________________________________________________________________
%
% If no output argument, then an updated voxel to world matrix is written
% to the headers of the images (a .mat file is created for 4D images).
% The details of the transformation are displayed in the results window as
% plots of translation and rotation.
% A set of realignment parameters are saved for each session, named:
% rp_*.txt.
%__________________________________________________________________________
%
% Voxel to world mapping:
%
% These are simply 4x4 affine transformation matrices represented in the
% NIFTI headers (see http://nifti.nimh.nih.gov/nifti-1 ).
% These are normally modified by the `realignment' and `coregistration'
% modules.  What these matrices represent is a mapping from the voxel
% coordinates (x0,y0,z0) (where the first voxel is at coordinate (1,1,1)),
% to coordinates in millimeters (x1,y1,z1).
%  
% x1 = M(1,1)*x0 + M(1,2)*y0 + M(1,3)*z0 + M(1,4)
% y1 = M(2,1)*x0 + M(2,2)*y0 + M(2,3)*z0 + M(2,4)
% z1 = M(3,1)*x0 + M(3,2)*y0 + M(3,3)*z0 + M(3,4)
%
% Assuming that image1 has a transformation matrix M1, and image2 has a
% transformation matrix M2, the mapping from image1 to image2 is: M2\M1
% (ie. from the coordinate system of image1 into millimeters, followed
% by a mapping from millimeters into the space of image2).
%
% These matrices allow several realignment or coregistration steps to be
% combined into a single operation (without the necessity of resampling the
% images several times).
%__________________________________________________________________________
%
% Reference:
%
% Friston KJ, Ashburner J, Frith CD, Poline J-B, Heather JD & Frackowiak
% RSJ (1995) Spatial registration and normalization of images Hum. Brain
% Map. 2:165-189
%__________________________________________________________________________
% Copyright (C) 1994-2013 Wellcome Trust Centre for Neuroimaging

% John Ashburner
% $Id: spm_realign.m 6070 2014-06-26 20:53:39Z guillaume $

% SVNid = '$Rev: 6070 $';
 
% P  - a vector of volumes (see spm_vol)
%--------------------------------------------------------------------------
% P(i).mat is modified to reflect the modified position of the image i.
% The scaling (and offset) parameters are also set to contain the
% optimum scaling required to match the images.
%__________________________________________________________________________

% Adopted for OpenNFT by Yury Koush and John Ashburner. 
% Copyright (C) 2016-2019 OpenNFT.org

%
% Real-time computational modifications. 
% Note, to speed up the computations,
% 'Coef' are transferred to the spm_reslice_rt, whcih implies
% 1) that exactly the same step in reslice is disabled, and
% 2) that interpolation specified in realign will be 'used'
% by default for the same step of Coef estimation during reslice
% (see smooth_vol() occurences).
% We recommend using the same interpolation for real-time adaptations of
% the realign and reslice functions.

% If flag is set to false, the SPM standard realignment and reslicing could
% be reproduced with the high precision. This results in longer ~3-7 sec
% processing of the first volume and a significant reduction of volume
% preprocessing time on each iteration. Relatively long processing of the
% first volume may require a longer first baseline block or alternative
% solutions when higher preprocessing speed is required, e.g. TR = 500ms.
fNFB = true; 

lkp  = flags.lkp;
if indVol == indFirstVol
    
    skip = sqrt( sum(P(1).mat(1:3,1:3) .^ 2) ) .^ (-1) * flags.sep;
    d    = P(1).dim(1:3);                                                                                                                        
    st   = rand('state'); 
    rand('state',0); 
    if d(3) < 3
        lkp  = [1 2 6];
        [x1,x2,x3] = ndgrid(1:skip(1):d(1)-0.5, ...
                            1:skip(2):d(2)-0.5, ...
                            1:skip(3):d(3)    );
        x1   = x1 + rand(size(x1)) * 0.5;
        x2   = x2 + rand(size(x2)) * 0.5;
    else
        [x1,x2,x3] = ndgrid(1:skip(1):d(1)-0.5, ...
                            1:skip(2):d(2)-0.5, ...
                            1:skip(3):d(3)-0.5);
        x1   = x1 + rand(size(x1)) * 0.5;
        x2   = x2 + rand(size(x2)) * 0.5;
        x3   = x3 + rand(size(x3)) * 0.5; 
    end
    rand('state',st); % rng(st);

    x1 = x1(:);
    x2 = x2(:);
    x3 = x3(:);

    %-Possibly mask an area of the sample volume.
    %----------------------------------------------------------------------
    if ~isempty(flags.PW)
        [y1,y2,y3] = coords([0 0 0  0 0 0],P(1).mat,flags.PW.mat,x1,x2,x3);
        wt  = spm_sample_vol(flags.PW, y1, y2, y3, 1);
        msk = find(wt > 0.01);
        x1  = x1(msk);
        x2  = x2(msk);
        x3  = x3(msk);
        wt  = wt(msk);
    else
        wt  = [];
    end

    %-Compute rate of change of chi2 w.r.t changes in parameters (matrix A)
    %----------------------------------------------------------------------
    [V, P(1).C] = smooth_vol(P(1), flags.interp, flags.wrap, flags.fwhm);
    deg = [flags.interp*[1 1 1]' flags.wrap(:)];

    [G, dG1, dG2, dG3] = spm_bsplins(V, x1, x2, x3, deg);
    clear V
    A0  = make_A(P(1).mat, x1, x2, x3, dG1, dG2, dG3, wt, lkp);

    b   = G;
    if ~isempty(wt), b = b .* wt; end

    % Remove voxels that contribute very little to the final estimate.
    % Simulated annealing or something similar could be used to
    % eliminate a better choice of voxels - but this way will do for
    % now. It basically involves removing the voxels that contribute
    % least to the determinant of the inverse covariance matrix.

    % This step requires a time to converge for the first volume, however,
    % it speeds up the real-time computations by 100ms or more. If the
    % first baseline block is lomg, this step could be used, however it is
    % disabled for now.
    if ~fNFB
        Alpha = [A0 b];
        Alpha = Alpha' * Alpha;
        det0  = det(Alpha);
        det1  = det0;
        spm_plot_convergence('Set', det1 / det0);
        while det1/det0 > flags.quality
            dets  = zeros(size(A0,1), 1);
            for i=1:size(A0,1)
                tmp     = [A0(i,:) b(i)];
                dets(i) = det(Alpha - tmp' * tmp);
            end;
            clear tmp
            [junk, msk] = sort(det1-dets);
            msk        = msk(1:round(length(dets)/10));
             A0(msk,:) = [];   b(msk,:) = [];   G(msk,:) = [];
             x1(msk,:) = [];  x2(msk,:) = [];  x3(msk,:) = [];
            dG1(msk,:) = []; dG2(msk,:) = []; dG3(msk,:) = [];
            if ~isempty(wt),  wt(msk,:) = []; end;
            Alpha = [A0 b];
            Alpha = Alpha' * Alpha;
            det1  = det(Alpha);
        end;    
    end
    
end
            
%-Loop over images
%--------------------------------------------------------------------------
% control over accuracy and number of iterations
if fNFB
    thAcc = 0.01;
    nrIter = 10;
else
    % SPM defualt:
    thAcc = 1e-8;
    nrIter = 64;
end

[V, P(2).C] = smooth_vol(P(2), flags.interp, flags.wrap, flags.fwhm);
d  = [size(V) 1 1];
d  = d(1:3);
ss = Inf;
countdown = -1;
for iter=1:nrIter
    [y1, y2, y3] = coords([0 0 0  0 0 0],P(1).mat, P(2).mat, x1, x2, x3);
    msk = find( y1>=1 & y1<=d(1) & y2>=1 & y2<=d(2) & y3>=1 & y3<=d(3) );
    if length(msk) < 32, error_message(P(2)); end

    F = spm_bsplins(V, y1(msk), y2(msk), y3(msk), deg);
    if ~isempty(wt), F = F .* wt(msk); end

    if fNFB
        if iter == 1
            fixA0 = A0' * A0;
        end
    end
    A          = A0(msk,:);
    b1         = b(msk);
    sc         = sum(b1) / sum(F);
    b1         = b1 - F * sc;
    if ~fNFB
        soln       = (A' * A) \ (A' * b1);
    else
        soln       = fixA0 \ (A' * b1);
    end

    p          = [0 0 0  0 0 0  1 1 1  0 0 0];
    p(lkp)     = p(lkp) + soln';
    P(2).mat   = spm_matrix(p) \ P(2).mat;

    pss        = ss;
    ss         = sum(b1 .^ 2) / length(b1);
    if ((pss-ss)/pss < thAcc) && (countdown == -1) % Stopped converging.
        countdown = 2;
    end
    if countdown ~= -1
        if countdown==0, break; end
        countdown = countdown -1;
    end
end

nrIter = iter;
    
%==========================================================================
% function [y1,y2,y3]=coords(p,M1,M2,x1,x2,x3)
%==========================================================================
function [y1, y2, y3]=coords(p, M1, M2, x1, x2, x3)
% Rigid body transformation of a set of coordinates
M  = inv(M2) * inv(spm_matrix(p)) * M1;
y1 = M(1,1)*x1 + M(1,2)*x2 + M(1,3)*x3 + M(1,4);
y2 = M(2,1)*x1 + M(2,2)*x2 + M(2,3)*x3 + M(2,4);
y3 = M(3,1)*x1 + M(3,2)*x2 + M(3,3)*x3 + M(3,4);


%==========================================================================
% function V = smooth_vol(P,hld,wrp,fwhm)
%==========================================================================
function [V, Coef] = smooth_vol(P, hld, wrp, fwhm)
% function V = smooth_vol(P,hld,wrp,fwhm)
% Convolve the volume in memory
s  = sqrt(sum(P.mat(1:3,1:3) .^2)) .^ (-1) * (fwhm / sqrt(8 * log(2)));
x  = round(6 * s(1)); x = -x:x;
y  = round(6 * s(2)); y = -y:y;
z  = round(6 * s(3)); z = -z:z;
x  = exp(-(x) .^ 2 / (2 * s(1) .^ 2));
y  = exp(-(y) .^ 2 / (2 * s(2) .^ 2));
z  = exp(-(z) .^ 2 / (2 * s(3) .^ 2));
x  = x/sum(x);
y  = y/sum(y);
z  = z/sum(z);

i  = (length(x) - 1)/2;
j  = (length(y) - 1)/2;
k  = (length(z) - 1)/2;
d  = [hld*[1 1 1]' wrp(:)];

Coef  = spm_bsplinc(P.Vol, d); 
V = zeros(size(P.Vol));
spm_conv_vol(Coef, V, x, y, z, -[i j k]);

%==========================================================================
% function A = make_A(M,x1,x2,x3,dG1,dG2,dG3,wt,lkp)
%==========================================================================
function A = make_A(M, x1, x2, x3, dG1, dG2, dG3, wt, lkp)
% Matrix of rate of change of weighted difference w.r.t. parameter changes
p0 = [0 0 0  0 0 0  1 1 1  0 0 0];
A  = zeros(numel(x1), length(lkp));
for i=1:length(lkp)
    pt         = p0;
    pt(lkp(i)) = pt(i) + 1e-6;
    [y1,y2,y3] = coords(pt, M, M, x1, x2, x3);
    tmp        = sum([y1-x1 y2-x2 y3-x3] .* [dG1 dG2 dG3], 2) / (-1e-6);
    if ~isempty(wt)
        A(:,i) = tmp .* wt;
    else
        A(:,i) = tmp; 
    end
end

%==========================================================================
% function error_message(P)
%==========================================================================
function error_message(P)
str = {'There is not enough overlap in the images to obtain a solution.',...
       ' ',...
       'Offending image:',...
       P.fname,...
       ' ',...
       'Please check that your header information is OK.',...
       'The Check Reg utility will show you the initial',...
       'alignment between the images, which must be',...
       'within about 4cm and about 15 degrees in order',...
       'for SPM to find the optimal solution.'};
spm('alert*',str,mfilename,sqrt(-1));
error('Insufficient image overlap.');


