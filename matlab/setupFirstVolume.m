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
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

if strcmp(P.DataType, 'DICOM')
    fDICOM = true;
    fIMAPH = false;
elseif strcmp(P.DataType, 'IMAPH')
    fDICOM = false;
    fIMAPH = true;
else
    fDICOM = false;
    fIMAPH = false;
end

%% Read first Exported Volume, set Dimensions
disp(inpFileName)
% check first Vol
if fDICOM
    dicomInfoVol = dicominfo(inpFileName);
    mxAct      = double(dicomInfoVol.AcquisitionMatrix(1));
    if (mxAct == 0)
        mxAct = double(dicomInfoVol.AcquisitionMatrix(3));
    end
    MatrixSizeX_Act = mxAct;
    dimVol = [MatrixSizeX_Act, MatrixSizeX_Act, double(P.NrOfSlices)];
    [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
        getMosaicDim(dimVol);
    % Optional. It is possible to use mat structure changes to adopt the
    % desired spatial orientation
    %matVol = getMAT(dicomInfoVol, dimVol);
    %dicomInfoVox   = [dicomInfoVol.PixelSpacing; ...
    %                  dicomInfoVol.SpacingBetweenSlices]';
    matTemplMotCorr = mainLoopData.matTemplMotCorr;
    matVol = matTemplMotCorr;
    dicomInfoVox   = sqrt(sum(matTemplMotCorr(1:3,1:3).^2));
end

if fIMAPH
    % get MC tempalte settings for Phillips in case of no proper header
    % of the rt export files
    dimTemplMotCorr = mainLoopData.dimTemplMotCorr;
    matTemplMotCorr = mainLoopData.matTemplMotCorr;
    dicomInfoVox   = sqrt(sum(matTemplMotCorr(1:3,1:3).^2));
    
    dimVol = dimTemplMotCorr;
    [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
        getMosaicDim(dimVol);
    matVol = matTemplMotCorr;
end

nrVoxInVol = prod(dimVol);

%% Init memmapfile transport
% mosaic volume from root matlab to python GUI
initMemmap(P.memMapFile, 'shared', uint8(zeros(img2DdimX, img2DdimY)), ...
    'uint8', 'mmImgViewTempl');

% statVol from root matlab to helper matlab
statVol = zeros(dimVol);
initMemmap(P.memMapFile, 'statVol', zeros(nrVoxInVol,1), 'double', ...
    'mmStatVol', {'double', size(statVol), 'statVol'});

%% transfer background mosaic to Python
imgVolTempl = mainLoopData.imgVolTempl;
imgViewTempl = vol3Dimg2D(imgVolTempl, slNrImg2DdimX, slNrImg2DdimY, ...
    img2DdimX, img2DdimY, dimVol);
imgViewTempl = uint8((imgViewTempl) / max(max(imgViewTempl)) * 255);
assignin('base', 'imgViewTempl', imgViewTempl);

m = evalin('base', 'mmImgViewTempl');
shift = 0 * length(imgViewTempl(:)) + 1;
m.Data(shift:end) = imgViewTempl(:);

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

