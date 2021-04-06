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
if P.isRTQA
    rtQA_matlab = evalin('base', 'rtQA_matlab');
end

evalin('base', 'clear mmImgViewTempl;');
evalin('base', 'clear mmStatVol;');
evalin('base', 'clear mmStatMap;');
evalin('base', 'clear mmStatMap_neg;');
evalin('base', 'clear mmOrthView;');

if ~exist(fullfile(P.WorkFolder,'Settings')), mkdir(fullfile(P.WorkFolder,'Settings')); end

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

% TCP Data
if P.UseTCPData
    data.watch = P.WatchFolder;
    data.LastName = '';
    data.ID = '';
    data.FirstFileName = P.FirstFileName;
    
    try tcp = evalin('base','tcp'); catch E
        if strcmp(E.identifier,'MATLAB:UndefinedFunction'), tcp = ImageTCPClass(P.TCPDataPort);
        else, throw(E); end
    end

    tcp.setHeaderFromDICOM(data);
    if ~tcp.Open
        try tcp.WaitForConnection; catch E
            if strcmp(E.message,'No valid handler! already closed?')
                
            else
                throw(E);
            end
        end
    end
    tcp.ReceiveInitial;
    % tcp.Quiet = true;
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
mainLoopData.blockTask2 = 0;
mainLoopData.lastTask2 = 0;
mainLoopData.blockTask3 = 0;
mainLoopData.lastTask3 = 0;

%% DCM Settings
if isDCM
    % This is to simplify the P.Protocol parameter listings for DCM,
    
    % -- read timing parameters from JSON file ----------------------------
    tim = loadTimings(P.ProtocolFile); 
    
    % in scans
    P.indNFTrial        = 0;
    P.lengthDCMTrial    = tim.trialLength;
    P.nrNFtrials        = tim.numberOfTrials;
    P.nrDisplayScans    = tim.feedbackDisplayDurationInScans; 
    P.nrBlankScans      = tim.feedbackEstimationDurationInScans;
    P.dcmRemoveInterval = P.nrBlankScans + P.nrDisplayScans;
    P.lengthDCMPeriod   = P.lengthDCMTrial + P.nrDisplayScans + P.nrBlankScans;
    P.beginDCMblock     = double([1:P.lengthDCMPeriod:P.lengthDCMPeriod*P.nrNFtrials]);
    P.endDCMblock       = double([P.lengthDCMTrial:P.lengthDCMPeriod:P.lengthDCMPeriod*P.nrNFtrials]);

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
if ~P.isRestingState
    P.isMotionRegr = true;
else
    P.isMotionRegr = false;
end

%% adding high-pass filter to iGLM
% Note, different data processing iGLM approach as compared to SPM
P.isHighPass = false;

%% adding linear regressor
P.isLinRegr = true;
P.linRegr = zscore((1:double(P.NrOfVolumes-P.nrSkipVol))');

SPM = setupSPM(P);
% TODO: To check
% High-pass filter
mainLoopData.K.X0 = SPM.xX.K.X0;

%% Explicit contrasts (optional)
if isfield(P,'Contrast')
    mainLoopData.tContr.pos = P.Contrast; 
    mainLoopData.tContr.neg = -P.Contrast; 
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
    if isPSC && (strcmp(P.Prot, 'Cont') || strcmp(P.Prot, 'ContTask'))
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol,contains(SPM.xX.name, P.CondIndexNames( 2 ))); % Index for Regulation block == 2
    end
    if isPSC && strcmp(P.Prot, 'Inter')
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol,contains(SPM.xX.name, [string(P.CondName),string(P.Task2Name),string(P.Task3Name),P.DispName]));
    end

    % DCM
    if isDCM && strcmp(P.Prot, 'InterBlock')
        % this contrast does not count constant term
        tmpSpmDesign = SPM.xX.X(1:P.lengthDCMTrial,2);
        [mainLoopData.DCM_EN, mainLoopData.dcmParTag, ...
            mainLoopData.dcmParOpp] = dcmPrep(SPM);
    end

    % SVM
    if isSVM && strcmp(P.Prot, 'Cont')
        mainLoopData.basFct = mainLoopData.basFct(:,find(contains(SPM.xX.name, P.CondIndexNames( 2 )))); % Index for Regulation block == 2
        mainLoopData.nrBasFct = 1;
        % this contrast does not count constant term
        tmpSpmDesign = SPM.xX.X(1:P.NrOfVolumes-P.nrSkipVol,contains(SPM.xX.name, P.CondIndexNames( 2 ))); % Index for Regulation block == 2
    end
        
    %% High-pass filter for iGLM given by SPM
    mainLoopData.K = SPM.xX.K;

    %% AR(1) for cGLM in signal preproessing
    if ~P.iglmAR1
        P.spmDesign = tmpSpmDesign;
    else
        P.spmDesign = arRegr(P.aAR1, tmpSpmDesign);
    end

    % PSC
    if isPSC && (strcmp(P.Prot, 'Cont') || strcmp(P.Prot, 'ContTask') || strcmp(P.Prot, 'Inter'))

        if P.NFRunNr > 1
            lSpmDesign = size(tmpSpmDesign,1);
            P.prevNfbDataFolder = fullfile(P.WorkFolder,['NF_Data_' sprintf('%d',P.NFRunNr-1)]);
            % get motion correction parameters
            pathPrevP = dir(fullfile(P.prevNfbDataFolder,'*_P.mat'));
            prevP = load(fullfile(P.prevNfbDataFolder,pathPrevP.name));
            % get time-series
            pathPrevTS = dir(fullfile(P.prevNfbDataFolder,'*_raw_tsROIs.mat'));
            mainLoopData.prevTS = load(fullfile(P.prevNfbDataFolder,pathPrevTS.name));
            % construct regressors
            tmpRegr = [ones(lSpmDesign,1) P.linRegr zscore(prevP.motCorrParam)];
            if P.cglmAR1
                mainLoopData.prev_cX0 = arRegr(P.aAR1,tmpRegr);
            end
            mainLoopData.prev_cX0 = [tmpRegr, P.spmDesign];
        end

    end

else
    mainLoopData.basFct = [];
    mainLoopData.nrBasFct = 6; % size of motion regressors, P.motCorrParam
    mainLoopData.numscan = 0;
    [mainLoopData.numscan, mainLoopData.nrHighPassFct] = size(mainLoopData.K.X0);
    P.spmDesign = [];
    mainLoopData.spmMaskTh = mean(SPM.xM.TH)*ones(size(SPM.xM.TH));
    mainLoopData.pVal = .1;
    mainLoopData.statMap3D_iGLM = [];
end

%% rGLM beta init
mainLoopData.betRegr = cell(P.NrROIs,1);
for i=1:P.NrROIs
    % TODO:
    % 2 - linear trend and constant; 6 - motion regressors
    mainLoopData.betRegr{i} = zeros(P.NrOfVolumes-P.nrSkipVol, 2+6+size(P.spmDesign,2));
end

%% rtQA init
rtQA_matlab.snrMapCreated = 0; 
if P.isRTQA
    % rtQA python saving preparation
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
    rtQA_python.FD = [];
    rtQA_python.MD = [];
    rtQA_python.rMSE = [];

    % rtQA matlab part structure preparation
    if isDCM
        rtQA_matlab.kalmanSpikesPos = zeros(P.NrROIs,P.lengthDCMTrial*P.nrNFtrials);
        rtQA_matlab.kalmanSpikesNeg = zeros(P.NrROIs,P.lengthDCMTrial*P.nrNFtrials);        
        rtQA_matlab.varErGlmProcTimeSeries = zeros(P.NrROIs,P.lengthDCMTrial*P.nrNFtrials);
        rtQA_matlab.tGlmProcTimeSeries.pos = zeros(P.NrROIs,P.lengthDCMTrial*P.nrNFtrials);
        rtQA_matlab.tGlmProcTimeSeries.neg = zeros(P.NrROIs,P.lengthDCMTrial*P.nrNFtrials);
    else
        rtQA_matlab.kalmanSpikesPos = zeros(P.NrROIs,P.VolumesNumber);
        rtQA_matlab.kalmanSpikesNeg = zeros(P.NrROIs,P.VolumesNumber);
        rtQA_matlab.varErGlmProcTimeSeries = zeros(P.NrROIs,P.VolumesNumber);
        rtQA_matlab.tGlmProcTimeSeries.pos = zeros(P.NrROIs,P.VolumesNumber);
        rtQA_matlab.tGlmProcTimeSeries.neg = zeros(P.NrROIs,P.VolumesNumber);
    end
    
    rtQA_matlab.snrData.snrVol = [];
    rtQA_matlab.snrData.meanSmoothed = [];
    rtQA_matlab.snrData.m2Smoothed = [];
    rtQA_matlab.snrData.meanNonSmoothed = [];
    rtQA_matlab.snrData.m2NonSmoothed = [];
    rtQA_matlab.snrData.iteration = 1;

    rtQA_matlab.betRegr = mainLoopData.betRegr;
    
    rtQA_matlab.Bn = cell(P.NrROIs,1);
    rtQA_matlab.var = cell(P.NrROIs,1);
    rtQA_matlab.tn.pos = cell(P.NrROIs,1);
    rtQA_matlab.tn.neg = cell(P.NrROIs,1);

    if ~P.isRestingState
        rtQA_matlab.cnrData.cnrVol = [];

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

        % indexes of baseline and condition for CNR calculation
        tmpindexesCond = find(SPM.xX.X(:,contains(SPM.xX.name, P.CondIndexNames( 2 )))>0.6); % Index for Regulation block == 2
        tmpindexesBas = find(SPM.xX.X(:,contains(SPM.xX.name, P.CondIndexNames( 2 )))<0.1); % Index for Regulation block == 2
        if isDCM
            tmpindexesBas = tmpindexesBas(1:end-1)+1;
            tmpindexesCond = tmpindexesCond-1;
            indexesBas = [];
            indexesCond = [];
            for i=0:P.nrNFtrials-1
                indexesBas = [ indexesBas; tmpindexesBas+i*(P.lengthDCMPeriod-P.dcmRemoveInterval) ];
                indexesCond = [ indexesCond; tmpindexesCond+i*(P.lengthDCMPeriod-P.dcmRemoveInterval) ];
            end
        else
            indexesBas = tmpindexesBas(1:end-1)+1;
            indexesCond = tmpindexesCond-1;
        end
        P.inds = { indexesBas, indexesCond };
        rtQA_matlab.cnrData.basData.indexesBas = indexesBas;
        rtQA_matlab.cnrData.condData.indexesCond = indexesCond;
    end
end

clear SPM

mainLoopData.mf = [];
mainLoopData.npv = 0;
mainLoopData.statMapCreated = 0;

%% Get motion realignment template data and volume
infoVolTempl = spm_vol(P.MCTempl);
mainLoopData.infoVolTempl = infoVolTempl;
tmp_imgVolTempl  = spm_read_vols(infoVolTempl);
dimTemplMotCorr     = infoVolTempl.dim;
matTemplMotCorr     = infoVolTempl.mat;

isZeroPadVol = 1;
if isZeroPadVol
    nrZeroPadVol = 3;
    zeroPadVol = zeros(dimTemplMotCorr(1),dimTemplMotCorr(2),nrZeroPadVol);
    dimTemplMotCorr(3) = dimTemplMotCorr(3)+nrZeroPadVol*2;
    imgVolTempl = cat(3, cat(3, zeroPadVol, tmp_imgVolTempl), zeroPadVol);
end

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


if P.isRTQA
    assignin('base', 'rtQA_matlab', rtQA_matlab);
    assignin('base', 'rtQA_python', rtQA_python);
end

assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);
if P.UseTCPData, assignin('base', 'tcp', tcp); end

end

function tim = loadTimings(protocoFilePath)
% Loads the DCM timings from the protocol JSON file. To be specified 
% as follows: Within the key "dcmdef", insert a key "timings"
%
% "timings": {
%     "trialLength": 108,
%     "numberOfTrials": 7,
%     "feedbackDisplayDurationInScans": 4,
%     "feedbackEstimationDurationInScans": 38
% }
% 
% This function will read those values and return an error if they are 
% misspecified.
% --------------------------------------------------------------------------

% -- Read the file ---------------------------------------------------------

try
    prt = loadjson(protocoFilePath);
catch
    error('Invalid path to protocol file.')
end

% -- Extract timings and check for completeness and type -------------------

tim            = prt.dcmdef.timings;
requiredFields = {'trialLength','numberOfTrials',...
                  'feedbackDisplayDurationInScans',...
                  'feedbackEstimationDurationInScans'};

for fn = requiredFields
    if ~strcmp(fn{:},fieldnames(tim))
        error('protocol JSON file missing field: %s',fn{:})
    end
end

for fn = fieldnames(tim)'
    if ~isnumeric(tim.(fn{:}))
        error('Timings.%s is invalid. Make sure its a number.',fn{:})
    end
end

end

