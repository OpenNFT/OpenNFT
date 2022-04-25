function mainLoopEntry(indVol)
% Common starting logic for incoming data volume,
% depending on Feedback type.
% displayData structure, necessary for displaing feedback, is filled here.
%
% input:
% Workspace variables.
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

indVol = double(indVol);
P = evalin('base', 'P');

if ~(indVol > P.nrSkipVol)
    return;
end
mainLoopData = evalin('base', 'mainLoopData');

% Get Matlab time stamp related to # t6 using PTB-3 function.
% For clarification, see OpenNFT timing diagram on the website and our ms.
% Note that there is a small difference between this one and recordEvent()
% times since they are taken subsequently. We also don't know how PTB
% functions could deal with time-referencing issues between 2 parallel Matlab
% processes, i.e. core process and PTB helper.
if indVol == double(P.nrSkipVol)+1
    if ~isempty(which('GetSecs')), P.expOns_t6 = GetSecs; % PTB may not be installed
    else, P.expOns_t6 = cputime; end
    fprintf('\n\n=============')
    fprintf('\nMatlab time stamp t6!')
    fprintf('\n=============\n\n')
end

flags = getFlagsType(P);

if (strcmp(P.Prot, 'Inter') ||  strcmp(P.Prot, 'Cont') || strcmp(P.Prot, 'ContTask') || strcmp(P.Prot, 'Auto_RTQA'))  && ...
        (flags.isPSC ||  flags.isSVM || flags.isCorr || flags.isNone)
    
    mainLoopData.indVolNorm = indVol - P.nrSkipVol;
    
    if P.isAutoRTQA
        assignin('base', 'mainLoopData', mainLoopData);
        return;
    end
    
    % initialize relevant fields and a flag
    condition = P.vectEncCond(indVol - P.nrSkipVol);
    mainLoopData.condition = condition;
    
    if strcmp(P.Prot, 'Cont')
        % here 2nd and 3rd conditions are left for simplicity,
        % otherwise it could be just 2 conditions in all the settings
        if condition == 1
            mainLoopData.flagEndPSC = 0;
            mainLoopData.dispValue = 0;
            mainLoopData.Reward = '';
        elseif condition == 2
            mainLoopData.flagEndPSC = 1;
        end
        displayData.displayStage = 'instruction';
    end
    
    if strcmp(P.Prot, 'ContTask')
        if condition == 1
            mainLoopData.flagEndPSC = 0;
            mainLoopData.dispValue = 0;
            mainLoopData.Reward = '';
        elseif condition == 2
            mainLoopData.flagEndPSC = 1;
        elseif condition == 3
            mainLoopData.flagEndPSC = 0;
            mainLoopData.Reward = '';
        end
        displayData.displayStage = 'instruction';
    end

    if strcmp(P.Prot, 'Inter')
        switch condition
            case 1
                mainLoopData.flagEndPSC = 0;
                mainLoopData.dispValue = 0;
                mainLoopData.Reward = '';
                displayData.displayStage = 'instruction';
            case 2
                mainLoopData.flagEndPSC = 0;
                mainLoopData.dispValue = 0;
                mainLoopData.Reward = '';
                displayData.displayStage = 'instruction';
            case 3
                mainLoopData.flagEndPSC = 1;
                displayData.displayStage = 'feedback';
        end
    end
    % displayData assignment
    if strcmp(P.Prot, 'Inter')
        displayData.feedbackType = 'value_fixation';
    elseif strcmp(P.Prot, 'Cont')
        displayData.feedbackType = 'bar_count';
    elseif strcmp(P.Prot, 'ContTask')
        displayData.feedbackType = 'bar_count_task';
    end
    displayData.condition = condition;
    displayData.dispValue = mainLoopData.dispValue;
    displayData.Reward = mainLoopData.Reward;
end

%% DCM
if strcmp(P.Prot, 'InterBlock') && flags.isDCM
    
    if ~isempty(find(P.beginDCMblock == indVol-P.nrSkipVol,1))
        mainLoopData.NrDCMblocks = mainLoopData.NrDCMblocks + 1;
    end
    mainLoopData.indVolNorm = indVol - P.nrSkipVol - ...
        P.dcmRemoveInterval * mainLoopData.NrDCMblocks;
    
    % initialize relevant fields and a flag
    condition = P.vectEncCond(indVol - P.nrSkipVol);
    mainLoopData.condition = condition;
    switch condition
        case 1
            mainLoopData.flagEndDCM = 0;
            mainLoopData.dispValue = 0;
            mainLoopData.Reward = '';
        case 2
            mainLoopData.flagEndDCM = 0;
            mainLoopData.dispValue = 0;
            mainLoopData.Reward = '';
        case 3
            mainLoopData.flagEndDCM = 1;
        case 4
            mainLoopData.flagEndDCM = 1;
    end
    
    % displayData assignment
    displayData.feedbackType = 'DCM';
    displayData.condition = condition;
    displayData.dispValue = mainLoopData.dispValue;
    displayData.Reward = mainLoopData.Reward;
    displayData.displayStage = 'instruction';
end

if P.isAutoRTQA
    displayData.feedbackType = 'none';
end

displayData.iteration = indVol;
displayData.displayBlankScreen = 0;
displayData.taskseq = 0;
mainLoopData.displayData = displayData;
mainLoopData.feedbackType = displayData.feedbackType;

assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
