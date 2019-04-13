function mat = getMAT(hdr,dim)
%
% Function to format brain volume orientation information.
% Note, it is currently disabled in OpenNFT, due to large heterogenity of
% real-time export comnfigurations.
% Note, an end-user is adviced to carefully ensure the spatial orientation 
% of their real-time data.
%
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Exemplified by Yury Koush and John Ashburner 
% (see spm_dicom_convert.m)

% Orientation information
%-------------------------------------------------------------------
% Axial Analyze voxel co-ordinate system:
% x increases     right to left
% y increases posterior to anterior
% z increases  inferior to superior

% DICOM patient co-ordinate system:
% x increases     right to left
% y increases  anterior to posterior
% z increases  inferior to superior

% T&T co-ordinate system:
% x increases      left to right
% y increases posterior to anterior
% z increases  inferior to superior

analyze_to_dicom = [diag([1 -1 1]) [0 (dim(2)-1) 0]'; 0 0 0 1]*...
                                                  [eye(4,3) [-1 -1 -1 1]'];

vox    = [hdr.PixelSpacing; hdr.SpacingBetweenSlices];
pos    = hdr.ImagePositionPatient;
orient = reshape(hdr.ImageOrientationPatient,[3 2]);
orient(:,3) = null(orient');
if det(orient) < 0, orient(:,3) = -orient(:,3); end;

% The image position vector is not correct. In dicom this vector points to
% the upper left corner of the image. Perhaps it is unlucky that this is
% calculated in the syngo software from the vector pointing to the center 
% of the slice (keep in mind: upper left slice) with the enlarged FoV.
dicom_to_patient = [orient*diag(vox) pos ; 0 0 0 1];
truepos          = dicom_to_patient * ...
                        [(double([hdr.Width hdr.Height])-dim(1:2))/2 0 1]';
dicom_to_patient = [orient*diag(vox) truepos(1:3) ; 0 0 0 1];
patient_to_tal   = diag([-1 -1 1 1]);
mat              = patient_to_tal * dicom_to_patient * analyze_to_dicom;

% Maybe flip the image depending on SliceNormalVector from 0029,1010
%-------------------------------------------------------------------
% SliceNormalVector = read_SliceNormalVector(hdr);
% if det([reshape(hdr.ImageOrientationPatient,[3 2]) SliceNormalVector(:)])<0;
%     volume = volume(:,:,end:-1:1);
%     mat    = mat*[eye(3) [0 0 -(dim(3)-1)]'; 0 0 0 1];
% end;
