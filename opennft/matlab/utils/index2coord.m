function coord = index2coord(index, dim) 
% Function to perform vector index to 3D volume coordinates conversion.
%
% input:
% index - voxel index within vecor
% dim   - 3D volume dimensions
% 
% output: 
% coord - voxel coordinates within 3D volume
%
% Note,
% [rows, columns, slices] = [dim(1), dim(2), dim(3)]
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

coord = zeros(length(index),3); 
% slice number dim(3)
coord(:,3) = ceil(index/(dim(1)*dim(2))); 
% voxel indices within slice with [dim(1), dim(2)]
index = index - (coord(:,3)-1)*(dim(1)*dim(2)); 
% within slice, dim(1) = slice columns
coord(:,2) = ceil(index/dim(1)); 
% within slice, dim(1) = slice rows 
index = index - (coord(:,2)-1)*(dim(1)); 
                                        
coord(:,1) = index;
