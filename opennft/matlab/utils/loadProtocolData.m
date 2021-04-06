function loadProtocolData()
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

    P.CondIndexNames = protNames;
    for x=1:lCond
        P.ProtCond{x} = {};
        for k = 1:length(prt.ConditionIndex{x}.OnOffsets(:,1))
            unitBlock = prt.ConditionIndex{x}.OnOffsets(k,1) : prt.ConditionIndex{x}.OnOffsets(k,2);
            P.vectEncCond(unitBlock) = x+inc;
            P.ProtCond{x}(k,:) = {unitBlock};
        end
    end

    P.CondNames = P.CondIndexNames;

    if isDCM
        % Baseline index == 1; Regulation block index == 2
        P.CondNames = [P.CondIndexNames(1), P.CondIndexNames(2)];

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

%% Contrast
if isfield(prt,'Contrast')
    if ~P.isRestingState
        condNames = cellfun(@(x) x.ConditionName, prt.ConditionIndex, 'UniformOutput',false);
        con = textscan(prt.Contrast,'%d*%s','Delimiter',';');
%         if length(condNames)>length(con{1})
%             condNames = condNames(1,1:end-length(con{1}));
%         end
        conVect = [];
        for ci = cellfun(@(x) find(strcmp(x,con{2})),condNames,'UniformOutput',false)
            if ~isempty(ci{1}), conVect(end+1) = con{1}(ci{1}); else conVect(end+1) = 0; end
        end
    else
        conVect = double(cell2mat(textscan(prt.Contrast,'%d','Delimiter',';'))');
    end
    %P.Contrast = [1 0 0 0]';%conVect';
    P.Contrast = [0 1 1 0]';%conVect';
end

%% Save
P.Protocol = prt;
assignin('base', 'P', P);
end