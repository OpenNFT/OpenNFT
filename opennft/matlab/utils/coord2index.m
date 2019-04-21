function index = coord2index(coord,dim)
% Function to transform from 3D volume coordinates to vector index.
%
% input:
% coord - voxel coordinates within 3D volume
% dim   - 3D volume dimensions
% 
% output: 
% index - voxel index within vecor
%
% Note,
% [rows, columns, slices] = [dim(1), dim(2), dim(3)]
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

index = zeros(size(coord,1));
index = coord(:,1) + ...
       (coord(:,2)-1)*(dim(1)) + ...
       (coord(:,3)-1)*(dim(1)*dim(2));
