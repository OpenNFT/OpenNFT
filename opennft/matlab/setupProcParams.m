function setupProcParams()
% Function to set up data processing parameters.
%
% input:
% Workspace variables.
%
% output:
% Output is assigned to workspace variables.
%
% The iGLM estimations are used for visualizations, however, note that
% negligible variations are possible in dynamic ROI update schemes or
% feedback estimations based on iGLM. 
%
% Note, the iGLM/cGLM contrasts are hard-coded and user-/study- defined,
% which is linked to the prepared SPM.mat structure.
% An end-user needs to set and justify their own parameter
% files and contrasts.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');
rtQA_matlab = evalin('base', 'rtQA_matlab');

evalin('base', 'clear mmImgViewTempl;');
evalin('base', 'clear mmStatVol;');
evalin('base', 'clear mmStatMap;');
evalin('base', 'clear mmOrthView;');

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);

if strcmp(P.DataType, 'DICOM')
    fDICOM = true;
    fIMAPH = false;
elseif strcmp(P.DataType, 'IMAPH')
    fDICOM = false;
    fIMAPH = true;
else
    fDICOM = false;
    fIMAPH = false;
end

%% SPM Settings
% It is recommended using the same interpolation for real-time
% realign and reslice functions. See spm_realign_rt() for further comments.
% 'interp' 4 is B-Spline 4th order in SPM12
mainLoopData.flagsSpmRealign = struct('quality',.9,'fwhm',5,'sep',4,...
    'interp',4,'wrap',[0 0 0],'rtm',0,'PW','','lkp',1:6);
mainLoopData.flagsSpmReslice = struct('quality',.9,'fwhm',5,'sep',4,...
    'interp',4,'wrap',[0 0 0],'mask',1,'mean',0,'which', 2);

%% Signal Processing Settings
P.VolumesNumber = P.NrOfVolumes - P.nrSkipVol;
% sliding window length in blocks, large value is used to ignore it.
P.nrBlocksInSlidingWindow = 100; % i.e disabled

% Kalman preset
S.Q = 0;
S.P = S.Q;
S.x = 0;
fPositDerivSpike = 0;
fNegatDerivSpike = 0;
S(1:P.NrROIs) = S;
fPositDerivSpike(1:P.NrROIs) = fPositDerivSpike;
fNegatDerivSpike(1:P.NrROIs) = fNegatDerivSpike;
mainLoopData.S = S;
mainLoopData.fPositDerivSpike(1:P.NrROIs) = fPositDerivSpike;
mainLoopData.fNegatDerivSpike(1:P.NrROIs) = fNegatDerivSpike;


% Scaling Init
tmp_posMin(1:P.NrROIs) = 0;
tmp_posMax(1:P.NrROIs) = 0;

mainLoopData.tmp_posMin = tmp_posMin;
mainLoopData.tmp_posMax = tmp_posMax;

P.rawTimeSeries = [];
mainLoopData.rawTimeSeries = [];
mainLoopData.kalmanProcTimeSeries = [];
mainLoopData.displRawTimeSeries = [];
mainLoopData.scalProcTimeSeries = [];
mainLoopData.emaProcTimeSeries = [];

mainLoopData.posMin = [];
mainLoopData.posMax = [];
mainLoopData.mposMax = [];
mainLoopData.mposMin = [];

mainLoopData.blockNF = 0;
mainLoopData.firstNF = 0;

rtQA_python.meanSNR = [];
rtQA_python.m2SNR = [];
rtQA_python.rSNR = [];
rtQA_python.meanBas = [];
rtQA_python.varBas = [];
rtQA_python.meanCond = [];
rtQA_python.varCond = [];
rtQA_python.rCNR = [];
rtQA_python.excFDIndexes_1 = [];
rtQA_python.excFDIndexes_2 = [];
rtQA_python.excMDIndexes = [];

rtQA_matlab.kalmanSpikesPos = zeros(P.NrROIs,P.VolumesNumber);
rtQA_matlab.kalmanSpikesNeg = zeros(P.NrROIs,P.VolumesNumber);

rtQA_matlab.snrData.snrVol = [];
rtQA_matlab.snrData.meanSmoothed = [];
rtQA_matlab.snrData.m2Smoothed = [];
rtQA_matlab.snrData.meanNonSmoothed = [];
rtQA_matlab.snrData.m2NonSmoothed = [];
rtQA_matlab.snrMapCreated = 0; 

if ~P.isRestingState
    rtQA_matlab.cnrData.cnrVol = []
    
    rtQA_matlab.cnrData.basData.mean = [];
    rtQA_matlab.cnrData.basData.m2 = [];
    rtQA_matlab.cnrData.basData.meanSmoothed = [];
    rtQA_matlab.cnrData.basData.m2Smoothed = [];
    rtQA_matlab.cnrData.basData.iteration = 1;

    rtQA_matlab.cnrData.condData.mean = [];
    rtQA_matlab.cnrData.condData.m2 = [];
    rtQA_matlab.cnrData.condData.meanSmoothed = [];
    rtQA_matlab.cnrData.condData.m2Smoothed = [];
    rtQA_matlab.cnrData.condData.iteration = 1;
end

%% DCM Settings
if isDCM
    % This is to simplify the P.Protocol parameter listings for DCM,
    % in scans
    P.lengthDCMTrial = 108;
    P.lengthDCMPeriod = 150;
    P.beginDCMblock = [1:150:1050];
    P.endDCMblock = [108:150:1050];
    P.indNFTrial = 0;
    P.nrNFtrials = 7;
    P.nrDisplayScans = 4; % feedback display duration in scans
    P.nrBlankScans = 38;  % DCM estiation duration in scans
    P.dcmRemoveInterval = P.nrBlankScans + P.nrDisplayScans;
    
    % used adaptive DCM ROIs per trial: 1-Group, 2-New, 3-Advanced
    mainLoopData.adaptROIs = [];
    % DCM block counter
    mainLoopData.NrDCMblocks = -1;
    % Reard per DCM trial
    mainLoopData.tReward = 0;
    % adding regressors on the level of DCM computing
    P.fRegrDcm = true;
end

%% AR(1)
if ~isDCM
    % AR(1) for cGLM, i.e. nfb signal processing
    P.cglmAR1 = true;
    % AR(1) for iGLM
    P.iglmAR1 = true;
else
    % For DCM:
    % use smoothing for DCM (optional, to explore the differences)
    P.smForDCM = true;
    % not implmented for cGLM
    P.cglmAR1 = false;
    % AR(1) for iGLM (optional, to explore the differences)
    P.iglmAR1 = true;
end
P.aAR1 = 0.2; % default SPM value

%% adding nuissance regressors to iGLM
P.isRegrIGLM = true;

%% adding nuissance regressors to iGLM
% Note, less efficient regressing out of the motion-related regressors than
% offline GLM given the whole motion regressors at once.
P.isMotionRegr = true;

%% adding high-pass filter to iGLM
% Note, different data processing iGLM approach as compared to SPM
P.isHighPass = true;

%% adding linear regressor
P.isLinRegr = true;
P.linRegr = zscore((1:double(P.NrOfVolumes-P.nrSkipVol))');

SPM = setupSPM(P);
% TODO: To check
% High-pass filter
mainLoopData.K.X0 = SPM.xX.K.X0;

if ~P.isRestingState
    tmpindexesCond = find(SPM.xX.X(:,2)>0.6);
    tmpindexesBas = find(SPM.xX.X(:,2)<0.1);
    indexesBas = tmpindexesBas(1:end-1)+1;
    indexesCond = tmpindexesCond-1;
    P.inds = { indexesBas, indexesCond }
    rtQA_matlab.cnrData.basData.indexesBas = indexesBas;
    rtQA_matlab.cnrData.condData.indexesCond = indexesCond;
end
    
if ~P.isRestingState
    
    if ~P.iglmAR1
        % exclude constant regressor
        mainLoopData.basFct = SPM.xX.X(:,1:end-1);
    else
        % exclude constant regressor
        mainLoopData.basFct = arRegr(P.aAR1, SPM.xX.X(:,1:end-1));
    end
    [mainLoopData.numscan, mainLoopData.nrBasFct] = size(mainLoopData.basFct);
    % see notes above definition of spmMaskTh value
    mainLoopData.spmMaskTh = mean(SPM.xM.TH)*ones(size(SPM.xM.TH)); % SPM.xM.TH;
    mainLoopData.pVal = .01;
    mainLoopData.statMap3D_iGLM = [];

    % PSC
    if isPSC && strcmp(P.Prot, 'Cont') && ~fIMAPH
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol, 2);
        % this contrast does not count constant term
        mainLoopData.tContr.pos = strcmp(P.CondNames,P.CondName)';
        mainLoopData.tContr.neg = ~mainLoopData.tContr.pos;
    end

    if isPSC && strcmp(P.Prot, 'Inter') && ~fIMAPH
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol, 2);
        % this contrast does not count constant term
        mainLoopData.tContr.pos = strcmp(P.CondNames,P.CondName)';
        mainLoopData.tContr.neg = ~mainLoopData.tContr.pos;
    end

    % PSC (Phillips)
    if isPSC && strcmp(P.Prot, 'Cont') && fIMAPH
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol,1);
        % this contrast does not count constant term
        mainLoopData.tContr.pos = [1];
        mainLoopData.tContr.neg = [-1];
    end

    % DCM
    if isDCM && strcmp(P.Prot, 'InterBlock')
        % this contrast does not count constant term
        tmpSpmDesign = SPM.xX.X(1:P.lengthDCMTrial,2);
        mainLoopData.tContr.pos = [-1; 1];
        mainLoopData.tContr.neg = [1; -1];
        [mainLoopData.DCM_EN, mainLoopData.dcmParTag, ...
            mainLoopData.dcmParOpp] = dcmPrep(SPM);
    end

    % SVM
    if isSVM && strcmp(P.Prot, 'Cont')
        mainLoopData.basFct = mainLoopData.basFct(:,2);
        mainLoopData.nrBasFct = 1;
        % this contrast does not count constant term
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol,strcmp(P.CondNames,P.CondName));
        mainLoopData.tContr.pos = [1];
        mainLoopData.tContr.neg = [-1];
    end

    %% High-pass filter for iGLM given by SPM
    mainLoopData.K = SPM.xX.K;

    clear SPM

    %% AR(1) for cGLM in signal preproessing
    if ~P.iglmAR1
        P.spmDesign = tmpSpmDesign;
    else
        P.spmDesign = arRegr(P.aAR1, tmpSpmDesign);
    end
else
    mainLoopData.basFct = [];
    mainLoopData.nrBasFct = 0;
    mainLoopData.numscan = 0;
    [mainLoopData.numscan, mainLoopData.nrHighPassFct] = size(mainLoopData.K.X0);
    P.spmDesign = [];
    mainLoopData.tContr.pos = ones(6,1);
    mainLoopData.tContr.neg = -ones(6,1);
    mainLoopData.spmMaskTh = mean(SPM.xM.TH)*ones(size(SPM.xM.TH));
    mainLoopData.pVal = .1;
    mainLoopData.statMap3D_iGLM = [];
end

mainLoopData.mf = [];
mainLoopData.npv = 0;
mainLoopData.statMapCreated = 0;

%% Get motion realignment template data and volume
infoVolTempl = spm_vol(P.MCTempl);
mainLoopData.infoVolTempl = infoVolTempl;
imgVolTempl  = spm_read_vols(infoVolTempl);
dimTemplMotCorr     = infoVolTempl.dim;
matTemplMotCorr     = infoVolTempl.mat;

mainLoopData.dimTemplMotCorr = dimTemplMotCorr;
mainLoopData.matTemplMotCorr = matTemplMotCorr;
mainLoopData.imgVolTempl  = imgVolTempl;

% Realign preset
A0=[];x1=[];x2=[];x3=[];wt=[];deg=[];b=[];
R(1,1).mat = matTemplMotCorr;
R(1,1).dim = dimTemplMotCorr;
R(1,1).Vol = imgVolTempl;

mainLoopData.R = R;
mainLoopData.A0 = A0;
mainLoopData.x1 = x1;
mainLoopData.x2 = x2;
mainLoopData.x3 = x3;
mainLoopData.wt = wt;
mainLoopData.deg = deg;
mainLoopData.b = b;

% make output data folder
P.nfbDataFolder = [P.WorkFolder filesep 'NF_Data_' num2str(P.NFRunNr)];
if ~exist(P.nfbDataFolder, 'dir')
    mkdir(P.nfbDataFolder);
end

assignin('base', 'rtQA_matlab', rtQA_matlab);
assignin('base', 'rtQA_python', rtQA_python);
assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
