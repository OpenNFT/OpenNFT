function betaRoi = onp_roiswglm

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

betaRoi = zeros(numel(P.ProtNF),P.NrROIs); % default value indicating no analysis

if ~isfield(mainLoopData,'indVolNorm') % init
    % load original SPM
    SPMSpec = load(fullfile(P.WorkFolder,'Settings','SPM.mat')); SPMSpec = SPMSpec.SPM;
    
    % make sure that the first regressor is the regulation and the order of the rest matches the order of CondNames
    P.CondNames(strcmp(P.Protocol.RegulationName, P.CondNames)) = [];
    P.CondNames = [{P.Protocol.RegulationName} P.CondNames];
    [junk,regrInd] = ismember(P.CondNames,cellfun(@(x) x.ConditionName, P.Protocol.Cond, 'UniformOutput', false));
    
    % add step-wise regressors for each block
    SPMSpec.Sess.U = struct('name',{},'ons',{},'dur',{},'P',{}, 'orth',{});
    if ~isempty(regrInd)
        for e = 1:numel(regrInd)
            cond = P.Protocol.Cond{regrInd(e)};
            if strcmp(cond.ConditionName, P.Protocol.RegulationName)
                for s = 1:size(cond.OnOffsets,1)
                    if s > 1, SPMSpec(s) = SPMSpec(s-1); end
                    SPMSpec(s).Sess.U(end+1) = cond2U(cond,s);
                end
            else
                for s = 1:numel(SPMSpec)
                    SPMSpec(s).Sess.U(end+1) = cond2U(cond);
                end
            end
        end
    end
    
    % generate xX for each model
    clear SPM
    for s = 1:numel(SPMSpec)
        SPM = spm_fmri_spm_ui(SPMSpec(s));
        if ~P.iglmAR1
            spmDesign{s} = SPM.xX.X(:,contains(SPM.xX.name,P.CondName));
        else
            spmDesign{s} = arRegr(P.aAR1, SPM.xX.X(:,contains(SPM.xX.name,P.CondName)));
        end
    end
    if exist(fullfile(pwd, 'SPM.mat'),'file'), delete('SPM.mat'); end
    
    % save models and block periods
    switchInds = cellfun(@(x) x(1), P.ProtBAS(1:end-1)); % not for the last baseline
    runInds = cellfun(@(x) x(1)-1, P.ProtBAS(2:end),'UniformOutput', false); % right before the consecutive baselines
    iDesign = mutableClass(switchInds);
    iDesign.addProp('runInds',runInds);
    iDesign.addProp('spmDesign',spmDesign);
    
    assignin('base', 'iDesign', iDesign);
    
else % run
    % load model according to block
    iDesign = evalin('base', 'iDesign');
    iDesign.indN = mainLoopData.indVolNorm;
    if mainLoopData.indVolNorm ~= iDesign.runInds, return; end
    
    spmDesign = iDesign.spmDesign;
    tmp_ind_end = mainLoopData.indVolNorm;
    regrStep = size(spmDesign,2) + 8; % 6 MC regressors, linear trend, constant
    tmp_rawTimeSeries = mainLoopData.tmp_rawTimeSeriesAR1;
    
    % a simplified version of prepSig 2.2
    if (tmp_ind_end < regrStep)
        tmpRegr = ones(tmp_ind_end,1);
        if P.cglmAR1
            tmpRegr = arRegr(P.aAR1,tmpRegr);
        end
        cX0 = tmpRegr;
    elseif (tmp_ind_end >= regrStep) && (tmp_ind_end < 2*regrStep)
        tmpRegr = [ones(tmp_ind_end,1) P.linRegr(1:tmp_ind_end)];
        if P.cglmAR1
            tmpRegr = arRegr(P.aAR1, tmpRegr);
        end
        cX0 = tmpRegr;
    elseif (tmp_ind_end >= 2*regrStep) && (tmp_ind_end < 3*regrStep)
        tmpRegr = [ones(tmp_ind_end,1) P.linRegr(1:tmp_ind_end) ...
            zscore(P.motCorrParam(1:tmp_ind_end,:))];
        if P.cglmAR1
            tmpRegr = arRegr(P.aAR1,tmpRegr);
        end
        cX0 = tmpRegr;
    else
        % zscore() is cumulative, which limits truly recursive
        % AR(1) filtering on regressors
        tmpRegr = [ones(tmp_ind_end,1) P.linRegr(1:tmp_ind_end) ...
            zscore(P.motCorrParam(1:tmp_ind_end,:))];
        if P.cglmAR1
            tmpRegr = arRegr(P.aAR1,tmpRegr);
        end
        if ~P.isAutoRTQA
            cX0 = [spmDesign(1:tmp_ind_end,:) tmpRegr];
        else
            cX0 = tmpRegr;
        end
    end
    
    for indRoi = 1:P.NrROIs
        betaReg = pinv(cX0) * tmp_rawTimeSeries(indRoi,:)';
        betaRoi(1:iDesign.stageN,indRoi) = betaReg(1:iDesign.stageN);
    end
    
end
end

function U = cond2U(cond,t)
% convert OpenNFT condition to SPM U
% optional: use t-th trial only
if nargin == 1, t = 1:size(cond.OnOffsets,1); end
CondName = cond.ConditionName;
if numel(t) == 1, CondName = sprintf('%s_%02d',CondName,t); end
U = struct(...
    'name',{cellstr(CondName)},...
    'ons',cond.OnOffsets(t,1),...
    'dur',(diff(cond.OnOffsets(t,:)')+1)',...
    'P',struct('name','none'),...
    'orth',1 ...
    );
end
