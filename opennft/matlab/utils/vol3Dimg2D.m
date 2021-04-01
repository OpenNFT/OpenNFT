function img2D = vol3Dimg2D(vol3D, slNrImg2DdimX, slNrImg2DdimY, ...
                            img2DdimX, img2DdimY, dim3D)
% Function to perform 3D to 2D conversion.
%
% input:
% vol3D         - 3D image volume
% slNrImg2DdimX - number of slices along row-dimension (2D)
% slNrImg2DdimY - number of slices along column-dimension (2D)
% img2DdimX     - 2D image columns
% img2DdimY     - 2D image rows
% dim3D         - 3D volume dimensions
% 
% output: 
% img2D - 2D image matrix
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

sl = 0;
img2D = zeros(img2DdimY, img2DdimX);
for sy  = 0:slNrImg2DdimY-1
    for sx = 0:slNrImg2DdimX-1
        sl = sl+1;
        if sl > dim3D(3), break, else
            img2D(sy*dim3D(2) + 1:(sy+1)*dim3D(2), ...
                  sx*dim3D(1) + 1:(sx+1)*dim3D(1)) = rot90(vol3D(:,:,sl));
        end
    end
end
