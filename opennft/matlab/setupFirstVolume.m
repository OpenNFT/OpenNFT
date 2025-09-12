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
if P.isGE
    P.DataType = 'GE'; % YKWIP
end
[vol, matVol, dimVol] = getVolData(P.DataType, inpFileName, 0, P.getMAT, P.UseTCPData);
if P.getMAT
    dicomInfoVox   = [dicomInfoVol.PixelSpacing; dicomInfoVol.SpacingBetweenSlices]';
else
    dicomInfoVox   = sqrt(sum(matTemplMotCorr(1:3,1:3).^2));
end
[slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = getMosaicDim(dimVol);
nrVoxInVol = prod(dimVol);

%% transfer background mosaic to Python
imgVolTempl = mainLoopData.imgVolTempl;
assignin('base', 'imgVolTempl', imgVolTempl);

m = evalin('base', 'mmTransferVol');
if P.isZeroPadding
    m.Data.transferVol = imgVolTempl(:,:,P.nrZeroPadVol+1:end-P.nrZeroPadVol);
else
    m.Data.transferVol = imgVolTempl;
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
