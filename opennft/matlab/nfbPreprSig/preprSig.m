function output = preprSig(indVol)
% Function to call real-time signal processing analyses.
%
% input:
% indVol - volume(scan) index
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');
if P.isRTQA
    rtQA_matlab = evalin('base', 'rtQA_matlab');
end

output = struct;

if indVol <= P.nrSkipVol
    return
end

flags = getFlagsType(P);

% Get ROI masks from workspace
if flags.isDCM
    % skip processing for rest epoch and NF display
    if mainLoopData.flagEndDCM
        return
    end
    ROIsGroup = evalin('base', 'ROIsGroup');
end
if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
    ROIs = evalin('base', 'ROIs');
end
if flags.isSVM
    WEIGHTs = evalin('base', 'WEIGHTs');
end

% normalized volume(scan) index
indVolNorm = mainLoopData.indVolNorm;
% handle type differences between Python/Matlab
indVolNorm = double(indVolNorm);

% raw time-series recursion
rawTimeSeries = mainLoopData.rawTimeSeries;

% number of regressors of no interest to correct with cGLM
if ~P.isAutoRTQA
    % 6 MC regressors, linear trend, constant
    nrRegrToCorrect = 8; 
else
    % 2 linear trend, constant, because 6 MC regressors are nrBasFct
    nrRegrToCorrect = 2; 
end

for indRoi = 1:P.NrROIs
    
    %% Get Raw time-series
    if flags.isPSC || flags.isCorr || P.isAutoRTQA
        rawTimeSeries(indRoi, indVolNorm) = mean(...
            mainLoopData.procVol(ROIs(indRoi).voxelIndex));
    end
    
    if flags.isSVM
        roiVect = mainLoopData.procVol(ROIs(indRoi).voxelIndex);
        weightVect = WEIGHTs.vol(ROIs(indRoi).voxelIndex);
        rawTimeSeries(indRoi, indVolNorm) = dot(roiVect,weightVect);
    end
    
    if flags.isDCM
        indNFTrial = P.indNFTrial;
        if indRoi == P.NrROIs && P.isRTQA
            % Whole brain ROI time-series
            ROIs = evalin('base', 'ROIs');
            rawTimeSeries(indRoi, indVolNorm) = mean( ...
                mainLoopData.procVol(ROIs.voxelIndex));
        else
            % manual set of ROI adaptation scheme
            isFixedGrROIforDCM = 0;
            if isFixedGrROIforDCM
                % fixed group ROI
                tmpVect = mainLoopData.procVol(ROIsGroup(indRoi).voxelIndex);
                rawTimeSeries(indRoi, indVolNorm) = mean(tmpVect);
                % ROI index, for records
                mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 1;
            else
                % dynamic optimal ROI
                if indNFTrial > 1
                    ROIsGlmAnat = evalin('base', 'ROIsGlmAnat');
                    ROIoptimGlmAnat = evalin('base', 'ROIoptimGlmAnat');
                    procVol = mainLoopData.procVol;
                    tmpVect = procVol(...
                        cell2mat(ROIsGlmAnat(indRoi).vol(indNFTrial))>0);

                    if ~isempty(tmpVect) && length(tmpVect)>10
                        rawTimeSeries(indRoi, indVolNorm) = mean(tmpVect);
                        mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 2;
                    else
                        tmpOptRoiVect = procVol(cell2mat(...
                            ROIoptimGlmAnat(indRoi).vol(indNFTrial))>0);
                        if ~isempty(tmpOptRoiVect) && length(tmpOptRoiVect)>10
                            rawTimeSeries(indRoi, indVolNorm) = mean(tmpOptRoiVect);
                            mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 3;
                        else
                            rawTimeSeries(indRoi, indVolNorm) = mean(...
                                procVol(ROIsGroup(indRoi).voxelIndex));
                            mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 1;
                        end
                    end
                else
                    rawTimeSeries(indRoi, indVolNorm) = mean(...
                        mainLoopData.procVol(...
                        ROIsGroup(indRoi).voxelIndex));
                    mainLoopData.adaptROIs(indRoi, indNFTrial+1) = 1;
                end
            end
    
            clear tmpVect tmpOptRoiVect

        end

    end
    
    %% Signal Processing
    % 1. Limits for scaling
    if flags.isDCM
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
    
    if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
        % continuous cGLM corrections
        tmp_ind_end = indVolNorm;
        tmp_begin = 1;
    end
    if flags.isDCM
        % trial-based cGLM corrections
        lTrial = P.lengthDCMTrial * P.indNFTrial;
        tmp_ind_end = indVolNorm - lTrial;
        tmp_begin = lTrial + 1;
    end
    tmp_rawTimeSeries = rawTimeSeries(indRoi, tmp_begin:end)';
    
    % 2.1. time-series AR(1) filtering
    if P.cglmAR1
        % initialize first AR(1) value
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
    regrStep = P.nrBasFct + nrRegrToCorrect;
    if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
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
            if ~P.isAutoRTQA
                cX0 = [tmpRegr mainLoopData.signalPreprocGlmDesign(1:tmp_ind_end,:)];
                betaReg = pinv(cX0) * tmp_rawTimeSeries;
                tmp_glmProcTimeSeries = (tmp_rawTimeSeries - ...
                    cX0 * [betaReg(1:end-mainLoopData.nrSignalPreprocGlmDesign); zeros(mainLoopData.nrSignalPreprocGlmDesign,1)])';
                if P.isRTQA
                    tmp_noRegGlmProcTimeSeries = (tmp_rawTimeSeries - ...
                        cX0 * [zeros(length(betaReg)-mainLoopData.nrSignalPreprocGlmDesign,1); betaReg(end-mainLoopData.nrSignalPreprocGlmDesign+1:end)])';
                end
            else
                cX0 = tmpRegr;
                betaReg = pinv(cX0) * tmp_rawTimeSeries;
                tmp_glmProcTimeSeries = (tmp_rawTimeSeries - cX0 * betaReg)';
                if P.isRTQA
                    tmp_noRegGlmProcTimeSeries = tmp_glmProcTimeSeries;
                end
            end

        end
        
        if P.isRTQA
            tContr = mainLoopData.tContr;
            erGlmProcTimeSeries = tmp_rawTimeSeries - cX0*betaReg;
            rtQA_matlab.varErGlmProcTimeSeries(indRoi,tmp_ind_end) = erGlmProcTimeSeries'*erGlmProcTimeSeries/(tmp_ind_end - length(tContr.pos));
            
            tmpBetRegr = [ betaReg; zeros(P.nrBasFct + nrRegrToCorrect - length(betaReg),1) ];
            rtQA_matlab.ROI(indRoi).betRegr(tmp_ind_end,:) = tmpBetRegr;
            rtQA_matlab.linRegr(indRoi,tmp_ind_end) = tmpBetRegr(2);
            
            tContr.pos = [ zeros(length(betaReg)-length(tContr.pos),1); tContr.pos ];
            tContr.neg = [ zeros(length(betaReg)-length(tContr.neg),1); tContr.neg ];
            
            if (tmp_ind_end >= 3*regrStep)

                invCX0 = inv(cX0'*cX0);
                pos_invCX0 = tContr.pos'*invCX0*tContr.pos;
                neg_invCX0 = tContr.neg'*invCX0*tContr.neg;

                rtQA_matlab.tGlmProcTimeSeries.pos(indRoi,tmp_ind_end) = tContr.pos'*betaReg /sqrt(rtQA_matlab.varErGlmProcTimeSeries(indRoi,tmp_ind_end)*pos_invCX0);
                rtQA_matlab.tGlmProcTimeSeries.neg(indRoi,tmp_ind_end) = tContr.neg'*betaReg /sqrt(rtQA_matlab.varErGlmProcTimeSeries(indRoi,tmp_ind_end)*neg_invCX0);

            end

            if tmp_ind_end < 3*regrStep
                mainLoopData.noRegGlmProcTimeSeries(indRoi,indVolNorm) = ...
                    tmp_rawTimeSeries(end);
            else
                mainLoopData.noRegGlmProcTimeSeries(indRoi,indVolNorm) = ...
                    tmp_noRegGlmProcTimeSeries(end);
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
    % as it is currently implemented (dcmBegin.m).
    if flags.isDCM
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
    
end
    
% 2. time-series iGLM

for indRoi = 1:P.NrROIs

    % 3. modified Kalman low-pass filter + spike identification & correction
    if flags.isPSC || flags.isSVM || flags.isDCM || flags.isCorr || P.isAutoRTQA
        tmpStd = std(mainLoopData.glmProcTimeSeries(indRoi,:));
    end
    if flags.isDCM
        mainLoopData.S(indRoi).Q = .25*tmpStd^2;
        mainLoopData.S(indRoi).R = tmpStd^2;
    end
    if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
        % See Koush 2012 for setting the constants
        mainLoopData.S(indRoi).Q = .25*tmpStd^2;
        mainLoopData.S(indRoi).R = tmpStd^2;
    end
    kalmThreshold = .9*tmpStd;
    [mainLoopData.kalmanProcTimeSeries(indRoi,indVolNorm), ...
        mainLoopData.S(indRoi), mainLoopData.fPositDerivSpike(indRoi), ...
        mainLoopData.fNegatDerivSpike(indRoi)] = ...
        modifKalman(kalmThreshold, ...
        mainLoopData.glmProcTimeSeries(indRoi,indVolNorm), ...
        mainLoopData.S(indRoi), mainLoopData.fPositDerivSpike(indRoi), ...
        mainLoopData.fNegatDerivSpike(indRoi));
    rtQA_matlab.kalmanSpikesPos(indRoi,indVolNorm) = mainLoopData.fPositDerivSpike(indRoi);
    rtQA_matlab.kalmanSpikesNeg(indRoi,indVolNorm) = mainLoopData.fNegatDerivSpike(indRoi);

    %4. Scaling
    if ~P.isAutoRTQA
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
    if flags.isSVM
        zcoredVal = ...
            zscore(mainLoopData.scalProcTimeSeries(indRoi, 1:indVolNorm));
        mainLoopData.scalProcTimeSeries(indRoi, indVolNorm) = ...
            1 ./ (1 + exp(-zcoredVal(end))); % or 1-logsig()
    end
    
end

% update main loop variable
mainLoopData.rawTimeSeries = rawTimeSeries;

% calculate average limits for 2 ROIs, e.g. for bilateral NF
% NF extensions with >2 ROIs requires an additional justification
mainLoopData.mposMax(indVolNorm)= mean(mainLoopData.posMax(:, indVolNorm));
mainLoopData.mposMin(indVolNorm)= mean(mainLoopData.posMin(:, indVolNorm));

output.posMin = [mainLoopData.posMin; mainLoopData.mposMin];
output.posMax = [mainLoopData.posMax; mainLoopData.mposMax];
output.scalProcTimeSeries = mainLoopData.scalProcTimeSeries;

output.glmProcTimeSeries = mainLoopData.glmProcTimeSeries;
output.kalmanProcTimeSeries = mainLoopData.kalmanProcTimeSeries;
output.displRawTimeSeries = mainLoopData.displRawTimeSeries;
output.rawTimeSeries = mainLoopData.rawTimeSeries;
output.motCorrParam = P.motCorrParam;
    
if P.isRTQA
    assignin('base', 'rtQA_matlab', rtQA_matlab);
end
assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
