function epiWholeBrainROI()
% Function to select whole-brain ROI based on fixed EPI template used for
% realignment and assigns ROI information structures.
% Note, Phillips data could be corrupted, e.g. without hearder info,
% flipped, etc.
% End user is advised to check ROIs, EPI template and rt time-series for
% spatial orientation.
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush and Nikita Davydov

P = evalin('base', 'P');
flags = getFlagsType(P);

mainLoopData = evalin('base', 'mainLoopData');
imgVolTempl          = mainLoopData.imgVolTempl;
dimTemplMotCorr      = mainLoopData.dimTemplMotCorr;
matTemplMotCorr      = mainLoopData.matTemplMotCorr;

[slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = getMosaicDim(dimTemplMotCorr);

if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
    iFile = P.NrROIs;
    if evalin('base','exist(''ROIs'')')
        ROIs = evalin('base','ROIs');
    else
        ROIs = [];
    end
    if ~isfield(P,'DynROI')
        P.DynROI = false;
    end
    P.ROINames(iFile) = {'Whole brain'};
elseif flags.isDCM
    iFile = 1;
end

ROIs(iFile).mat = matTemplMotCorr;
ROIs(iFile).dim = dimTemplMotCorr;

% smooth EPI template
dicomInfoVox = sqrt(sum(matTemplMotCorr(1:3,1:3).^2));
gKernel = [8 8 8] ./ dicomInfoVox;
smImgVolTempl = zeros(dimTemplMotCorr);
spm_smooth(imgVolTempl, smImgVolTempl, gKernel);

% mask voxels
wholeBrainMaskThreshold = 30;
smImgVolTempl(smImgVolTempl<wholeBrainMaskThreshold) = nan;

if 0
    % check thresholded template
    mosaicSmImgVolTempl = vol3Dimg2D(smImgVolTempl, slNrImg2DdimX, ...
        slNrImg2DdimY, img2DdimX, img2DdimY, ROIs(iFile).dim);
    figure, imshow(mosaicSmImgVolTempl,[])
end

% histohram
nbins = 2^nextpow2(max(smImgVolTempl(:)));
[N,edges] = histcounts(smImgVolTempl,1:nbins);

% histogram fit with single exponent and single gaussian
fun = @(b,x) b(1)*exp(-x*b(2)) + b(3)*exp(-(x - b(4)).^2/b(5));

% data
xdata = edges(wholeBrainMaskThreshold:end-1);
lxdata = length(xdata);
ydata = N(wholeBrainMaskThreshold:end);

% fit
maxiter = 200;
tolfun = 1e-10;
cf = [ydata(1), .001, 10, round(lxdata/2), 10];
lb = [1, 0, 0, 5, nbins/10, nbins/100];
ub = [inf, inf, inf, lxdata, inf];
maxfuneval = maxiter*(length(cf)+1);
opt = optimset('Tolfun',tolfun,'MaxFunEval',maxfuneval,'MaxIter',...
    maxiter,'Display','iter','DiffMinChange',1e-8);

fitResults = lsqcurvefit(fun,cf,xdata,ydata,lb,ub,opt);

threshEpiWholeBrainMask = round(fitResults(4)/2);

% get mask
epiWholeBrainMask = zeros(dimTemplMotCorr);
indexEpiWholeBrainMask = find(smImgVolTempl>threshEpiWholeBrainMask);
epiWholeBrainMask(indexEpiWholeBrainMask) = 1;

% display histogram and mask
if 0
    xfit = wholeBrainMaskThreshold:nbins;
    figure,plot(xdata,ydata,'k.'),hold on,
    plot(xfit,fun(fitResults,xfit),'b-', 'linewidth', 2)

    mosaicEpiWholeBrainMask = vol3Dimg2D(epiWholeBrainMask, slNrImg2DdimX, ...
        slNrImg2DdimY, img2DdimX, img2DdimY, ROIs(iFile).dim);
    figure, imshow(mosaicEpiWholeBrainMask)
end

% assign ROI
ROIs(iFile).vol = epiWholeBrainMask;
ROIs(iFile).voxelIndex = indexEpiWholeBrainMask;
ROIs(iFile).voxelCoord = index2coord(indexEpiWholeBrainMask,dimTemplMotCorr);


% DVARS scaling is most frequent image value given fit
P.scaleFactorDVARS = median(smImgVolTempl(indexEpiWholeBrainMask));

assignin('base', 'P', P);
assignin('base', 'ROIs', ROIs);