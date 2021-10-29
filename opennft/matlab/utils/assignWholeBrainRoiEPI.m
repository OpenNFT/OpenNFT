function assignWholeBrainRoiEPI()

P = evalin('base', 'P');
flags = getFlagsType(P);

infoVolTempl = spm_vol(P.MCTempl);
imgVolTempl  = spm_read_vols(infoVolTempl);
dimTemplMotCorr     = infoVolTempl.dim;
matTemplMotCorr     = infoVolTempl.mat;

[slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = getMosaicDim(dimTemplMotCorr);

if flags.isPSC || flags.isSVM || flags.isCorr || P.isRestingState
    iFile = P.NrROIs;
    ROIs = evalin('base','ROIs');
elseif flags.isDCM
    iFile = 1;
end

ROIs(iFile).mat = matTemplMotCorr;
ROIs(iFile).dim = dimTemplMotCorr;
ROIs(iFile).vol = imgVolTempl;

maskThreshold = P.wholeBrainMaskThreshold;

ROIs(iFile).vol(ROIs(iFile).vol < maskThreshold) = 0;
ROIs(iFile).vol(ROIs(iFile).vol >= maskThreshold) = 1;

ROIs(iFile).voxelIndex = find(ROIs(iFile).vol == 1);

ROIs(iFile).mask2D = vol3Dimg2D(ROIs(iFile).vol, slNrImg2DdimX, ...
             slNrImg2DdimY, img2DdimX, img2DdimY, ROIs(iFile).dim);

assignin('base', 'P', P);
assignin('base', 'ROIs', ROIs);