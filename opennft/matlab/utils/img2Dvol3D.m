function vol3D = img2Dvol3D(img2D, slNrImg2DdimX, slNrImg2DdimY, dim3D)
% Function to perform 2D to 3D conversion.
%
% input:
% img2D         - 2D image matrix
% slNrImg2DdimX - number of slices along row-dimension (2D)
% slNrImg2DdimY - number of slices along column-dimension (2D)
% img2DdimX     - 2D image columns
% img2DdimY     - 2D image rows
% dim3D         - 3D volume dimensions
% 
% output: 
% vol3D         - 3D image volume
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

sl = 0;
vol3D = zeros(dim3D);
for sy  = 0:slNrImg2DdimY-1
    for sx = 0:slNrImg2DdimX-1
        sl = sl+1;
        if sl>dim3D(3), break, else
            vol3D(:,:,sl)= img2D(sy * dim3D(1) + 1:(sy+1) * dim3D(1), ...
                                 sx * dim3D(1) + 1:(sx+1) * dim3D(1));
        end
        vol3D(:,:,sl) = rot90(vol3D(:,:,sl),3);
    end
end