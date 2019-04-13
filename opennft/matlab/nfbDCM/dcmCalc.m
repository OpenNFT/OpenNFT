function LE = dcmCalc(modelName)
% Case-sensitive wrapper to estiamte Target and Opposed models
%
% input:
% modelName - name of the DCM model
%
% output:
% LE - Free-energy bound on log evidence (DCM.F)
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

loadedData = load([tempdir, 'dcmInputData.mat']);
dcmInputData = loadedData.dcmInputData;

if strcmp(modelName, 'Tag')
    dcmPar = dcmInputData.dcmParTag;
elseif strcmp(modelName, 'Opp')
    dcmPar = dcmInputData.dcmParOpp;
end

dcmOutputData = dcmEst(dcmInputData.DCM_EN, dcmPar);
LE = dcmOutputData.LE;
end

function outputData = dcmEst(DCM_EN, dcmPar)
% Function to estiamte a single DCM model
DCM_EN.a = dcmPar.dcm.a;
DCM_EN.b = dcmPar.dcm.b;
DCM_EN.c = dcmPar.dcm.c;

[DCM, dcmRT] = spm_dcm_estimate_rt_spm12(DCM_EN);

outputData.DCM_EN = DCM_EN;
outputData.DCM    = DCM;
outputData.LE     = DCM.F;
outputData.TIME   = [sum(dcmRT.time) mean(dcmRT.time)];
outputData.ITER   = dcmRT.Iter;
end
