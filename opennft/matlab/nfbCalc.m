function displayData = nfbCalc(indVol, displayData, ...
                               dcmTagLE, dcmOppLE, isDcmCalculated)
% Function to estimate the feedback.
%
% input:
% indVol          - volume(scan) index
% displayData     - data structure for feedback presentation
% dcmParTag       - model-defining structure for a target model (model 1)
% dcmParOpp       - model-defining structure for an opposed model (model 2)
% isDcmCalculated - flag for DCM estiamtion state
%
% output: 
% displayData - updated data structure for feedback presentation
%
% Note, DCM feedback estimates are hardcorded separately as function input.
% Generalizations are planned.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

if indVol <= P.nrSkipVol
    return
end
indVolNorm = mainLoopData.indVolNorm;
condition = mainLoopData.condition;

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);

%% Continuous PSC NF
if isPSC && (strcmp(P.Prot, 'Cont') || strcmp(P.Prot, 'ContTask'))
    blockNF = mainLoopData.blockNF;
    firstNF = mainLoopData.firstNF;

    % NF estimation condition
    if condition == 2

        % count NF regulation blocks
        % index for Regulation block == 2
        k = cellfun(@(x) x(1) == indVolNorm, P.ProtCond{ 2 });
        if any(k)
            blockNF = find(k);
            firstNF = indVolNorm;
        end
    
        % Get reference baseline in cumulated way across the RUN, 
        % or any other fashion
        i_blockBAS = [];
        if blockNF<2
            % according to json protocol
            % index for Baseline == 1
            i_blockBAS = P.ProtCond{ 1 }{blockNF}(end-6:end);
        else            
            for iBas = 1:blockNF
                i_blockBAS = [i_blockBAS P.ProtCond{ 1 }{iBas}(3:end)];
                % ignore 2 scans for HRF shift, e.g. if TR = 2sec
            end
        end

        for indRoi = 1:P.NrROIs
            mBas = median(mainLoopData.scalProcTimeSeries(indRoi,i_blockBAS));
            mCond = mainLoopData.scalProcTimeSeries(indRoi,indVolNorm);
            norm_percValues(indRoi) = mCond - mBas;
        end

        % compute average %SC feedback value
        tmp_fbVal = eval(P.RoiAnatOperation); 
        dispValue = round(P.MaxFeedbackVal*tmp_fbVal, P.FeedbackValDec); 

        % [0...P.MaxFeedbackVal], for Display
        if ~P.NegFeedback && dispValue < 0
            dispValue = 0;
        elseif P.NegFeedback && dispValue < P.MinFeedbackVal
             dispValue = P.MinFeedbackVal;
        end
        if dispValue > P.MaxFeedbackVal
            dispValue = P.MaxFeedbackVal;
        end

        mainLoopData.norm_percValues(indVolNorm,:) = norm_percValues;
        mainLoopData.dispValues(indVolNorm) = dispValue;
        mainLoopData.dispValue = dispValue;
    else
        tmp_fbVal = 0;
        mainLoopData.dispValue = 0;                                    
    end

    mainLoopData.vectNFBs(indVolNorm) = tmp_fbVal;
    mainLoopData.blockNF = blockNF;
    mainLoopData.firstNF = firstNF;
    mainLoopData.Reward = '';

    displayData.Reward = mainLoopData.Reward;
    displayData.dispValue = mainLoopData.dispValue;
% else
%     tmp_fbVal = 0;
%     mainLoopData.dispValue = 0;
%     mainLoopData.vectNFBs(indVolNorm) = tmp_fbVal;
%     mainLoopData.Reward = '';
% 
%     displayData.Reward = mainLoopData.Reward;
%     displayData.dispValue = mainLoopData.dispValue;
end

%% Intermittent PSC NF
if isPSC && strcmp(P.Prot, 'Inter')
    blockNF = mainLoopData.blockNF;
    firstNF = mainLoopData.firstNF;
    blockTask2 = mainLoopData.blockTask2;
    lastTask2 = mainLoopData.lastTask2;
    blockTask3 = mainLoopData.blockTask3;
    lastTask3 = mainLoopData.lastTask3;

    dispValue = mainLoopData.dispValue;
    Reward = mainLoopData.Reward;

    % count blocks
    if condition == 3 || condition == 4
        % Task2 block
        iTask2 = cellfun(@(x) x(end) == indVolNorm, P.ProtTask2);
        if any(iTask2)
            blockTask2 = find(iTask2);
            lastTask2 = indVolNorm;
            mainLoopData.flagEndPSC = 1;
        end
        % Task3 block
        iTask3 = cellfun(@(x) x(end) == indVolNorm, P.ProtTask3);
        if any(iTask3)
            blockTask3 = find(iTask3);
            lastTask3 = indVolNorm;
            mainLoopData.flagEndPSC = 1;
        end
    end

    % NF estimation condition
    if condition == 5
        % count Rest blocks
        k = cellfun(@(x) x(end) == indVolNorm, P.ProtREST);
        if any(k)
            blockNF = find(k);
            firstNF = indVolNorm;
            mainLoopData.flagEndPSC = 1;
            if (P.ProtTask1{blockNF}(end)+4) == (P.ProtTask2{blockTask2}(1))
                isTask2 = 1;
                isTask3 = 0;
            elseif (P.ProtTask1{blockNF}(end)+4) == (P.ProtTask3{blockTask3}(1))
                isTask2 = 0;
                isTask3 = 1;
            end
        end

        % assign baseline indexes, for complications in fixation condition
        % number of indxAllBAS should be equal to number of blockNF for
        % simplicity
        isMixedBaseline = 1;
        if ~isMixedBaseline
            indxAllBAS = 1:1:length(P.ProtBAS);
        else
            indxAllBAS = 1:2:length(P.ProtBAS);
        end

        isTakePreviousBlockBAS = 0;
        % Get reference baseline in cumulated way across the RUN,
        % or any other fashion
        if ~isTakePreviousBlockBAS
            i_blockBAS = [];
            if blockNF==1
                i_blockBAS = P.ProtBAS{indxAllBAS(blockNF)}(3:end);
            elseif blockNF>1
                for iBas = 1:blockNF
                    i_blockBAS = [i_blockBAS P.ProtBAS{indxAllBAS(iBas)}(4:end)];
                    % ignore 2 scans for HRF shift, e.g. if TR = 2sec
                end
            end
        end

        regSuccess = 0;
        if firstNF == indVolNorm % the first volume of the NF block is 
            % expected when assigning volumes for averaging, take HRF delay
            % into account
            if blockNF==1
                if isTask2
                    i_blockNF = [P.ProtTask1{blockNF}(4:end) P.ProtTask2{blockTask2}(4:end)];
                elseif isTask3
                    i_blockNF = [P.ProtTask1{blockNF}(4:end) P.ProtTask3{blockTask3}(4:end)];
                end
                if isTakePreviousBlockBAS
                    i_blockBAS = [];
                    i_blockBAS = P.ProtBAS{indxAllBAS(blockNF)}(3:end);
                end
            elseif blockNF>1
                if isTask2
                    i_blockNF = [P.ProtTask1{blockNF}(4:end) P.ProtTask2{blockTask2}(4:end)];
                elseif isTask3
                    i_blockNF = [P.ProtTask1{blockNF}(4:end) P.ProtTask3{blockTask3}(4:end)];
                end

                if isTakePreviousBlockBAS
                    % take just previous block and an extra point from the
                    % next condition given hrf delay
                    i_blockBAS = [];
                    i_blockBAS = [P.ProtBAS{indxAllBAS(blockNF)}(4:end) ...
                                  P.ProtBAS{indxAllBAS(blockNF)}(end)+1];
                end
            end

            for indRoi = 1:P.NrROIs
                isFeedbackPSC = 1;
                if ~isFeedbackPSC
                    % Common range Scaling was recommneded/tested for
                    % bilateral co-activation only. Separarte range scaling
                    % should be also used with caution because signals
                    % may have reasonably different ranges and separate
                    % scaling would neutralize it.

                    % Averaging across blocks
                    mBas  = median(mainLoopData.kalmanProcTimeSeries(indRoi,...
                                                                  i_blockBAS));
                    mCond = median(mainLoopData.kalmanProcTimeSeries(indRoi,...
                                                                   i_blockNF));

                    % Scaling
                    mBasScaled  = (mBas - mainLoopData.mposMin(indVolNorm)) / ...
                                            (mainLoopData.mposMax(indVolNorm) - ...
                                             mainLoopData.mposMin(indVolNorm));
                    mCondScaled = (mCond - mainLoopData.mposMin(indVolNorm)) / ...
                                            (mainLoopData.mposMax(indVolNorm) - ...
                                             mainLoopData.mposMin(indVolNorm));
                    norm_percValues(indRoi) = mCondScaled - mBasScaled;
                else
                    % PSC estimation
                    mBasPSC  = median(mainLoopData.constProcTimeSeries(indRoi,...
                        i_blockBAS));
                    mCondPSC = median(mainLoopData.constProcTimeSeries(indRoi,...
                        i_blockNF));
                    norm_percValues(indRoi) = 100*(mCondPSC - mBasPSC)/mBasPSC;
                end
            end

            % compute feedback based on two ROIs average or difference
            if ~isFeedbackPSC && P.NrROIs == 2
                tmp_fbVal = eval(P.RoiAnatOperation);
            elseif isFeedbackPSC && P.NrROIs == 2
                tmp_fbVal = norm_percValues(2) - norm_percValues(1);
            end
            mainLoopData.vectNFBs(indVolNorm) = tmp_fbVal;
            dispValue = round(P.MaxFeedbackVal*tmp_fbVal, P.FeedbackValDec); 

            % display feedback value and threshold overheads
            if ~P.NegFeedback && dispValue < 0
                dispValue = 0;
            elseif P.NegFeedback && dispValue < P.MinFeedbackVal
                dispValue = P.MinFeedbackVal;
            end
            if dispValue > P.MaxFeedbackVal
                dispValue = P.MaxFeedbackVal;
            end

            % regSuccess and shaping
            P.actValue(blockNF) = tmp_fbVal;
            if P.NFRunNr == 1
                if blockNF==1
                    if P.actValue(blockNF) > 0.5
                        regSuccess = 1;
                    end
                elseif blockNF>1
                    if blockNF == 2
                        tmp_Prev = P.actValue(blockNF-1);
                    elseif blockNF == 3
                        tmp_Prev = median(P.actValue(blockNF-2:blockNF-1));
                    else
                        tmp_Prev = median(P.actValue(blockNF-3:blockNF-1));
                    end
                    if  (0.9*P.actValue(blockNF) >= tmp_Prev)  % 10% larger
                        regSuccess = 1;
                    end
                end
            elseif P.NFRunNr>1
                tmp_actValue = [P.prev_actValue P.actValue]; 
                % creates a vector from previous run and current run
                lactVal = length(tmp_actValue);
                tmp_Prev = median(tmp_actValue(lactVal-3:lactVal-1)); 
                % takes 3 last, except for current
                if  (0.9 * P.actValue(blockNF) >= tmp_Prev)  % 10% larger
                    regSuccess = 1;
                end
            end

            mainLoopData.norm_percValues(blockNF,:) = norm_percValues;
            mainLoopData.regSuccess(blockNF) = regSuccess;
        else
            tmp_fbVal = 0;
        end
    else
        tmp_fbVal = 0;
    end

    if mainLoopData.flagEndPSC 
        mainLoopData.dispValues(indVolNorm) = dispValue;
        mainLoopData.dispValue = dispValue;
    else
        mainLoopData.dispValues(indVolNorm) = 0;
        mainLoopData.dispValue = 0;                                    
    end

    mainLoopData.vectNFBs(indVolNorm) = tmp_fbVal;    
    mainLoopData.blockNF = blockNF;
    mainLoopData.firstNF = firstNF;
    mainLoopData.blockTask2 = blockTask2;
    mainLoopData.lastTask2 = lastTask2;
    mainLoopData.blockTask3 = blockTask3;
    mainLoopData.lastTask3 = lastTask3;

    mainLoopData.Reward = '';

    displayData.Reward = mainLoopData.Reward;
    displayData.dispValue = mainLoopData.dispValue;
end

%% trial-based DCM NF
if isDCM
    indNFTrial  = P.indNFTrial;

    %isDcmCalculated = ~isempty(find(P.endDCMblock==indVol-P.nrSkipVol,1));

    % Reward threshold for DCM is hard-coded per day, see Intermittent PSC
    % NF for generalzad reward data transfer aross the runs.
    thReward = 3; % set the threshold for logBF, 
                  % e.g. constant per run or per day

    if isDcmCalculated
        logBF = dcmTagLE - dcmOppLE;
        disp(['logBF value: ', num2str(logBF)]);

        mainLoopData.logBF(indNFTrial) = logBF;
        mainLoopData.vectNFBs(indNFTrial) = logBF;
        mainLoopData.flagEndDCM = 1;
        tmp_fbVal = mainLoopData.logBF(indNFTrial);
        dispValue = round(P.MaxFeedbackVal*tmp_fbVal, P.FeedbackValDec); 

        % calculating monetory reward value
        if mainLoopData.dispValue > thReward
            mainLoopData.tReward = mainLoopData.tReward + 1;
        end

        mainLoopData.Reward = mat2str(mainLoopData.tReward);
    end

    if mainLoopData.flagEndDCM 
        displayData.Reward = mainLoopData.Reward;
        displayData.dispValue = mainLoopData.dispValue;
    else
        mainLoopData.dispValue = 0;
        mainLoopData.Reward = '';
        displayData.Reward = mainLoopData.Reward;
        displayData.dispValue = mainLoopData.dispValue;
    end

end

%% continuous SVM NF
if isSVM
    blockNF = mainLoopData.blockNF;
    firstNF = mainLoopData.firstNF;    
    dispValue = mainLoopData.dispValue;

    if condition == 2
        % count NF regulation blocks
        k = cellfun(@(x) x(end) == indVolNorm, P.ProtCond{ 2 });
        if any(k)
            blockNF = find(k);
            firstNF = indVolNorm;
        end

        for indRoi = 1:P.NrROIs
            norm_percValues(indRoi) = ...
                       mainLoopData.scalProcTimeSeries(indRoi, indVolNorm);
        end

        % compute average feedback value
        tmp_fbVal = eval(P.RoiAnatOperation); 
        dispValue = round(P.MaxFeedbackVal*tmp_fbVal, P.FeedbackValDec); 

        mainLoopData.norm_percValues(indVolNorm,:) = norm_percValues;
        mainLoopData.dispValues(indVolNorm) = dispValue;
        mainLoopData.dispValue = dispValue;
    else
        tmp_fbVal = 0;
        mainLoopData.dispValue = 0;                                    
    end

    mainLoopData.vectNFBs(indVolNorm) = tmp_fbVal;
    mainLoopData.blockNF = blockNF;
    mainLoopData.firstNF = firstNF;
    mainLoopData.Reward = '';

    displayData.Reward = mainLoopData.Reward;
    displayData.dispValue = mainLoopData.dispValue;

end

assignin('base', 'P', P);
assignin('base', 'mainLoopData', mainLoopData);

