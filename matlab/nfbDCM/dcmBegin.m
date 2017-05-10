function calculateDcm = dcmBegin(indVol)
% Function to add data vectors and regressors to DCM models in the
% beginning of the DCM estimation.
%
% input:
% indVol - volume(scan) index
%
% output:
% dcmInputData - final DCM models structure that contains the set of
%                parameters to estimate both models.
%__________________________________________________________________________
% Copyright (C) 2016-2017 OpenNFT.org
%
% Written by Yury Koush

calculateDcm = false;

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

if indVol <= P.nrSkipVol
    return
end

indVolNorm = mainLoopData.indVolNorm;

if ~mainLoopData.flagEndDCM
    
    calculateDcm = ~isempty(find(P.endDCMblock == (indVol-P.nrSkipVol),1));
    
    if calculateDcm
        
        DCM_EN = mainLoopData.DCM_EN;
        
        lTrial = P.lengthDCMTrial;
        trialOffset     = lTrial - 1;
        vectDcmTrial    = indVolNorm - trialOffset : indVolNorm;
        
        % set regressors
        if ~P.fRegrDcm
            % adding constant, the rest is left to signal processing
            DCM_EN.Y.X0 = ones(lTrial, 1);
        else
            % For DCM feedback, signal processing is just Kalman filter
            % despiking and low-pass filtering. Here we can add motion
            % regressors, linear trend and constant
            DCM_EN.Y.X0 = [zscore(P.motCorrParam(vectDcmTrial, :)) ...
                zscore([1:lTrial]') ones(lTrial, 1)];
        end
        
        % set time-series
        tmp_xY.name  = 'AMG_L';
        tmp_xY.u     = mainLoopData.kalmanProcTimeSeries(1, vectDcmTrial)';
        tmp_xY.Sess  = 1;
        tmp.xY(1)    = tmp_xY;
        tmp_xY.name  = 'AMG_R';
        tmp_xY.u     = mainLoopData.kalmanProcTimeSeries(2, vectDcmTrial)';
        tmp_xY.Sess  = 1;
        tmp.xY(2)    = tmp_xY;
        tmp_xY.name  = 'PFC';
        tmp_xY.u     = mainLoopData.kalmanProcTimeSeries(3, vectDcmTrial)';
        tmp_xY.Sess  = 1;
        tmp.xY(3)    = tmp_xY;
        
        DCM_EN.v     = length(tmp_xY.u);
        DCM_EN.Y.Q   = spm_Ce(ones(1, DCM_EN.n) * DCM_EN.v);
        DCM_EN.xY    = tmp.xY;
        
        % input
        for i = 1:DCM_EN.n
            DCM_EN.Y.y(:,i)  = DCM_EN.xY(i).u;
            DCM_EN.Y.name{i} = DCM_EN.xY(i).name;
        end
        
        P.indNFTrial = P.indNFTrial + 1;
        
        dcmInputData.DCM_EN = DCM_EN;
        dcmInputData.dcmParTag = mainLoopData.dcmParTag;
        dcmInputData.dcmParOpp = mainLoopData.dcmParOpp;
        
        % For now, this storage is a simplification of the proble that
        % dcmInputData structure contains Python-unsupported data type
        % that returne from MATLAB.
        save([tempdir, 'dcmInputData.mat'], 'dcmInputData');
    end
    
    assignin('base', 'mainLoopData', mainLoopData);
    assignin('base', 'P', P);
end

