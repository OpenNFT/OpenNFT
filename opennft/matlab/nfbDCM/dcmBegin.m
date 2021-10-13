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
    % Copyright (C) 2016-2021 OpenNFT.org
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
            
            % Make time-series setting dynamic
            for roi = 1:DCM_EN.n 
                tmp.xY(roi).name   = DCM_EN.roiNames{roi};
                DCM_EN.Y.name{roi} = DCM_EN.roiNames{roi};
                tmp.xY(roi).u      = mainLoopData.kalmanProcTimeSeries(roi, vectDcmTrial)';
                DCM_EN.Y.y(:,roi)  = mainLoopData.kalmanProcTimeSeries(roi, vectDcmTrial)';
                tmp.xY(roi).Sess   = 1;
            end
            
            DCM_EN.v     = length(tmp.xY(1).u);
            DCM_EN.Y.Q   = spm_Ce(ones(1, DCM_EN.n) * DCM_EN.v);
            DCM_EN.xY    = tmp.xY;
            
            P.indNFTrial = P.indNFTrial + 1;
            
            dcmInputData.DCM_EN = DCM_EN;
            dcmInputData.dcmParTag = mainLoopData.dcmParTag;
            dcmInputData.dcmParOpp = mainLoopData.dcmParOpp;
            
            % For now, this storage is a simplification of the problem that
            % dcmInputData structure contains Python-unsupported data type
            % that returned from MATLAB.
            save([tempdir, 'dcmInputData.mat'], 'dcmInputData');
        end
        
        assignin('base', 'mainLoopData', mainLoopData);
        assignin('base', 'P', P);
    end
    
    
