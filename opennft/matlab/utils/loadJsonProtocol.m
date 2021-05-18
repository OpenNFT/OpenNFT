function loadJsonProtocol()
% Function to load experimental protocol stored in json format.
% Note, to work with json files, use jsonlab toolbox.
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

P = evalin('base', 'P');

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);

jsonFile = P.ProtocolFile;
NrOfVolumes = P.NrOfVolumes;
nrSkipVol = P.nrSkipVol;
   
prt = loadjson(jsonFile);

% -- remove dcmdef field -- %
if isDCM
    prt = rmfield(prt, 'dcmdef');
end

if ~P.isRestingState
    
    lCond = length(prt.ConditionIndex);
    for x=1:lCond
        protNames{x} = prt.ConditionIndex{x}.ConditionName;
    end

    P.vectEncCond = ones(1,NrOfVolumes-nrSkipVol);

    % check if baseline field already exists in protocol
    % and protocol reading presets
    % 1 is for Baseline
    if any(contains(protNames,'BAS'))
        P.basBlockLength = prt.ConditionIndex{ 1 }.OnOffsets(1,2);
        inc = 0;
    else
        inc = 1;
    end

    tmpSignalPreprocessingBasis = textscan(prt.SignalPreprocessingBasis,'%s','Delimiter',';');
    P.SignalPreprocessingBasis = tmpSignalPreprocessingBasis{:};
    P.CondIndexNames = protNames;
    for x=1:lCond
        P.ProtCond{x} = {};
        for k = 1:length(prt.ConditionIndex{x}.OnOffsets(:,1))
            unitBlock = prt.ConditionIndex{x}.OnOffsets(k,1) : prt.ConditionIndex{x}.OnOffsets(k,2);
            P.vectEncCond(unitBlock) = x+inc;
            P.ProtCond{x}(k,:) = {unitBlock};
        end
    end

    %% Implicit baseline
    BasInd = find(P.vectEncCond == 1);
    ProtCondBas = accumarray( cumsum([1, diff(BasInd) ~= 1]).', BasInd, [], @(x){x'} );
    if ~any(contains(P.CondIndexNames,'BAS'))
        P.ProtCond = [ {ProtCondBas} P.ProtCond ];
        P.CondIndexNames = [ {''} P.CondIndexNames ];
        P.basBlockLength = ProtCondBas{1}(end);
    end

end

%% Contrast and Conditions For Contrast encoding from .json Contrast specification
if isfield(prt,'ContrastActivation')
    if ~P.isRestingState
        conditionNames = cellfun(@(x) x.ConditionName, prt.ConditionIndex, 'UniformOutput',false);
        contrastString = textscan(prt.ContrastActivation,'%d*%s','Delimiter',';');
        P.ConditionForContrast = contrastString{2}';
        if length(conditionNames)>length(contrastString{1})
            conditionNames = intersect(contrastString{2},conditionNames)';
        end
        contrastVect = [];
        for contrastIndex = cellfun(@(x) find(strcmp(x,contrastString{2})),conditionNames,'UniformOutput',false)
            if ~isempty(contrastIndex{1})
                contrastVect(end+1) = contrastString{1}(contrastIndex{1});
            else
                contrastVect(end+1) = 0;
            end
        end
    else
        contrastVect = double(cell2mat(textscan(prt.ContrastActivation,'%d','Delimiter',';'))');
    end
    P.ContrastActivation = contrastVect';
end

%% Save
P.Protocol = prt;
assignin('base', 'P', P);
end