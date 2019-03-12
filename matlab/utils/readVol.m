function [voxelCoord, voxelIntens, voxelIndex, mat, dim, vol] = ...
                                                          readVol(fileName)
% Function to read .nii volume using spm functions.
%
% input:
% fileName - volume file name 
% 
% output: 
% voxelCoord  - voxel coordinates within 3D volume
% voxelIntens - voxel grey-values 
% voxelIndex  - voxel index within vecor
% mat         - volume orientation structure
% dim         - 3D volume dimensions
% vol         - 3D volume
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

volInfo = spm_vol(fileName);
vol = spm_read_vols(volInfo);
mat = volInfo.mat;
dim = volInfo.dim;
vol(isnan(vol)) = 0;
voxelIndex = find(vol~=0);
voxelIntens = vol(voxelIndex);
voxelCoord = index2coord(voxelIndex,dim); 
% voxelIndex_2 = coord2index(voxelCoord,dim);
% vol_2 = zeros(dim);
% vol_2(voxelIndex_2) = voxelIntens;
% figure, imshow(vol(:,:,15))
% figure, imshow(vol_2(:,:,15)) 
