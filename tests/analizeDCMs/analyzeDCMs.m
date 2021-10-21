function logBF_Offl = analyzeDCMs(idxTrials, parametersFileName,...
    spmFileName, timeseriesFileName)
% Function to re-calculate offline the DCM models used in OpenNFT, or test
% your own models prior to integration into OpenNFT.
%
% input:
% idxTrials          - trial index
% parametersFileName - parameters structure file name
% spmFileName        - SPM structure file name
% timeseriesFileName - time-series file name, at the end of the DCM
%                      feedback run.
%
% output:
% logBF_Offl         - logBF value calculated post-hoc (offline)
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

% P - parameters structure as produced by OpenNFT at the end of the DCM
% feedback run.
P = load(parametersFileName);
load(timeseriesFileName);
load(spmFileName);

% loop across trials
for iTrial = idxTrials
    % indices of the data and regressors input,
    % period of P.lengthDCMTrial = 108
    idxTrial = [(iTrial-1)*P.lengthDCMTrial + 1 : iTrial*P.lengthDCMTrial];
    
    trialMotRegr = P.motCorrParam(idxTrial, :);
    trialTimeSeries = kalmanProcTimeSeries(:, idxTrial);
    
    % set DCMs
    [DCM_EN, dcmParTag, dcmParOpp] = dcmPrep(SPM);
    dcmInputData = dcmBegin_Offl(DCM_EN, trialTimeSeries, ...
        trialMotRegr, dcmParTag, dcmParOpp);
    
    % calculate DCMs
    LE_Tag = dcmCalc('Tag', dcmInputData);
    LE_Opp = dcmCalc('Opp', dcmInputData);
    logBF_Offl(iTrial) = LE_Tag - LE_Opp;
    
    % clear after both DCMs per trial are computed
    clear DCM_EN dcmInputData dcmParTag dcmParOpp ...
        idxTrial trialTimeSeries trialMotRegr
end
