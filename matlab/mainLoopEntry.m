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
% Copyright (C) 2016-2017 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

indVol = double(indVol);
P = evalin('base', 'P');

if ~(indVol > P.nrSkipVol)
    return;
end
mainLoopData = evalin('base', 'mainLoopData');

%% PSC
if (strcmp(P.Prot, 'Inter') ||  strcmp(P.Prot, 'Cont'))  && ...
        (strcmp(P.Type, 'PSC')   ||  strcmp(P.Type, 'SVM') )
    
    mainLoopData.indVolNorm = indVol - P.nrSkipVol;
    
    % initalize relevant fields and a flag
    condition = P.vectEncCond(indVol - P.nrSkipVol);
    mainLoopData.condition = condition;
    
    if strcmp(P.Prot, 'Cont')
        % here 2nd and 3rd conditions are left for simplicity,
        % otheriwse it could be just 2 conditions in all the settings
        if condition == 1
            mainLoopData.flagEndPSC = 0;
            mainLoopData.dispValue = 0;
            mainLoopData.Reward = '';
        elseif condition == 2
            mainLoopData.flagEndPSC = 1;
        end
    end
    
    if strcmp(P.Prot, 'Inter')
        switch condition
            case 1
                mainLoopData.flagEndPSC = 0;
                mainLoopData.dispValue = 0;
                mainLoopData.Reward = '';
            case 2
                mainLoopData.flagEndPSC = 0;
                mainLoopData.dispValue = 0;
                mainLoopData.Reward = '';
            case 3
                mainLoopData.flagEndPSC = 1;
        end
    end
    % displayData assignment
    if strcmp(P.Prot, 'Inter')
        displayData.feedbackType = 'value_fixation';
    elseif strcmp(P.Prot, 'Cont')
        displayData.feedbackType = 'bar_count';
    end
    displayData.condition = condition;
    displayData.dispValue = mainLoopData.dispValue;
    displayData.Reward = mainLoopData.Reward;
end

%% DCM
if strcmp(P.Prot, 'InterBlock') && strcmp(P.Type, 'DCM')
    
    if ~isempty(find(P.beginDCMblock == indVol-P.nrSkipVol,1))
        mainLoopData.NrDCMblocks = mainLoopData.NrDCMblocks + 1;
    end
    mainLoopData.indVolNorm = indVol - P.nrSkipVol - ...
        P.dcmRemoveInterval * mainLoopData.NrDCMblocks;
    
    % initalize relevant fields and a flag
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
end

displayData.displayStage = 'instruction';
displayData.iteration = indVol;
displayData.displayBlankScreen = 0;
mainLoopData.displayData = displayData;
mainLoopData.feedbackType = displayData.feedbackType;

assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
