function preprVol(inpFileName, indVol)
% Function to call real-time data preprocessing analyses.
%
% input:
% indVol - volume(scan) index
% inpFileName - current file name
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

if indVol <= P.nrSkipVol
    return;
end

% Get Matlab time stamp related to # t2 using PTB-3 function.
% For clarification, see OpenNFT timing diagram on the website and our ms.
% Note that there is a small difference between this one and recordEvent()
% times since they are taken subsequently. We also don't know how PTB
% functions could deal with time-referencing issues between 2 parallel Matlab
% processes, i.e. core process and PTB helper.
if indVol == double(P.nrSkipVol)+1
    P.expOns_t2 = GetSecs;
    fprintf('\n\n=============')
    fprintf('\nMatlab time stamp t2!')
    fprintf('\n=============\n\n')
end

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);
if isDCM
    ROIsAnat = evalin('base', 'ROIsAnat');
end

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

% realign and reslice init
R = mainLoopData.R;
A0 = mainLoopData.A0;
x1 = mainLoopData.x1;
x2 = mainLoopData.x2;
x3 = mainLoopData.x3;
wt = mainLoopData.wt;
deg = mainLoopData.deg;
b = mainLoopData.b;

matVol = mainLoopData.matVol;
matTemplMotCorr = mainLoopData.matTemplMotCorr;
dicomInfoVox = mainLoopData.dicomInfoVox;
dimTemplMotCorr = mainLoopData.dimTemplMotCorr;
dimVol = mainLoopData.dimVol;
slNrImg2DdimX = mainLoopData.slNrImg2DdimX;
slNrImg2DdimY = mainLoopData.slNrImg2DdimY;
img2DdimX = mainLoopData.img2DdimX;
img2DdimY = mainLoopData.img2DdimY;

% Flags
flagsSpmReslice = mainLoopData.flagsSpmReslice;
flagsSpmRealign = mainLoopData.flagsSpmRealign;

% iGLM init
nrVoxInVol = mainLoopData.nrVoxInVol;
nrBasFct = mainLoopData.nrBasFct;
numscan = mainLoopData.numscan;
spmMaskTh = mainLoopData.spmMaskTh;
basFct = mainLoopData.basFct;

% type conversion Matlab-Python bug
indVolNorm = mainLoopData.indVolNorm;
indVolNorm = double(indVolNorm);

% trial indices for DCM feedback
if isDCM
    % skip preprocessing for rest epoch and NF display
    if mainLoopData.flagEndDCM
        assignin('base', 'P', P);
        return;
    end
    indNFTrial = P.indNFTrial;
end

%% EPI Data Preprocessing
% Read Data in real-time
if fDICOM
    dcmData = double(dicomread(inpFileName));
end
if fIMAPH
    % Note, possibly corrupted Phillips rt data export
    infoVol = spm_vol(inpFileName);
    imgVol  = spm_read_vols(infoVol);
    % If necessary, flip rt time-series so that it matches the template
    % set in setupFirstVolume.m, setupProcParams.m, selectROI.m
    imgVol  = fliplr(imgVol);
end

% update parameters
if fDICOM
    R(2,1).mat = matVol;
    R(2,1).dim = dimVol;
    R(2,1).Vol = img2Dvol3D(dcmData, slNrImg2DdimX, slNrImg2DdimY, dimVol);
end
if fIMAPH
    R(2,1).mat = matTemplMotCorr;
    R(2,1).dim = dimTemplMotCorr;
    R(2,1).Vol = imgVol;
end

tStartMotCorr = tic;

%% realign
[R, A0, x1, x2, x3, wt, deg, b, nrIter] = ...
    spm_realign_rt(R, flagsSpmRealign, indVol,  ...
    P.nrSkipVol + 1, A0, x1, x2, x3, wt, deg, b);

mainLoopData.nrIter(indVolNorm) = nrIter;
mainLoopData.A0 = A0;
mainLoopData.x1 = x1;
mainLoopData.x2 = x2;
mainLoopData.x3 = x3;
mainLoopData.wt = wt;
mainLoopData.deg = deg;
mainLoopData.b = b;

%% MC params
tmpMCParam = spm_imatrix(R(2,1).mat / R(1,1).mat);
if (indVol == P.nrSkipVol + 1)
    P.offsetMCParam = tmpMCParam(1:6);
end
P.motCorrParam(indVolNorm,:) = tmpMCParam(1:6)-P.offsetMCParam;
%P.motCorrParam(indVolNorm,:) = tmpMCParam(1:6);

%% reslice
reslVol = spm_reslice_rt(R, flagsSpmReslice);
tStopMC = toc(tStartMotCorr);

%% Smoothing
if isPSC || isSVM
    gKernel = [5 5 5] ./ dicomInfoVox;
end
if isDCM
    gKernel = [5 5 5] ./ dicomInfoVox;
end
mainLoopData.gKernel = gKernel;

smReslVol = zeros(dimVol);
spm_smooth(reslVol, smReslVol, gKernel);

if isPSC || isSVM
    % Smoothed Vol 3D -> 2D
    smReslVol_2D = vol3Dimg2D(smReslVol, slNrImg2DdimX, slNrImg2DdimY, ...
        img2DdimX, img2DdimY, dimVol);
    mainLoopData.smReslVol_2D = smReslVol_2D;
end

if isDCM
    if ~P.smForDCM
        % NoN-Smoothed Vol 3D -> 2D
        nosmReslVol_2D = vol3Dimg2D(reslVol, slNrImg2DdimX, ...
            slNrImg2DdimY, img2DdimX, img2DdimY, dimVol);
        mainLoopData.nosmReslVol_2D = nosmReslVol_2D;
    else
        % Smoothed Vol 3D -> 2D
        smReslVol_2D = vol3Dimg2D(smReslVol, slNrImg2DdimX, ...
            slNrImg2DdimY, img2DdimX, img2DdimY, dimVol);
        mainLoopData.smReslVol_2D = smReslVol_2D;
    end
end

%% AR(1) iGLM, i.e. after assigning _2D matrices used for ROI's extractions
if P.iglmAR1
    if indVolNorm == 1
        % initalize first AR(1) volume
        mainLoopData.smReslVolAR1_1 = (1 - P.aAR1) * smReslVol;
    else
        mainLoopData.smReslVolAR1_1 = smReslVol - ...
            P.aAR1 * mainLoopData.smReslVolAR1_1;
    end
    smReslVol = mainLoopData.smReslVolAR1_1;
end

tStopSm = toc(tStartMotCorr);

%% iGLM 
if isDCM
    fIGLM_onset = isempty(find(P.beginDCMblock == indVol-P.nrSkipVol,1));
else
    fIGLM_onset =  true;
end

if isIGLM
    fLockedTempl = 0; % 0 = update, 1 = fix
    
    if isfield(mainLoopData, 'iGLMinit') && fIGLM_onset
        %% Get initialized variables
        iGLMinit = mainLoopData.iGLMinit;
        
        pVal = mainLoopData.pVal;
        tContr = mainLoopData.tContr;
        nrBasFctRegr = mainLoopData.nrBasFctRegr;
        Cn = mainLoopData.Cn;
        Dn = mainLoopData.Dn;
        s2n = mainLoopData.s2n;
        tn = mainLoopData.tn;
        tTh = mainLoopData.tTh;
        dyntTh = mainLoopData.dyntTh;
        
        statMapVect = mainLoopData.statMapVect;
        statMap3D = mainLoopData.statMap3D; % this structure is set with 0
        statMap2D = mainLoopData.statMap2D; % this structure is set with 0
        
        if ~fLockedTempl
            % assign Tempalte
            max_smReslVol = max(smReslVol(:));
            min_smReslVol = min(smReslVol(:));
            normSmReslVol = (smReslVol-min_smReslVol) / ...
                (max_smReslVol-min_smReslVol);
            normSmReslVol_2D = vol3Dimg2D(normSmReslVol, slNrImg2DdimX, ...
                slNrImg2DdimY, img2DdimX, img2DdimY, dimVol);
            imgViewTempl = uint8(normSmReslVol_2D * 255);
            assignin('base', 'imgViewTempl', imgViewTempl)
            m = evalin('base', 'mmImgViewTempl');
            shift = 0 * length(imgViewTempl(:)) + 1;
            m.Data(shift:end) = imgViewTempl(:);
        end
        
    else
        %% Initialize variables
        % assign Tempalte
        max_smReslVol = max(smReslVol(:));
        min_smReslVol = min(smReslVol(:));
        normSmReslVol = (smReslVol-min_smReslVol) / ...
            (max_smReslVol-min_smReslVol);
        normSmReslVol_2D = vol3Dimg2D(normSmReslVol, slNrImg2DdimX, ...
            slNrImg2DdimY, img2DdimX, img2DdimY, dimVol);
        mainLoopData.normSmReslVol_2D = normSmReslVol_2D;
        imgViewTempl = uint8(normSmReslVol_2D * 255);
        assignin('base', 'imgViewTempl', imgViewTempl)
        m = evalin('base', 'mmImgViewTempl');
        shift = 0 * length(imgViewTempl(:)) + 1;
        m.Data(shift:end) = imgViewTempl(:);
        
        pVal = mainLoopData.pVal;
        tContr = mainLoopData.tContr;
        
        if ~P.isRegrIGLM
            nrBasFctRegr = 1;
        else
            nrHighPassRegr = size(mainLoopData.K.X0,2);
            nrMotRegr = 6;
            if P.isHighPass && P.isMotionRegr && P.isLinRegr
                nrBasFctRegr = nrMotRegr+nrHighPassRegr+2;
                % adding 6 head motion, linear, high-pass filter, and
                % constant regressors
            elseif ~P.isHighPass && P.isMotionRegr && P.isLinRegr
                nrBasFctRegr = nrMotRegr+2;
                % adding 6 head motion, linear, and constant regressors
            elseif P.isHighPass && ~P.isMotionRegr && P.isLinRegr
                nrBasFctRegr = nrHighPassRegr+2;
                % adding high-pass filter, linear, and constant regressors
            elseif P.isHighPass && ~P.isMotionRegr && ~P.isLinRegr
                nrBasFctRegr = nrHighPassRegr+1;
                % adding high-pass filter, and constant regressors
            elseif ~P.isHighPass && ~P.isMotionRegr && P.isLinRegr
                nrBasFctRegr = 2; % adding linear, and constant regressors
            end
        end
        Cn = zeros(nrBasFct + nrBasFctRegr);
        Dn = zeros(nrVoxInVol, nrBasFct + nrBasFctRegr);
        s2n = zeros(nrVoxInVol, 1);
        tn = zeros(nrVoxInVol, 1);
        tTh = zeros(numscan, 1);
        dyntTh = 0;
        mainLoopData.iGLMinit = 'done';
        
        statMapVect = zeros(nrVoxInVol, 1);
        statMap3D = zeros(dimVol);
        mainLoopData.statMapVect = statMapVect;
        mainLoopData.statMap3D = statMap3D;
        statMap2D = zeros(img2DdimY,img2DdimX);
        mainLoopData.statMap2D = statMap2D;
    end
    
    if isPSC || isSVM
        indIglm = indVolNorm;
    end
    if isDCM
        indIglm = (indVolNorm - P.indNFTrial * P.lengthDCMTrial);
    end
    
    % set regressors of no interest
    if P.isRegrIGLM
        % note, constant regressor is added at the end
        if P.isHighPass && P.isMotionRegr && P.isLinRegr
            tmpRegr = [zscore(P.motCorrParam(1:indIglm,:)), ...
                P.linRegr(1:indIglm), ...
                mainLoopData.K.X0(1:indIglm,:), ...
                ones(indIglm,1)];
        elseif ~P.isHighPass && P.isMotionRegr && P.isLinRegr
            tmpRegr = [zscore(P.motCorrParam(1:indIglm,:)), ...
                P.linRegr(1:indIglm), ...
                ones(indIglm,1)];
        elseif P.isHighPass && ~P.isMotionRegr && P.isLinRegr
            tmpRegr = [P.linRegr(1:indIglm), ...
                mainLoopData.K.X0(1:indIglm,:), ...
                ones(indIglm,1)];
        elseif P.isHighPass && ~P.isMotionRegr && ~P.isLinRegr
            tmpRegr = [mainLoopData.K.X0(1:indIglm,:), ones(indIglm,1)];
        elseif ~P.isHighPass && ~P.isMotionRegr && P.isLinRegr
            tmpRegr = [P.linRegr(1:indIglm), ones(indIglm,1)];
        end
    else
        tmpRegr = ones(indIglm,1);
    end
    
    % AR(1) for regressors of no interest
    if P.iglmAR1
        tmpRegr = arRegr(P.aAR1,tmpRegr);
    end
    % combine with prepared basFct design regressors
    basFctRegr = [basFct(1:indIglm,:), tmpRegr];
    % account for contrast term in contrast vector (+1)
    tContr = [tContr; zeros(nrBasFctRegr,1)];
    % estimate iGLM
    [idxActVoxIGLM, dyntTh, tTh, Cn, Dn, s2n, tn, neg_e2n] = ...
        iGlmVol(Cn, Dn, s2n, tn, smReslVol(:), indIglm, ...
        (nrBasFct+nrBasFctRegr), tContr, basFctRegr, pVal, ...
        dyntTh, tTh, spmMaskTh);
    
    % catch negative iGLM estimation error message for log
    mainLoopData.neg_e2n{indIglm} = neg_e2n;
    if ~isempty(neg_e2n)
        disp('HERE THE NEGATIVE e2n!!!')
    end
    
    mainLoopData.nrBasFctRegr = nrBasFctRegr;
    mainLoopData.Cn = Cn;
    mainLoopData.Dn = Dn;
    mainLoopData.s2n = s2n;
    mainLoopData.tn = tn;
    mainLoopData.tTh = tTh;
    mainLoopData.dyntTh = dyntTh;
    mainLoopData.idxActVoxIGLM{indVolNorm} = idxActVoxIGLM;
else
    idxActVoxIGLM = [];
end

%% sharing iGLM results 
mainLoopData.statMapCreated = 0;
statMap_2D = zeros(img2DdimY,img2DdimX);
if ~isempty(idxActVoxIGLM) && max(tn) > 0 % handle empty activation map
    % and division by 0
    maskedStatMapVect = tn(idxActVoxIGLM);
    maxTval = max(maskedStatMapVect);
    statMapVect = maskedStatMapVect;
    statMap3D(idxActVoxIGLM) = statMapVect;
    
    clear idxActVoxIGLM
    
    statMap2D = vol3Dimg2D(statMap3D, slNrImg2DdimX, slNrImg2DdimY, ...
        img2DdimX, img2DdimY, dimVol) / maxTval;
    
    posIdx2D = find(statMap2D > 0);
    pythonPosIdx2D = posIdx2D - 1;
    
    assignin('base', 'strIdx', matData2strData(pythonPosIdx2D));
    tmpStrData = matData2strData(statMap2D(posIdx2D)*255);
    assignin('base', 'strStatMap', tmpStrData);
    
    % shared for SPM matlab helper
    m = evalin('base', 'mmStatVol');
    m.Data.statVol = statMap3D;
    mainLoopData.statMapCreated = 1;    
end

%% storage of iGLM results, could be disabled to save time
if ~isDCM
    if indIglm == P.NrOfVolumes - P.nrSkipVol
        mainLoopData.statMap3D_iGLM = statMap3D;
    end
else
    if indIglm == P.lengthDCMTrial
        mainLoopData.statMap3D_iGLM(:,:,:,mainLoopData.NrDCMblocks+1) = ...
            statMap3D;
        % save, optional
        statVolData = statMap3D;
        % FIXME
        save([P.nfbDataFolder filesep 'statVolData_' sprintf('%02d', ...
            mainLoopData.NrDCMblocks+1) '.mat'],'statVolData');
    end
end

tStopIGLM = toc(tStartMotCorr);
fprintf('TIMING: %d iter - PREPROC MC: %d s - SMOOTH: %d s - IGLM: %d s',...
    nrIter, tStopMC, tStopSm-tStopMC, tStopIGLM-tStopSm);

%% dynamic ROI mask based on statMap2D
if isDCM
    if ~isempty(find( P.endDCMblock == indVol - P.nrSkipVol,1 ))
        if (indNFTrial+1) > 1
            ROIsGlmAnat = evalin('base', 'ROIsGlmAnat');
        end
        if (indNFTrial+1) > 2
            ROIoptimGlmAnat = evalin('base', 'ROIoptimGlmAnat');
        end
        for iROI = 1:P.NrROIs
            ROIsAnat(iROI).mask2D(isnan(ROIsAnat(iROI).mask2D))=0;
            
            ROIsGlmAnat(iROI).mask2D(indNFTrial+1) = ...
                {statMap2D & ROIsAnat(iROI).mask2D};
            clear tmpVect
            tmpVect = find(cell2mat(ROIsGlmAnat(iROI).mask2D(indNFTrial+1))>0);
            if ~isempty(tmpVect) && length(tmpVect)>10
                ROIsGlmAnat(iROI).meanGlmAnatROI(indNFTrial+1) = ...
                    mean(statMap2D(tmpVect));
            else
                ROIsGlmAnat(iROI).meanGlmAnatROI(indNFTrial+1) = 0;
            end
            if (indNFTrial+1) > 1
                % for at least 2 ROIsGlmAnat, there is always one ROIoptimGlmAnat
                [val, nrROIoptimGlmAnat] = ...
                    max(ROIsGlmAnat(iROI).meanGlmAnatROI);
                ROIoptimGlmAnat(iROI).mask2D(indNFTrial+1) = ...
                    ROIsGlmAnat(iROI).mask2D(nrROIoptimGlmAnat);
                mainLoopData.nrROIoptimGlmAnat(iROI,indNFTrial) = ...
                    nrROIoptimGlmAnat;
                clear nrROIoptimGlmAnat val
            end
        end
        
        assignin('base', 'ROIsGlmAnat', ROIsGlmAnat);
        if (indNFTrial+1) > 1
            assignin('base', 'ROIoptimGlmAnat', ROIoptimGlmAnat);
        end
    end
    P.indNFTrial = indNFTrial;
end

assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);

end

