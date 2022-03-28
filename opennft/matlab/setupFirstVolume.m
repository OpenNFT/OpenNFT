function setupFirstVolume(inpFileName)
% Function that collect operations that are required only during the first
% real-time volume processing.
%
% input:
% inpFileName - input file name
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

matTemplMotCorr = mainLoopData.matTemplMotCorr;
        
%% Read first Exported Volume, set Dimensions
disp(inpFileName)

% if used, TCP must be called first to allow standard rt export
if P.UseTCPData
    tcp = evalin('base', 'tcp');
    while ~tcp.BytesAvailable, pause(0.01); end
    [hdr, ~] = tcp.ReceiveScan;
    dimVol = hdr.Dimensions;
    matVol = hdr.mat;
    dicomInfoVox = sqrt(sum(matVol(1:3,1:3).^2));
else
    % check first Vol
    switch P.DataType
        case 'DICOM'
            dicomInfoVol = dicominfo(inpFileName); %spm_dicom_headers(inpFileName); dicomInfoVol = dicomInfoVol{1};
            if dicomInfoVol.NumberOfFrames == 1
                P.isDicom2D = 1;
                mxAct      = double(dicomInfoVol.AcquisitionMatrix(1));
                if (mxAct == 0)
                    mxAct = double(dicomInfoVol.AcquisitionMatrix(3));
                end
                MatrixSizeX_Act = mxAct;
                dimVol = [MatrixSizeX_Act, MatrixSizeX_Act, double(P.NrOfSlices)];
            else
                P.isDicom2D = 0;
                dimVol = [double(dicomInfoVol.Rows), double(dicomInfoVol.Columns), double(dicomInfoVol.NumberOfFrames)];
            end
            if P.getMAT
                matVol = getMAT(dicomInfoVol, dimVol);
                dicomInfoVox   = [dicomInfoVol.PixelSpacing; ...
                    dicomInfoVol.SpacingBetweenSlices]';
            else
                matVol = matTemplMotCorr;
                dicomInfoVox   = sqrt(sum(matTemplMotCorr(1:3,1:3).^2));
            end
        case 'IMAPH'
            % get MC template settings for Phillips in case of no proper header
            % of the rt export files
            dimTemplMotCorr = mainLoopData.dimTemplMotCorr;
            dicomInfoVox   = sqrt(sum(matTemplMotCorr(1:3,1:3).^2));
            
            dimVol = dimTemplMotCorr;
            matVol = matTemplMotCorr;
        case 'NII'
            V = spm_vol(inpFileName);
            dimVol = V.dim;
            matVol = V.mat;
            dicomInfoVox = sqrt(sum(matVol(1:3,1:3).^2));
    end
end
[slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = getMosaicDim(dimVol);
nrVoxInVol = prod(dimVol);

%% Init memmapfile transport
% volume from root matlab to python GUI
initMemmap(P.memMapFile, 'shared', zeros(nrVoxInVol,1), ...
    'double', 'mmImgVolTempl', {'double', dimVol, 'imgVolTempl'});

% statVol from root matlab to helper matlab
statVol = zeros(dimVol);
initMemmap(P.memMapFile, 'statVol', zeros(nrVoxInVol,2), 'double', ...
    'mmStatVol', {'double', size(statVol), 'posStatVol'; 'double', size(statVol), 'negStatVol'});

%% transfer background mosaic to Python
imgVolTempl = mainLoopData.imgVolTempl;
assignin('base', 'imgVolTempl', imgVolTempl);

m = evalin('base', 'mmImgVolTempl');
if P.isZeroPadding
    m.Data.imgVolTempl = imgVolTempl(:,:,P.nrZeroPadVol+1:end-P.nrZeroPadVol);
else
    m.Data.imgVolTempl = imgVolTempl;
end

if P.isRTQA
    mainLoopData.procVol = zeros(dimVol);
end

mainLoopData.dimVol = dimVol;
mainLoopData.matVol = matVol;
mainLoopData.dicomInfoVox = dicomInfoVox;
mainLoopData.img2DdimX = img2DdimX;
mainLoopData.img2DdimY = img2DdimY;
mainLoopData.slNrImg2DdimX = slNrImg2DdimX;
mainLoopData.slNrImg2DdimY = slNrImg2DdimY;
mainLoopData.nrVoxInVol = nrVoxInVol;


assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
end
