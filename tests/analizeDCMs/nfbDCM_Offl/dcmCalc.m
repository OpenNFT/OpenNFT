function LE = dcmCalc(modelName, dcmInputData)
% Case-sensitive wrapper to estiamte Target and Opposed models
%
% input:
% modelName    - name of the DCM model
% dcmInputData - DCM models structure that contains the set of
%                parameters to estimate both models.
% output:
% LE - Free-energy bound on log evidence (DCM.F)
%__________________________________________________________________________
% Copyright (C) 2016-2017 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

if strcmp(modelName, 'Tag')
    dcmPar = dcmInputData.dcmParTag;
elseif strcmp(modelName, 'Opp')
    dcmPar = dcmInputData.dcmParOpp;
end

dcmOutputData = dcmEst(dcmInputData.DCM_EN, dcmPar);
LE = dcmOutputData.LE;
end

function outputData = dcmEst(DCM_EN, dcmPar)
% DCM computation
DCM_EN.a = dcmPar.dcm.a;
DCM_EN.b = dcmPar.dcm.b;
DCM_EN.c = dcmPar.dcm.c;

% select between SPM8 and SPM12
isSPM8 = 0;
if isSPM8
    [DCM, dcmRT] = spm_dcm_estimate_rt_spm8(DCM_EN);
else
    [DCM, dcmRT] = spm_dcm_estimate_rt_spm12(DCM_EN);
end

outputData.DCM_EN = DCM_EN;
outputData.DCM    = DCM;
outputData.LE     = DCM.F;
outputData.TIME   = [sum(dcmRT.time) mean(dcmRT.time)];
outputData.ITER   = dcmRT.Iter;
end
