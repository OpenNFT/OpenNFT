function output = preprSig(indVol)
% Function to call real-time signal processing analyses.
%
% input:
% indVol - volume(scan) index
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

output = struct;

if indVol <= P.nrSkipVol
    return
end

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);

% Get ROI masks from workspace
if isDCM
    % skip processing for rest epoch and NF display
    if mainLoopData.flagEndDCM
        return
    end
    ROIsGroup = evalin('base', 'ROIsGroup');
end
if isPSC || P.isRestingState
    ROIs = evalin('base', 'ROIs');
end
if isSVM
    ROIs = evalin('base', 'ROIs');
    WEIGHTs = evalin('base', 'WEIGHTs');
end

% normalized volume(scan) index
indVolNorm = mainLoopData.indVolNorm;
% handle type differences between Python/Matlab
indVolNorm = double(indVolNorm);

% raw time-series recursion
rawTimeSeries = mainLoopData.rawTimeSeries;
if ~P.isRestingState
    % number of regressors of interest for cGLM
    nrRegrDesign = size(P.spmDesign,2);
else
    nrRegrDesign = 0;
end
% number of regressors of no interest to correct with cGLM
nrRegrToCorrect = 8; % 6 MC regressors, linear trend, constant

for indRoi = 1:P.NrROIs
    
    %% Get Raw time-series
    if isPSC || P.isRestingState
        rawTimeSeries(indRoi, indVolNorm) = mean(...
            mainLoopData.smReslVol_2D(ROIs(indRoi).mask2D>0));
    end
    
    if isSVM
        roiVect = mainLoopData.smReslVol_2D(ROIs(indRoi).mask2D>0);
        weightVect = WEIGHTs.mask2D(ROIs(indRoi).mask2D>0);
        rawTimeSeries(indRoi, indVolNorm) = dot(roiVect,weightVect);
    end
    
    if isDCM
        indNFTrial = P.indNFTrial;
        
        % manual set of ROI adaptation scheme
        isFixedGrROIforDCM = 0;
        if isFixedGrROIforDCM
            % fixed group ROI
            if ~P.smForDCM
                tmpVect = mainLoopData.nosmReslVol_2D(...
                    ROIsGroup(indRoi).mask2D>0);
            else
                tmpVect = mainLoopData.smReslVol_2D(...
                    ROIsGroup(indRoi).mask2D>0);
            end
            rawTimeSeries(indRoi, indVolNorm) = mean(tmpVect);
            % ROI index, for records
            mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 1;
        else
            % dynamic optimal ROI
            if indNFTrial > 1
                ROIsGlmAnat = evalin('base', 'ROIsGlmAnat');
                ROIoptimGlmAnat = evalin('base', 'ROIoptimGlmAnat');
                if ~P.smForDCM
                    tmpVect = mainLoopData.nosmReslVol_2D(...
                        cell2mat(ROIsGlmAnat(indRoi).mask2D(indNFTrial))>0);
                else
                    tmpVect = mainLoopData.smReslVol_2D(...
                        cell2mat(ROIsGlmAnat(indRoi).mask2D(indNFTrial))>0);
                end
                if ~isempty(tmpVect) && length(tmpVect)>10
                    rawTimeSeries(indRoi, indVolNorm) = mean(tmpVect);
                    mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 2;
                else
                    if ~P.smForDCM
                        tmpOptRoiVect = mainLoopData.nosmReslVol_2D(cell2mat(...
                            ROIoptimGlmAnat(indRoi).mask2D(indNFTrial))>0);
                    else
                        tmpOptRoiVect = mainLoopData.smReslVol_2D(cell2mat(...
                            ROIoptimGlmAnat(indRoi).mask2D(indNFTrial))>0);
                    end
                    if ~isempty(tmpOptRoiVect) && length(tmpOptRoiVect)>10
                        rawTimeSeries(indRoi, indVolNorm) = mean(tmpOptRoiVect);
                        mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 3;
                    else
                        if ~P.smForDCM
                            rawTimeSeries(indRoi, indVolNorm) = mean(...
                                mainLoopData.nosmReslVol_2D(...
                                ROIsGroup(indRoi).mask2D>0));
                        else
                            rawTimeSeries(indRoi, indVolNorm) = mean(...
                                mainLoopData.smReslVol_2D(...
                                ROIsGroup(indRoi).mask2D>0));
                        end
                        mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 1;
                    end
                end
            else
                if ~P.smForDCM
                    rawTimeSeries(indRoi, indVolNorm) = mean(...
                        mainLoopData.nosmReslVol_2D(...
                        ROIsGroup(indRoi).mask2D>0));
                else
                    rawTimeSeries(indRoi, indVolNorm) = mean(...
                        mainLoopData.smReslVol_2D(...
                        ROIsGroup(indRoi).mask2D>0));
                end
                mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 1;
            end
        end
        clear tmpVect tmpOptRoiVect
    end
    
    %% Signal Processing
    % 1. Limits for scaling
    if isDCM
        mainLoopData.initLim(indRoi) = 0.01*mean(rawTimeSeries(indRoi, :));
    else
        mainLoopData.initLim(indRoi) = 0.005*mean(rawTimeSeries(indRoi,:));
    end
    % Raw for Display
    mainLoopData.displRawTimeSeries(indRoi,indVolNorm) = ...
        rawTimeSeries(indRoi, indVolNorm)-rawTimeSeries(indRoi, 1);
    
    % 2. cumulative cGLM
    % to avoid NaNs given algnment to zero, see preprVol()    
    P.motCorrParam(1,:) = 0.00001; 
    
    if isPSC || isSVM || P.isRestingState
        % continuous cGLM corrections
        tmp_ind_end = indVolNorm;
        tmp_begin = 1;
    end
    if isDCM
        % trial-based cGLM corrections
        lTrial = P.lengthDCMTrial * P.indNFTrial;
        tmp_ind_end = indVolNorm - lTrial;
        tmp_begin = lTrial + 1;
    end
    tmp_rawTimeSeries = rawTimeSeries(indRoi, tmp_begin:end)';
    
    % 2.1. time-series AR(1) filtering
    if P.cglmAR1
        % initalize first AR(1) value
        if tmp_ind_end == 1
            mainLoopData.tmp_rawTimeSeriesAR1(indRoi,tmp_ind_end) = ...
                (1 - P.aAR1) * tmp_rawTimeSeries(tmp_ind_end);
        else
            mainLoopData.tmp_rawTimeSeriesAR1(indRoi,tmp_ind_end) = ...
                tmp_rawTimeSeries(tmp_ind_end) - P.aAR1 * ...
                mainLoopData.tmp_rawTimeSeriesAR1(indRoi,tmp_ind_end-1);
        end
        % replace raw ime-series with AR(1) time-series
        clear tmp_rawTimeSeries
        tmp_rawTimeSeries = mainLoopData.tmp_rawTimeSeriesAR1(indRoi, ...
            tmp_begin:end)';
    end
 
    % 2.2. exemplary step-wise addition of regressors, step = total nr of
    % Regressors, which may require a justification for particular project
    regrStep = nrRegrDesign+nrRegrToCorrect;
    if isPSC || isSVM || P.isRestingState
        if (tmp_ind_end < regrStep)
            tmpRegr = ones(tmp_ind_end,1);
            if P.cglmAR1
                tmpRegr = arRegr(P.aAR1,tmpRegr);
            end
            cX0 = tmpRegr;
            betaReg = pinv(cX0)*tmp_rawTimeSeries;
            tmp_glmProcTimeSeries = (tmp_rawTimeSeries - cX0*betaReg)';
        elseif (tmp_ind_end >= regrStep) && (tmp_ind_end < 2*regrStep)
            tmpRegr = [ones(tmp_ind_end,1) P.linRegr(1:tmp_ind_end)];
            if P.cglmAR1
                tmpRegr = arRegr(P.aAR1, tmpRegr);
            end
            cX0 = tmpRegr;
            betaReg = pinv(cX0) * tmp_rawTimeSeries;
            tmp_glmProcTimeSeries = (tmp_rawTimeSeries - cX0 * betaReg)';
        elseif (tmp_ind_end >= 2*regrStep) && (tmp_ind_end < 3*regrStep)
            tmpRegr = [ones(tmp_ind_end,1) P.linRegr(1:tmp_ind_end) ...
                zscore(P.motCorrParam(1:tmp_ind_end,:))];
            if P.cglmAR1
                tmpRegr = arRegr(P.aAR1,tmpRegr);
            end
            cX0 = tmpRegr;
            betaReg = pinv(cX0) * tmp_rawTimeSeries;
            tmp_glmProcTimeSeries = (tmp_rawTimeSeries - cX0 * betaReg)';
        else
            % zscore() is cumulative, which limits truly recursive
            % AR(1) filtering on regressors
            tmpRegr = [ones(tmp_ind_end,1) P.linRegr(1:tmp_ind_end) ...
                zscore(P.motCorrParam(1:tmp_ind_end,:))];
            if P.cglmAR1
                tmpRegr = arRegr(P.aAR1,tmpRegr);
            end
            if ~P.isRestingState
                cX0 = [tmpRegr P.spmDesign(1:tmp_ind_end,:)];
                betaReg = pinv(cX0) * tmp_rawTimeSeries;
                tmp_glmProcTimeSeries = (tmp_rawTimeSeries - ...
                    cX0 * [betaReg(1:end-1); zeros(1,1)])';
            else
                cX0 = tmpRegr;
                betaReg = pinv(cX0) * tmp_rawTimeSeries;
                tmp_glmProcTimeSeries = (tmp_rawTimeSeries - cX0 * betaReg)';
            end
        end
        mainLoopData.glmProcTimeSeries(indRoi,indVolNorm) = ...
                tmp_glmProcTimeSeries(end);

    end

    % 2.3.1 alternative processign for DCM, e.g. no motion and linear trend
    % regressors. Note, DCM could be very sensitive to cumulative signal
    % processing. Hence, motion and the linear trend regressors are
    % not necessary to be added cumulatively here. They could be added 
    % when DCM needs to be computed, i.e. at the end of the entire trial, 
    % as it is currently implmented (dcmBegin.m).
    if isDCM
        % subtract the absolute value of the trial
        cX0 = ones(tmp_ind_end,1);
        betaReg = pinv(cX0)*tmp_rawTimeSeries;
        tmp_glmProcTimeSeries = (tmp_rawTimeSeries - cX0*betaReg)';
        mainLoopData.glmProcTimeSeries(indRoi,indVolNorm) = ...
            tmp_glmProcTimeSeries(end);
    end

    % 2.3.2 alternative detrending using EMA filter, careful, exponential lags
    enableEma = 0;
    if enableEma
        % EMA preset
        thEMA = 0.98;
        if ~isempty(find(P.beginDCMblock ==indVol-P.nrSkipVol,1))
            mainLoopData.inpFilt(indRoi)= rawTimeSeries(indRoi,indVolNorm);
        end
        if (indVolNorm < 2)
            mainLoopData.emaProcTimeSeries(indRoi,indVolNorm) = ...
                rawTimeSeries(indRoi, indVolNorm)-rawTimeSeries(indRoi, 1);
        else
            [mainLoopData.emaProcTimeSeries(indRoi,indVolNorm), ...
                mainLoopData.inpFilt(indRoi)] = ...
                emaFilt(thEMA, rawTimeSeries(indRoi, indVolNorm), ...
                mainLoopData.inpFilt(indRoi));
        end
    end

    % 3. modified Kalman low-pass filter + spike identification & correction
    if isPSC || isSVM || isDCM || P.isRestingState
        tmpStd = std(mainLoopData.glmProcTimeSeries(indRoi,:));
    end
    if isDCM
        mainLoopData.S(indRoi).Q = .25*tmpStd^2;
        mainLoopData.S(indRoi).R = tmpStd^2;
    end
    if isPSC || isSVM || P.isRestingState
        % See Koush 2012 for setting the constants
        mainLoopData.S(indRoi).Q = tmpStd^2;
        mainLoopData.S(indRoi).R = 1.95*tmpStd^2;
    end
    kalmThreshold = .9*tmpStd;
    [mainLoopData.kalmanProcTimeSeries(indRoi,indVolNorm), ...
        mainLoopData.S(indRoi), mainLoopData.fPositDerivSpike(indRoi), ...
        mainLoopData.fNegatDerivSpike(indRoi)] = ...
        modifKalman(kalmThreshold, ...
        mainLoopData.glmProcTimeSeries(indRoi,indVolNorm), ...
        mainLoopData.S(indRoi), mainLoopData.fPositDerivSpike(indRoi), ...
        mainLoopData.fNegatDerivSpike(indRoi));

    %4. Scaling
    if ~P.isRestingState
        slWind = P.basBlockLength*P.nrBlocksInSlidingWindow;
    else
        slWind = P.NrOfVolumes - P.nrSkipVol;
    end
    [mainLoopData.scalProcTimeSeries(indRoi, indVolNorm), ...
        mainLoopData.tmp_posMin(indRoi), mainLoopData.tmp_posMax(indRoi)] = ...
        scaleTimeSeries(mainLoopData.kalmanProcTimeSeries(indRoi,:), ...
        indVolNorm, slWind, mainLoopData.initLim(indRoi),...
        mainLoopData.tmp_posMin(indRoi), ...
        mainLoopData.tmp_posMax(indRoi), P);
    mainLoopData.posMin(indRoi,indVolNorm)=mainLoopData.tmp_posMin(indRoi);
    mainLoopData.posMax(indRoi,indVolNorm)=mainLoopData.tmp_posMax(indRoi);

    % 5. z-scoring and sigmoidal transform
    if isSVM
        zcoredVal = ...
            zscore(mainLoopData.scalProcTimeSeries(indRoi, 1:indVolNorm));
        mainLoopData.scalProcTimeSeries(indRoi, indVolNorm) = ...
            logsig(zcoredVal(end)); % or 1-logsig()
    end
    
end

% update main loop variable
mainLoopData.rawTimeSeries = rawTimeSeries;

% calcualte average limits for 2 ROIs, e.g. for bilateral NF
% NF extensions with >2 ROIs requires an additional justification
mainLoopData.mposMax(indVolNorm)= mean(mainLoopData.posMax(:, indVolNorm));
mainLoopData.mposMin(indVolNorm)= mean(mainLoopData.posMin(:, indVolNorm));

output.posMin = [mainLoopData.posMin; mainLoopData.mposMin];
output.posMax = [mainLoopData.posMax; mainLoopData.mposMax];
output.scalProcTimeSeries = mainLoopData.scalProcTimeSeries;

output.kalmanProcTimeSeries = mainLoopData.kalmanProcTimeSeries;
output.displRawTimeSeries = mainLoopData.displRawTimeSeries;
output.rawTimeSeries = mainLoopData.rawTimeSeries;
output.motCorrParam = P.motCorrParam;
    
assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
