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
            mxAct      = double(dicomInfoVol.AcquisitionMatrix(1));
            if (mxAct == 0)
                mxAct = double(dicomInfoVol.AcquisitionMatrix(3));
            end
            MatrixSizeX_Act = mxAct;
            dimVol = [MatrixSizeX_Act, MatrixSizeX_Act, double(P.NrOfSlices)];
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
% mosaic volume from root matlab to python GUI
initMemmap(P.memMapFile, 'shared', uint8(zeros(img2DdimX, img2DdimY)), ...
    'uint8', 'mmImgViewTempl');

% statVol from root matlab to helper matlab
statVol = zeros(dimVol);
initMemmap(P.memMapFile, 'statVol', zeros(nrVoxInVol,2), 'double', ...
    'mmStatVol', {'double', size(statVol), 'posStatVol'; 'double', size(statVol), 'negStatVol'});

if P.isRTQA
    rtqaVol = zeros(dimVol);
    initMemmap(P.memMapFile, 'RTQAVol', zeros(nrVoxInVol,1), 'double', ...
        'mmrtQAVol', {'double', size(rtqaVol), 'rtQAVol'});
end

% mosaic stat map to python GUI
initMemmap(P.memMapFile, 'statMap', uint8(zeros(img2DdimX*img2DdimY, 1)), 'uint8', ...
    'mmStatMap', {'uint8', [img2DdimX, img2DdimY], 'statMap'; });
initMemmap(P.memMapFile, 'statMap_neg', uint8(zeros(img2DdimX*img2DdimY, 1)), 'uint8', ...
    'mmStatMap_neg', {'uint8', [img2DdimX, img2DdimY], 'statMap_neg' });

map_template = zeros(img2DdimX,img2DdimY);
m_out =  evalin('base', 'mmStatMap');
m_out.Data.statMap = uint8(map_template);
assignin('base', 'statMap', map_template);

m_out =  evalin('base', 'mmStatMap_neg');
m_out.Data.statMap_neg = uint8(map_template);
assignin('base', 'statMap_neg', map_template);


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

