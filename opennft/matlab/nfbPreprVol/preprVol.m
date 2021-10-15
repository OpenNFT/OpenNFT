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
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');
imageViewMode = evalin('base', 'imageViewMode');
if P.isRTQA
    isShowRtqaVol = evalin('base', 'isShowRtqaVol');
    rtQAMode = evalin('base', 'rtQAMode');
    isSmoothed = evalin('base', 'isSmoothed');
    rtQA_matlab = evalin('base', 'rtQA_matlab');
    FIRST_SNR_VOLUME = evalin('base', 'FIRST_SNR_VOLUME');
else
    isShowRtqaVol = false;
end

if P.UseTCPData, tcp = evalin('base', 'tcp'); end

if indVol <= P.nrSkipVol
    if P.UseTCPData && (indVol > 1), while ~tcp.BytesAvailable, pause(0.01); end; [~, ~] = tcp.ReceiveScan; end
    return;
end

flags = getFlagsType(P);
if flags.isDCM
    ROIsAnat = evalin('base', 'ROIsAnat');
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

% type conversion Matlab-Python bug
indVolNorm = mainLoopData.indVolNorm;
indVolNorm = double(indVolNorm);

% trial indices for DCM feedback
if flags.isDCM
    % skip preprocessing for rest epoch and NF display
    if mainLoopData.flagEndDCM
        assignin('base', 'P', P);
        return;
    end
    indNFTrial = P.indNFTrial;
end

%% EPI Data Preprocessing
% Read Data in real-time and update parameters
switch P.DataType
    case 'DICOM'
        if P.UseTCPData && (indVol > 1)
            while ~tcp.BytesAvailable, pause(0.01); end
            [~, dcmData] = tcp.ReceiveScan;
        else
            dcmData = [];
            while isempty(dcmData) || contains(lastwarn,'Suspicious fragmentary file')
                dcmData = double(dicomread(inpFileName));
            end
            dcmData = img2Dvol3D(dcmData, slNrImg2DdimX, slNrImg2DdimY, dimVol);
        end
        R(2,1).mat = matVol;
        if P.isZeroPadding
            zeroPadVol = zeros(dimVol(1),dimVol(2),P.nrZeroPadVol);
            dimVol(3) = dimVol(3)+P.nrZeroPadVol*2;
            R(2,1).Vol = cat(3, cat(3, zeroPadVol, dcmData), zeroPadVol);
        else
            R(2,1).Vol = dcmData;
        end
        R(2,1).dim = dimVol;
    case 'IMAPH'
        % Note, possibly corrupted Phillips rt data export
        imgVol  = spm_read_vols(spm_vol(inpFileName));
        % If necessary, flip rt time-series so that it matches the template
        % set in setupFirstVolume.m, setupProcParams.m, selectROI.m
        imgVol  = fliplr(imgVol);

        R(2,1).mat = matTemplMotCorr;
        if P.isZeroPadding
            zeroPadVol = zeros(dimTemplMotCorr(1),dimTemplMotCorr(2),P.nrZeroPadVol);
            dimTemplMotCorr(3) = dimTemplMotCorr(3)+P.nrZeroPadVol*2;
            R(2,1).Vol = cat(3, cat(3, zeroPadVol, imgVol), zeroPadVol);
        else
            R(2,1).Vol = imgVol;
        end
        R(2,1).dim = dimTemplMotCorr;
        
    case 'NII'
        R(2,1).mat = matVol;
        tmpVol = spm_read_vols(spm_vol(inpFileName));
        if P.isZeroPadding
            zeroPadVol = zeros(dimVol(1),dimVol(2),P.nrZeroPadVol);
            dimVol(3) = dimVol(3)+P.nrZeroPadVol*2;
            R(2,1).Vol = cat(3, cat(3, zeroPadVol, tmpVol), zeroPadVol);
        else
            R(2,1).Vol = tmpVol;
        end
        R(2,1).dim = dimVol;
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
if P.isZeroPadding
    tmp_reslVol = spm_reslice_rt(R, flagsSpmReslice);
    reslVol = tmp_reslVol(:,:,P.nrZeroPadVol+1:end-P.nrZeroPadVol);
    dimVol(3) = dimVol(3) - P.nrZeroPadVol*2;
else
    reslVol = spm_reslice_rt(R, flagsSpmReslice);
end
tStopMC = toc(tStartMotCorr);

%% Smoothing
if flags.isPSC || flags.isSVM || flags.isCorr || P.isRestingState
    gKernel = [5 5 5] ./ dicomInfoVox;
end
if flags.isDCM
    gKernel = [5 5 5] ./ dicomInfoVox;
end
mainLoopData.gKernel = gKernel;

smReslVol = zeros(dimVol);
spm_smooth(reslVol, smReslVol, gKernel);

% statMap2D_pos = zeros(img2DdimY, img2DdimX);

% RTQA calculations of SNR and CNR
if P.isRTQA && indVolNorm > FIRST_SNR_VOLUME
    
    if flags.isDCM && ~isempty(find(P.beginDCMblock == indVol-P.nrSkipVol,1))
        rtQA_matlab.snrData.meanSmoothed = [];
        rtQA_matlab.cnrData.basData.mean = [];
        rtQA_matlab.cnrData.condData.mean = [];
    end
    
    [ rtQA_matlab.snrData ] = snr_calc(indVolNorm, reslVol, smReslVol, rtQA_matlab.snrData, isSmoothed);
    
    if ~P.isRestingState
        [ rtQA_matlab.cnrData ] = cnr_calc(indVolNorm, reslVol, smReslVol, rtQA_matlab.cnrData, isSmoothed);
    end
        
    rtQA_matlab.snrMapCreated = 1;

    % Transfer data for following visualization
    if isShowRtqaVol
        
        if ~rtQAMode || P.isRestingState
            % 0 - SNR mode, 2 - CNR mode
            outputVol = rtQA_matlab.snrData.snrVol;
        else
            outputVol = rtQA_matlab.cnrData.cnrVol;
        end
   
        if imageViewMode == 1 || imageViewMode == 2
            % orthviewAnat (1) || orthviewEPI (2)
            fname = strrep(P.memMapFile, 'shared', 'RTQAVol');
            m_out = evalin('base', 'mmrtQAVol');
            m_out.Data.rtQAVol = outputVol;

        else
            % mosaic (0)
            statMap2D_pos = vol3Dimg2D(outputVol, slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY, dimVol);
            statMap2D_pos = statMap2D_pos-min(statMap2D_pos(:));
            statMap2D_pos = (statMap2D_pos / max(statMap2D_pos(:))) * 255;
            m = evalin('base', 'mmStatMap');
            m.Data.statMap = uint8(statMap2D_pos);
            assignin('base', 'statMap', statMap2D_pos);
        
        end
        
        rtQA_matlab.snrMapCreated = 1;
           
    end
else
    
    rtQA_matlab.snrMapCreated = 0;
    
end
    

    
if flags.isPSC || flags.isSVM || flags.isCorr || P.isRestingState
    % Smoothed Vol 3D -> 2D
    smReslVol_2D = vol3Dimg2D(smReslVol, slNrImg2DdimX, slNrImg2DdimY, ...
        img2DdimX, img2DdimY, dimVol);
    mainLoopData.smReslVol_2D = smReslVol_2D;
end

if flags.isDCM
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

% iGLM init
nrVoxInVol = mainLoopData.nrVoxInVol;
nrBasFct = mainLoopData.nrBasFct;
numscan = mainLoopData.numscan;
spmMaskTh = mainLoopData.spmMaskTh;
basFct = mainLoopData.basFct;

%% AR(1) iGLM, i.e. after assigning _2D matrices used for ROI's extractions
if P.iglmAR1
    if indVolNorm == 1
        % initialize first AR(1) volume
        mainLoopData.smReslVolAR1_1 = (1 - P.aAR1) * smReslVol;
    else
        mainLoopData.smReslVolAR1_1 = smReslVol - ...
            P.aAR1 * mainLoopData.smReslVolAR1_1;
    end
    smReslVol = mainLoopData.smReslVolAR1_1;
end

tStopSm = toc(tStartMotCorr);
indIglm = 1;

%% iGLM
if flags.isDCM
    fIGLM_onset = isempty(find(P.beginDCMblock == indVol-P.nrSkipVol,1));
else
    fIGLM_onset =  true;
end

if flags.isIGLM
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
        statMap3D_pos = mainLoopData.statMap3D_pos; % this structure is set with 0
        statMap3D_neg = mainLoopData.statMap3D_neg; % this structure is set with 0
        tempStatMap2D = mainLoopData.statMap2D; % this structure is set with 0
        
        if ~fLockedTempl
            % assign Template
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
        % assign Template
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
            if ~P.isRestingState
                nrBasFctRegr = 1;
            else
                nrBasFctRegr = 6;
            end
        else
            nrHighPassRegr = size(mainLoopData.K.X0,2);
            if ~P.isRestingState
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
            else
                if P.isHighPass && P.isLinRegr
                    nrBasFctRegr = nrHighPassRegr+2;
                    % adding 6 head motion, linear, high-pass filter, and
                    % constant regressors
                elseif ~P.isHighPass && P.isLinRegr
                    nrBasFctRegr = 2;
                    % adding 6 head motion, linear, and constant regressors
                elseif P.isHighPass && ~P.isLinRegr
                    nrBasFctRegr = nrHighPassRegr+1;
                    % adding high-pass filter, and constant regressors
                end
            end
        end
        Cn = zeros(nrBasFct + nrBasFctRegr);
        Dn = zeros(nrVoxInVol, nrBasFct + nrBasFctRegr);
        s2n = zeros(nrVoxInVol, 1);
        tn.pos = zeros(nrVoxInVol, 1);
        tn.neg = zeros(nrVoxInVol, 1);
        tTh = zeros(numscan, 1);
        dyntTh = 0;
        mainLoopData.iGLMinit = 'done';
        
        statMapVect = zeros(nrVoxInVol, 1);
        statMap3D_pos = zeros(dimVol);
        statMap3D_neg = zeros(dimVol);
        mainLoopData.statMapVect = statMapVect;
        mainLoopData.statMap3D_pos = statMap3D_pos;
        mainLoopData.statMap3D_neg = statMap3D_neg;
        tempStatMap2D = zeros(img2DdimY,img2DdimX);
        mainLoopData.statMap2D = tempStatMap2D;
    end
    
    if flags.isPSC || flags.isSVM || flags.isCorr || P.isRestingState
        indIglm = indVolNorm;
    end
    if flags.isDCM
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
    if ~P.isRestingState
        % combine with prepared basFct design regressors
        basFctRegr = [basFct(1:indIglm,:), tmpRegr];
    else
        % combine with prepared basFct design regressors
        basFctRegr = [zscore(P.motCorrParam(1:indIglm,:)), tmpRegr];
    end
    % account for contrast term in contrast vector (+1)
    tContr.pos = [tContr.pos; zeros(nrBasFctRegr,1)];
    tContr.neg = [tContr.neg; zeros(nrBasFctRegr,1)];
    
    % estimate iGLM
    [idxActVoxIGLM, dyntTh, tTh, Cn, Dn, s2n, tn, neg_e2n, Bn, e2n] = ...
        iGlmVol( Cn, Dn, s2n, tn, smReslVol(:), indIglm, ...
        (nrBasFct+nrBasFctRegr), tContr, basFctRegr, pVal, ...
        dyntTh, tTh, spmMaskTh);
    
    % catch negative iGLM estimation error message for log
    mainLoopData.neg_e2n{indIglm} = neg_e2n;
    if ~isempty(neg_e2n)
        disp('HERE THE NEGATIVE e2n!!!')
    end
    
    if P.isRTQA
        if flags.isDCM
            ROIs = evalin('base', 'ROIsAnat');
        else
            ROIs = evalin('base', 'ROIs');
        end
        for i=1:P.NrROIs
            rtQA_matlab.Bn{i}(indIglm,:) = mean(Bn(ROIs(i).voxelIndex,:));
            inds = intersect(ROIs(i).voxelIndex,find(tn.pos>0));
            if isempty(inds)
                rtQA_matlab.tn.pos{i}(indIglm,:) = 0;
            else
                rtQA_matlab.tn.pos{i}(indIglm,:) = geomean(tn.pos(inds));
            end
            inds = intersect(ROIs(i).voxelIndex,find(tn.neg>0));
            if isempty(inds)
                rtQA_matlab.tn.neg{i}(indIglm,:) = 0;
            else
                rtQA_matlab.tn.neg{i}(indIglm,:) = geomean(tn.neg(inds));
            end
            rtQA_matlab.var{i}(indIglm,:) =  geomean(e2n(ROIs(i).voxelIndex,:));
        end
    end
    mainLoopData.nrBasFctRegr = nrBasFctRegr;
    mainLoopData.Cn = Cn;
    mainLoopData.Dn = Dn;
    mainLoopData.s2n = s2n;
    mainLoopData.tn = tn;
    mainLoopData.tTh = tTh;
    mainLoopData.dyntTh = dyntTh;
    mainLoopData.idxActVoxIGLM.pos{indVolNorm} = idxActVoxIGLM.pos;
    mainLoopData.idxActVoxIGLM.neg{indVolNorm} = idxActVoxIGLM.neg;
else
    idxActVoxIGLM.pos = [];
    idxActVoxIGLM.neg = [];
end

%% sharing iGLM results
mainLoopData.statMapCreated = 0;
if ~isempty(idxActVoxIGLM.pos) && max(tn.pos) > 0 % handle empty activation map
    % and division by 0
    maskedStatMapVect_pos = tn.pos(idxActVoxIGLM.pos);
    maxTval_pos = max(maskedStatMapVect_pos);
    statMapVect = maskedStatMapVect_pos;
    statMap3D_pos(idxActVoxIGLM.pos) = statMapVect;
        
    statMap2D_pos = vol3Dimg2D(statMap3D_pos, slNrImg2DdimX, slNrImg2DdimY, ...
        img2DdimX, img2DdimY, dimVol) / maxTval_pos;
    statMap2D_pos = statMap2D_pos * 255;
   
    if indVol == 26
       1 ;
    end
    
    if ~isShowRtqaVol && ~imageViewMode
        
        m_out =  evalin('base', 'mmStatMap');
        m_out.Data.statMap = uint8(statMap2D_pos);
        assignin('base', 'statMap', statMap2D_pos);
        
    end
    
    % shared for SPM matlab helper
    m = evalin('base', 'mmStatVol');
    m.Data.posStatVol = statMap3D_pos;
    mainLoopData.statMapCreated = 1;
end
if ~isempty(idxActVoxIGLM.neg) && max(tn.neg) > 0
        
    maskedStatMapVect_neg = tn.neg(idxActVoxIGLM.neg);
    maxTval_neg = max(maskedStatMapVect_neg);
    statMapVect = maskedStatMapVect_neg;
    statMap3D_neg(idxActVoxIGLM.neg) = statMapVect;
    
    clear idxActVoxIGLM
     
    statMap2D_neg = vol3Dimg2D(statMap3D_neg, slNrImg2DdimX, slNrImg2DdimY, ...
        img2DdimX, img2DdimY, dimVol) / maxTval_neg;
    statMap2D_neg = statMap2D_neg * 255;
    
    if ~isShowRtqaVol && ~imageViewMode
        
        m_out =  evalin('base', 'mmStatMap_neg');
        m_out.Data.statMap_neg = uint8(statMap2D_neg);
        assignin('base', 'statMap_neg', statMap2D_neg);
        
    end
    
    % shared for SPM matlab helper
    m = evalin('base', 'mmStatVol');
    m.Data.negStatVol = statMap3D_neg;
%     mainLoopData.statMapCreated = 1;

end

%% storage of iGLM results, could be disabled to save time
if ~flags.isDCM
    if indIglm == P.NrOfVolumes - P.nrSkipVol
        mainLoopData.statMap3D_iGLM = statMap3D_pos;
    end
else
    if indIglm == P.lengthDCMTrial
        mainLoopData.statMap3D_iGLM(:,:,:,mainLoopData.NrDCMblocks+1) = ...
            statMap3D_pos;
        % save, optional
        statVolData = statMap3D_pos;
        % FIXME
        save([P.nfbDataFolder filesep 'statVolData_' sprintf('%02d', ...
            mainLoopData.NrDCMblocks+1) '.mat'],'statVolData');
    end
end

tStopIGLM = toc(tStartMotCorr);
fprintf('TIMING: %d iter - PREPROC MC: %d s - SMOOTH: %d s - IGLM: %d s\n',...
    nrIter, tStopMC, tStopSm-tStopMC, tStopIGLM-tStopSm);

%% dynamic ROI mask based on statMap2D
if flags.isDCM
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
                {statMap2D_pos & ROIsAnat(iROI).mask2D};
            clear tmpVect
            tmpVect = find(cell2mat(ROIsGlmAnat(iROI).mask2D(indNFTrial+1))>0);
            if ~isempty(tmpVect) && length(tmpVect)>10
                ROIsGlmAnat(iROI).meanGlmAnatROI(indNFTrial+1) = ...
                    mean(statMap2D_pos(tmpVect));
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

assignin('base', 'rtQA_matlab', rtQA_matlab);
assignin('base', 'mainLoopData', mainLoopData);
assignin('base', 'P', P);

end

