function dcmInputData = dcmBegin_Offl(DCM_EN, procTimeSeries, ...
    motCorrRegr, dcmParTag, dcmParOpp)
% Function to add data vectors and regressors to DCM models in the
% beginning of the DCM estimation.
%
% input:
% DCM_EN         - initial DCM structure
% procTimeSeries - processed time-series as provided at the end of OpenNFT
% motCorrRegr    - head-motion residuals
% dcmParTag      - model-defining structure for a target model (model 1)
% dcmParOpp      - model-defining structure for an opposed model (model 2)
%
% output:
% dcmInputData - DCM models structure that contains the set of
%                parameters to estimate both models.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

lTrial = size(motCorrRegr,1);

% set regressors, if necessary
fRegrDcm = 1;
if ~fRegrDcm
    % adding constant, the rest is left to signal processing
    DCM_EN.Y.X0 = [ones(lTrial,1)];
else
    % For DCM feedback, signal processing is just Kalman filter despiking
    % and low-pass filtering. Here we can add motion regressors, linear
    % trend and constant
    DCM_EN.Y.X0 = [zscore(motCorrRegr) zscore([1:lTrial]') ones(lTrial,1)];
end

% set time-series
tmp_xY.name     = 'AMG_L';
tmp_xY.u        = procTimeSeries(1, :)';
tmp_xY.Sess     = 1;
tmp.xY(1)       = tmp_xY;
tmp_xY.name     = 'AMG_R';
tmp_xY.u        = procTimeSeries(2,:)';
tmp_xY.Sess     = 1;
tmp.xY(2)       = tmp_xY;
tmp_xY.name     = 'PFC';
tmp_xY.u        = procTimeSeries(3,:)';
tmp_xY.Sess     = 1;
tmp.xY(3)       = tmp_xY;

DCM_EN.v        = length(tmp_xY.u);
DCM_EN.Y.Q      = spm_Ce(ones(1,DCM_EN.n)*DCM_EN.v);
DCM_EN.xY       = tmp.xY;

% input
for i = 1:DCM_EN.n
    DCM_EN.Y.y(:,i)  = DCM_EN.xY(i).u;
    DCM_EN.Y.name{i} = DCM_EN.xY(i).name;
end

dcmInputData.DCM_EN = DCM_EN;
dcmInputData.dcmParTag = dcmParTag;
dcmInputData.dcmParOpp = dcmParOpp;
