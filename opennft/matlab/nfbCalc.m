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
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

if indVol <= P.nrSkipVol
    return
end
indVolNorm = mainLoopData.indVolNorm;
condition = mainLoopData.condition;

flags = getFlagsType(P);

if P.isRTQA
    loopNrROIs = P.NrROIs-1;
else
    loopNrROIs = P.NrROIs;
end

%% Continuous PSC NF
if flags.isPSC && (strcmp(P.Prot, 'Cont') || strcmp(P.Prot, 'ContTask'))
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

        for indRoi = 1:loopNrROIs
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
if  strcmp(P.Prot, 'Inter') && (flags.isPSC || flags.isCorr)
    blockNF = mainLoopData.blockNF;
    firstNF = mainLoopData.firstNF;
    dispValue = mainLoopData.dispValue;
    Reward = mainLoopData.Reward;

    % NF estimation condition
    if condition == 2
        % count NF regulation blocks
        k = cellfun(@(x) x(end) == indVolNorm, P.ProtCond{ 2 });
        if any(k)
            blockNF = find(k);
            firstNF = indVolNorm;
            mainLoopData.flagEndPSC = 1;
        end

        regSuccess = 0;
        if firstNF == indVolNorm % the first volume of the NF block is
            % expected when assigning volumes for averaging, take HRF delay
            % into account
            if blockNF<2
                i_blockNF = P.ProtCond{ 2 }{blockNF}(end-6:end);
                i_blockBAS = P.ProtCond{ 1 }{blockNF}(end-6:end);
            else
                i_blockNF = P.ProtCond{ 2 }{blockNF}(end-6:end);
                i_blockBAS = [P.ProtCond{ 1 }{blockNF}(end-5:end) ...
                              P.ProtCond{ 1 }{blockNF}(end)+1];
            end

            if flags.isPSC
                for indRoi = 1:loopNrROIs
                    % Averaging across blocks
                    mBas  = median(mainLoopData.scalProcTimeSeries(indRoi,...
                        i_blockBAS));
                    mCond = median(mainLoopData.scalProcTimeSeries(indRoi,...
                        i_blockNF));

                    % Scaling
                    mBasScaled  = (mBas - mainLoopData.mposMin(indVolNorm)) / ...
                        (mainLoopData.mposMax(indVolNorm) - ...
                        mainLoopData.mposMin(indVolNorm));
                    mCondScaled = (mCond - mainLoopData.mposMin(indVolNorm)) / ...
                        (mainLoopData.mposMax(indVolNorm) - ...
                        mainLoopData.mposMin(indVolNorm));
                    norm_percValues(indRoi) = mCondScaled - mBasScaled;
                end

                % compute average %SC feedback value
                tmp_fbVal = eval(P.RoiAnatOperation);
            elseif flags.isCorr
                rhoBas = corrcoef(mainLoopData.scalProcTimeSeries(:,i_blockBAS)'); rhoBas = rhoBas(1,2);
                rhoCond = corrcoef(mainLoopData.scalProcTimeSeries(:,i_blockNF)'); rhoCond = rhoCond(1,2);
                norm_percValues(1:loopNrROIs) = rhoCond - rhoBas;

                % compute average %SC feedback value
                tmp_fbVal = rhoCond - rhoBas;
            end
            mainLoopData.vectNFBs(indVolNorm) = tmp_fbVal;
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

            % regSuccess and Shaping
            P.actValue(blockNF) = tmp_fbVal;
            if P.NFRunNr == 1
                if blockNF == 1
                    if P.actValue(blockNF) > 0.5
                        regSuccess = 1;
                    end
                else
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
    mainLoopData.Reward = '';

    displayData.Reward = mainLoopData.Reward;
    displayData.dispValue = mainLoopData.dispValue;
end

%% trial-based DCM NF
if flags.isDCM
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
        mainLoopData.dispValue = round(P.MaxFeedbackVal*tmp_fbVal, P.FeedbackValDec);

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
if flags.isSVM
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

        for indRoi = 1:loopNrROIs
            norm_percValues(indRoi) = ...
                       mainLoopData.scalProcTimeSeries(indRoi, indVolNorm);
        end

        % compute average feedback value
        tmp_fbVal = mean(norm_percValues);%eval(P.RoiAnatOperation);
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

%%
assignin('base', 'P', P);
assignin('base', 'mainLoopData', mainLoopData);