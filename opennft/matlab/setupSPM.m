function SPM = setupSPM(P)

% For now, note that spmMaskTh is assigned based on the EPI template/
% background image, for simplicity; and a somewhat lower relative threshold
% (see THR = 0.5 vs SPM default 0.8) aims to take the temporal variability 
% (std ca. 0.5%) into account, see in code.
% This is because SPM provides the TH value for each volume given the data,
% which is not available in real-time in the current OpenNFT version. 
% TH values could depend on the data acquisition setup, and could evtl. be
% set as mean(SPM.xM.TH)*ones(size(SPM.xM.TH)), or zeros(size(SPM.xM.TH)) 
% given masking threshold defined in SPM batch. 
% T0 indicates the shift of onsets to correspond with the slice order. SPM
% default T0 = 8 given T = 16. We assume T0=1 does not introduce shift.
%__________________________________________________________________________
%
% Written by Tibor Auer (tibor.auer@gmail.com)

THR = 0.5;

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);

%% Construct SPM and set parameters for iGLM & cGLM corrections
SPM.xY.RT = double(P.TR)/1000;
SPM.nscan = double(P.NrOfVolumes-P.nrSkipVol);

% basis function defaults
SPM.xBF.T = 16;
SPM.xBF.T0 = 1; % check for the desired onset shift
SPM.xBF.UNITS = 'scans';
SPM.xBF.Volterra   = 1;
SPM.xBF.name       = 'hrf';
SPM.xBF.length     = 32;
SPM.xBF.order      = 1;
SPM.xBF.dt = SPM.xY.RT/SPM.xBF.T;

SPM.xX.K.HParam = 128;
    
% protocol
if ~P.isRestingState
    % get conditions from ConditionForContrast
    [junk,regrInd] = ismember(P.ConditionForContrast,cellfun(@(x) x.ConditionName, P.Protocol.ConditionIndex, 'UniformOutput', false));
else
    regrInd = [];
end

if isDCM && strcmp(P.Prot, 'InterBlock')
    SPM.nscan = P.lengthDCMTrial;
end

if ~isempty(regrInd)
    for e = 1:numel(regrInd)
        SPM.Sess.U(e) = struct(...
            'name',{cellstr(P.Protocol.ConditionIndex{regrInd(e)}.ConditionName)},...
            'ons',P.Protocol.ConditionIndex{regrInd(e)}.OnOffsets(:,1),...
            'dur',(diff(P.Protocol.ConditionIndex{regrInd(e)}.OnOffsets')+1)',...
            'P',struct('name','none'),...
            'orth',1 ...
            );
    end
else
   SPM.Sess.U = []; 
end
SPM.Sess.C.C = [];
SPM.Sess.C.name = {};

SPM.xGX.iGXcalc = 'None';
SPM.xVi.form = sprintf('AR(%1.1f)',P.aAR1);

% masking threshold based on moco template (with lower relative threshold)
% TODO, seems just Matlab version solution:
%meanVol = mean(spm_read_vols(spm_vol(P.MCTempl)),[1,2,3]);
meanVol = mean2(mean(spm_read_vols(spm_vol(P.MCTempl)),1));
SPM.xM.TH = repmat(meanVol*THR,[1 SPM.nscan]);

SPM = spm_fmri_spm_ui(SPM);
save(fullfile(P.WorkFolder,'Settings','SPM.mat'),'SPM');
if exist(fullfile(pwd, 'SPM.mat'),'file'), delete('SPM.mat'); end
