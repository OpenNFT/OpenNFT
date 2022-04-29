function mat = getMAT(hdr,dim,P)
%
% Function to format brain volume orientation information.
% Note, it is currently disabled in OpenNFT, due to large heterogenity of
% real-time export configurations.
% Note, an end-user is advised to carefully ensure the spatial orientation
% of their real-time data.
%
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Exemplified by Yury Koush, Tibor Auer, and John Ashburner
% (see spm_dicom_header.m and spm_dicom_convert.m)

% Orientation information
%-------------------------------------------------------------------
% Axial Analyze voxel coordinate system:
% x increases     right to left
% y increases posterior to anterior
% z increases  inferior to superior

% DICOM patient coordinate system:
% x increases     right to left
% y increases  anterior to posterior
% z increases  inferior to superior

% T&T coordinate system:
% x increases      left to right
% y increases posterior to anterior
% z increases  inferior to superior

analyze_to_dicom = [diag([1 -1 1]) [0 (dim(2)-1) 0]'; 0 0 0 1]*...
                                                  [eye(4,3) [-1 -1 -1 1]'];

vox    = [hdr.PixelSpacing; hdr.SpacingBetweenSlices];
pos    = hdr.ImagePositionPatient;
orient = reshape(hdr.ImageOrientationPatient,[3 2]);
orient(:,3) = null(orient');
if det(orient) < 0, orient(:,3) = -orient(:,3); end

% The image position vector is not correct. In dicom this vector points to
% the upper left corner of the image. Perhaps it is unlucky that this is
% calculated in the syngo software from the vector pointing to the center
% of the slice (keep in mind: upper left slice) with the enlarged FoV.
dicom_to_patient = [orient*diag(vox) pos ; 0 0 0 1];
truepos          = dicom_to_patient * ...
                        [(double([hdr.Columns hdr.Rows])-dim(1:2))/2 0 1]';
dicom_to_patient = [orient*diag(vox) truepos(1:3) ; 0 0 0 1];
patient_to_tal   = diag([-1 -1 1 1]);
mat              = patient_to_tal * dicom_to_patient * analyze_to_dicom;

if ~P.isDicomSiemensXA30
    % Maybe flip the image depending on SliceNormalVector from 0029,1010
    %-------------------------------------------------------------------
    hdr.CSAImageHeaderInfo = ParseCSA(hdr.Private_0029_1010);
    SliceNormalVector = str2num([hdr.CSAImageHeaderInfo(cellfun(@(x) strcmpi(x,'SliceNormalVector'),{hdr.CSAImageHeaderInfo.name})).item.val]);
    if det([reshape(hdr.ImageOrientationPatient,[3 2]) SliceNormalVector(:)])<0
        mat    = mat*[eye(3) [0 0 -(dim(3)-1)]'; 0 0 0 1];
    end
else
    % TODO for DicomSiemensXA30
end
end

function t = ParseCSA(csavec) % CSA2
if ~all(csavec(1:4)'==[83 86 49 48]) % "SV10"
    t = struct('name','format not supported');
    return
end

NumBytes = numel(csavec);
csavec = csavec';
csavec(1:8) =[]; % unused
[n, csavec] = readCSAvec(csavec,1,'uint32');
if isempty(n) || n>1024 || n < 0
    t = struct('name','Don''t know how to read this damned file format');
    return;
end
csavec(1:4) =[]; % unused
Position = 16;
t(n)     = struct('name','', 'vm',[], 'vr','', 'syngodt',[], 'nitems',[], 'xx',[], 'item',struct('xx',{},'val',{}));
for i=1:n
    [t(i).name, csavec] = readCSAvec(csavec,64,'uint8');
    Position  = Position + 64;
    msk       = find(~t(i).name)-1;
    if ~isempty(msk)
        t(i).name = char(t(i).name(1:msk(1)));
    else
        t(i).name = char(t(i).name);
    end
    [t(i).vm, csavec] = readCSAvec(csavec, 1, 'int32');
    [t(i).vr, csavec] = readCSAvec(csavec, 4, 'uint8');
    t(i).vr      = char(t(i).vr(1:3));
    [t(i).syngodt, csavec] = readCSAvec(csavec, 1, 'int32');
    [t(i).nitems, csavec] = readCSAvec(csavec, 1, 'int32');
    [t(i).xx, csavec] = readCSAvec(csavec, 1, 'int32'); % 77 or 205
    Position     = Position + 20;
    if t(i).nitems > 0
        t(i).item(t(i).nitems) = struct('xx',[], 'val',[]);
    end
    for j=1:t(i).nitems
        [t(i).item(j).xx, csavec] = readCSAvec(csavec,4,'int32'); % [x x 77 x]
        Position         = Position + 16;
        BytesToRead      = t(i).item(j).xx(2);
        if BytesToRead > NumBytes-Position
            BytesToRead      = NumBytes-Position;
            [t(i).item(j).val, csavec] = readCSAvec(csavec, BytesToRead, 'uint8'); t(i).item(j).val = char(t(i).item(j).val);
            [~, csavec] = readCSAvec(csavec,rem(4-rem(BytesToRead, 4), 4), 'uint8');
            t(i).item        = t(i).item(1:j);
            warning('spm:dicom','%s: Problem reading Siemens CSA field.', fopen(FID));
            return;
        end
       [t(i).item(j).val, csavec] = readCSAvec(csavec, BytesToRead, 'uint8'); t(i).item(j).val = char(t(i).item(j).val);
       [~, csavec] = readCSAvec(csavec,rem(4-rem(BytesToRead, 4), 4), 'uint8');
    end
end
end

function [dat,csavec] = readCSAvec(csavec,n,typestr)
nBits = str2double(regexp(typestr,'[0-9]*','match'));
n = n * nBits/8;
dat = typecast(csavec(1:n),typestr);
csavec(1:n) = [];
end
