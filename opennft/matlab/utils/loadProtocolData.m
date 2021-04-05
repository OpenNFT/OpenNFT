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
    
    lCond = length(prt.Cond);
    protFieldNames = fieldnames(prt);
    protFieldNames = protFieldNames(1:lCond);
    protNames = struct2cell(prt);
    protNames = protNames(1:lCond);
    
    P.vectEncCond = ones(1,NrOfVolumes-nrSkipVol);
%     tempP.vectEncCond = ones(1,NrOfVolumes-nrSkipVol);
    P.basBlockLength = prt.Cond{1}.OnOffsets(1,2);
    
    protCond = prt.Cond;
    if ~isempty(find(contains(protFieldNames,'BaselineName')))
        for x=1:lCond
            if strcmp(prt.Cond{x}.ConditionName,prt.BaselineName)
                protCond(x) = [];
                break;
            end
        end    
        lCond = length(protCond);
    end
    
    P.protNames = [];
    for x=1:lCond
        P.protNames.(protFieldNames{x}) = protNames{x};
        P.(protCond{x}.ConditionName) = {};
        for k = 1:length(protCond{x}.OnOffsets(:,1))
            unitBlock = protCond{x}.OnOffsets(k,1) : protCond{x}.OnOffsets(k,2); 
            P.vectEncCond(unitBlock) = x+1;
            P.(protCond{x}.ConditionName)(k,:) = {unitBlock};
        end
    end
        
%     P.CondName = prt.RegulationName;
%     P.ProtNF = {};
%     P.ProtTask = {};
    
%     P.CondNames = {P.CondName};
    P.CondNames = {P.protNames.RegulationName};
    if isPSC
        if strcmp(P.Prot, 'ContTask')

            P.TaskFirstVol = zeros(1,P.NrOfVolumes+P.nrSkipVol);            
            P.TaskFirstVol(1,(prt.Cond{end}.OnOffsets(:,1)+double(P.nrSkipVol))')=1;
            
            P.CondNames = {P.protNames.RegulationName, P.protNames.TaskName};
            
        elseif strcmp(P.Prot, 'Inter')
            
%             P.DispName = prt.nfbDisplayName;
            P.CondNames = {P.protNames.RegulationName, P.protNames.nfbDisplayName}; 
            
        end
    elseif isDCM

        P.CondNames = {P.protNames.BaselineName, P.protNames.RegulationName};      
        
    end

%     %% PSC
%     if strcmp(P.Prot, 'Cont') && isPSC
%         P.CondNames = {P.CondName};
%         for x = 1:lCond
%             for k = 1:length(prt.Cond{x}.OnOffsets(:,1)) 
%                 unitBlock = prt.Cond{x}.OnOffsets(k,1) : prt.Cond{x}.OnOffsets(k,2); 
%                 if strcmpi(prt.Cond{x}.ConditionName, P.CondName) 
%                     P.vectEncCond(unitBlock) = 2;
%                     P.ProtNF(k,:) = {unitBlock};                
%                 end
%             end
%         end
%     end
% 
%     if strcmp(P.Prot, 'ContTask') && isPSC
%         P.TaskName = prt.TaskName;
%         P.TaskFirstVol = zeros(1,P.NrOfVolumes+P.nrSkipVol);
% 
%         P.TaskFirstVol(1,(prt.Cond{end}.OnOffsets(:,1)+double(P.nrSkipVol))')=1;
%         P.CondNames = {P.CondName, P.TaskName};
%         for x = 1:lCond
%             for k = 1:length(prt.Cond{x}.OnOffsets(:,1)) 
%                 unitBlock = prt.Cond{x}.OnOffsets(k,1) : prt.Cond{x}.OnOffsets(k,2); 
%                 if strcmpi(prt.Cond{x}.ConditionName, 'NFBREG') 
%                     P.vectEncCond(unitBlock) = 2;
%                     P.ProtNF(k,:) = {unitBlock};  
%                 elseif strcmpi(prt.Cond{x}.ConditionName, 'TASK') 
%                     P.vectEncCond(unitBlock) = 3;
%                     P.ProtTask(k,:) = {unitBlock};  
%                 end
%             end
%         end 
%     end
% 
%     if strcmp(P.Prot, 'Inter') && isPSC
%         P.DispName = prt.nfbDisplayName;
%         P.CondNames = {P.CondName, P.DispName}; 
%         for x = 1:lCond
%             for k = 1:length(prt.Cond{x}.OnOffsets(:,1))
%                 unitBlock = prt.Cond{x}.OnOffsets(k,1) : prt.Cond{x}.OnOffsets(k,2);
%                 if strcmpi(prt.Cond{x}.ConditionName, P.CondName)
%                     P.ProtNF(k,:) = {unitBlock};
%                     P.vectEncCond(unitBlock) = 2;
%                 elseif strcmpi(prt.Cond{x}.ConditionName, P.DispName)
%                     P.vectEncCond(unitBlock) = 3;
%                 end
%             end
%         end
%     end
% 
%     %% DCM
%     if strcmp(P.Prot, 'InterBlock') && isDCM
%         P.DispName = prt.nfbDisplayName;
%         P.RestName = prt.RestName;
%         P.CondNames = {prt.BaselineName, P.CondName}; 
%         for x = 1:lCond
%             for k = 1:length(prt.Cond{x}.OnOffsets(:,1))
%                 unitBlock = prt.Cond{x}.OnOffsets(k,1) : prt.Cond{x}.OnOffsets(k,2);
%                 if strcmpi(prt.Cond{x}.ConditionName, P.CondName)
%                     P.vectEncCond(unitBlock) = 2;
%                 elseif strcmpi(prt.Cond{x}.ConditionName, P.RestName)
%                     P.vectEncCond(unitBlock) = 3;
%                 elseif strcmpi(prt.Cond{x}.ConditionName, P.DispName)
%                     P.vectEncCond(unitBlock) = 4;
%                 end
%             end
%         end
%     end
% 
%     %% SVM
%     if strcmp(P.Prot, 'Cont') && isSVM
%         P.CondNames = {P.CondName};
%         for x = 1:lCond
%             for k = 1:length(prt.Cond{x}.OnOffsets(:,1)) 
%                 unitBlock = prt.Cond{x}.OnOffsets(k,1) : prt.Cond{x}.OnOffsets(k,2); 
%                 if strcmpi(prt.Cond{x}.ConditionName, P.CondName) 
%                     P.vectEncCond(unitBlock) = 2;
%                     P.ProtNF(k,:) = {unitBlock};                
%                 end
%             end
%         end
%     end
    
    %% Implicit baseline
    BasInd = find(P.vectEncCond == 1);
%     P.ProtBAS = accumarray( cumsum([1, diff(BasInd) ~= 1]).', BasInd, [], @(x){x'} )';
    if ~isempty(find(contains(fieldnames(prt),'BaselineName')))
        P.(prt.Cond{1}.ConditionName) = accumarray( cumsum([1, diff(BasInd) ~= 1]).', BasInd, [], @(x){x'} );
    else
        P.BAS = accumarray( cumsum([1, diff(BasInd) ~= 1]).', BasInd, [], @(x){x'} );
    end
end

%% Contrast
if isfield(prt,'Contrast')
    if ~P.isRestingState
        condNames = cellfun(@(x) x.ConditionName, prt.Cond, 'UniformOutput',false);
        con = textscan(prt.Contrast,'%d*%s','Delimiter',';');
        if length(condNames)>length(con{1})
            condNames = condNames(1,1:end-length(con{1}));
        end
        conVect = [];
        for ci = cellfun(@(x) find(strcmp(x,con{2})),condNames,'UniformOutput',false)
            if ~isempty(ci{1}), conVect(end+1) = con{1}(ci{1}); else conVect(end+1) = 0; end
        end
    else
        conVect = double(cell2mat(textscan(prt.Contrast,'%d','Delimiter',';'))');
    end
    P.Contrast = conVect';
end

%% Save
P.Protocol = prt;
assignin('base', 'P', P);
end