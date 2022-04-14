function [mat, dim, vol] = readVol(fileName)
% Function to read .nii volume using spm functions.
%
% input:
% fileName - volume file name
%
% output:
% voxelCoord  - voxel coordinates within 3D volume
% voxelIndex  - voxel index within vector
% mat         - volume orientation structure
% dim         - 3D volume dimensions
% vol         - 3D volume
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

volInfo = spm_vol(fileName);
vol = spm_read_vols(volInfo);
mat = volInfo.mat;
dim = volInfo.dim;
vol(isnan(vol)) = 0;
