function [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
                                                        getMosaicDim(dim3D)
% Function to get dimensions of mosaic image.
%
% input:
% dim3D         - 3D volume dimensions
% 
% output: 
% slNrImg2DdimX - number of slices along row-dimension (2D)
% slNrImg2DdimY - number of slices along column-dimension (2D)
% img2DdimX     - 2D image columns
% img2DdimY     - 2D image rows
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

slNrImg2DdimX = round(sqrt(dim3D(3)));
tmpDim = dim3D(3) - slNrImg2DdimX^2;
if tmpDim == 0
    slNrImg2DdimY = slNrImg2DdimX;
elseif tmpDim > 0
    slNrImg2DdimY = slNrImg2DdimX;
    slNrImg2DdimX = slNrImg2DdimX + 1;    
elseif tmpDim < 0
    % evtl. TODO
    slNrImg2DdimX = slNrImg2DdimX;
    slNrImg2DdimY = slNrImg2DdimX;
end   
img2DdimX = slNrImg2DdimX * dim3D(1);
img2DdimY = slNrImg2DdimY * dim3D(1);  