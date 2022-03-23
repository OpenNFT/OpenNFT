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

if P.UseTCPData, tcp = evalin('base', 'tcp'); end

if indVol <= P.nrSkipVol
    if P.UseTCPData && (indVol > 1), while ~tcp.BytesAvailable, pause(0.01); end; [~, ~] = tcp.ReceiveScan; end
    return;
end

flags = getFlagsType(P);

if P.isRTQA
    rtQA_matlab = evalin('base', 'rtQA_matlab');
end

if flags.isDCM
    ROIsAnat = evalin('base', 'ROIsAnat');
    if P.isRTQA
        wholeBrainROI = evalin('base','ROIs');
        ROIsAnat(P.NrROIs).voxelIndex = wholeBrainROI.voxelIndex;
        ROIsAnat(P.NrROIs).mat = wholeBrainROI.mat;
        ROIsAnat(P.NrROIs).dim = wholeBrainROI.dim;
        ROIsAnat(P.NrROIs).vol = wholeBrainROI.vol;
    end
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
            if ~P.isDicom2D
                % for strange 4D Siemens XA30 data format
                dcmData = squeeze(dcmData);
            else
                dcmData = img2Dvol3D(dcmData, slNrImg2DdimX, slNrImg2DdimY, dimVol);
            end
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
if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
    gKernel = [5 5 5] ./ dicomInfoVox;
end
if flags.isDCM
    gKernel = [5 5 5] ./ dicomInfoVox;
end
mainLoopData.gKernel = gKernel;

smReslVol = zeros(dimVol);
spm_smooth(reslVol, smReslVol, gKernel);

% statMap2D_pos = zeros(img2DdimY, img2DdimX);

% DVARS calulcation and new volume assign
if flags.isDCM && ~P.smForDCM
    % for DCM without smoothing
    if P.isRTQA
        ROIs = evalin('base','ROIs');            
        indROI = ROIs.voxelIndex;
        % on current iteration mainLoopData has previous volume
        dvarsDiff = ((reslVol(indROI) - mainLoopData.procVol(indROI)) ./ P.scaleFactorDVARS).^2;
        mainLoopData.dvarsValue = 100 * sqrt(mean(dvarsDiff(:)));
    end
    % after DVARS calculation previous volume re-assign with current
    mainLoopData.procVol = reslVol;
else
    % for PSC/SVM/Resting state/DCM with smoothing
    if P.isRTQA
        ROIs = evalin('base','ROIs');            
        indROI = ROIs(end).voxelIndex;
        dvarsDiff = ((smReslVol(indROI) - mainLoopData.procVol(indROI)) ./ P.scaleFactorDVARS).^2;
        mainLoopData.dvarsValue = 100 * sqrt(mean(dvarsDiff(:)));
    end
    mainLoopData.procVol = smReslVol;
end

% iGLM init
nrVoxInVol = mainLoopData.nrVoxInVol;
nrBasFct = P.nrBasFct;
numscan = mainLoopData.numscan;
spmMaskTh = mainLoopData.spmMaskTh;
basFct = mainLoopData.basFct;
nrBasFctRegr = P.nrBasFctRegr;

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
        Cn = mainLoopData.Cn;
        Dn = mainLoopData.Dn;
        s2n = mainLoopData.s2n;
        tn = mainLoopData.tn;
        tTh = mainLoopData.tTh;
        dyntTh = mainLoopData.dyntTh;
        
        statMapVect = mainLoopData.statMapVect;
        statMap3D_pos = mainLoopData.statMap3D_pos; % this structure is set with 0
        statMap3D_neg = mainLoopData.statMap3D_neg; % this structure is set with 0

        if ~fLockedTempl
            % assign Template
            mainLoopData.imgVolTempl = smReslVol;
            assignin('base', 'imgVolTempl', smReslVol)
            m = evalin('base', 'mmImgVolTempl');
            m.Data.imgVolTempl = smReslVol;
        end
        
    else
        %% Initialize variables
        % assign Template
        mainLoopData.imgVolTempl = smReslVol;
        assignin('base', 'imgVolTempl', smReslVol)
        m = evalin('base', 'mmImgVolTempl');
        m.Data.imgVolTempl = smReslVol;
        
        pVal = mainLoopData.pVal;
        tContr = mainLoopData.tContr;

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
    end
    
    if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
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
    if ~P.isAutoRTQA
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
            wholeBrainROI = evalin('base','ROIs');
            ROIs(P.NrROIs).voxelIndex = wholeBrainROI.voxelIndex;
            ROIs(P.NrROIs).mat = wholeBrainROI.mat;
            ROIs(P.NrROIs).dim = wholeBrainROI.dim;
            ROIs(P.NrROIs).vol = wholeBrainROI.vol;
        else
            ROIs = evalin('base', 'ROIs');
        end
        for i=1:P.NrROIs
            rtQA_matlab.ROI(i).Bn(indIglm,:) = mean(Bn(ROIs(i).voxelIndex,:));
            inds = intersect(ROIs(i).voxelIndex,find(tn.pos>0));
            if isempty(inds)
                rtQA_matlab.ROI(i).tn.pos(indIglm) = 0;
            else
                rtQA_matlab.ROI(i).tn.pos(indIglm) = geomean(tn.pos(inds));
            end
            inds = intersect(ROIs(i).voxelIndex,find(tn.neg>0));
            if isempty(inds)
                rtQA_matlab.ROI(i).tn.neg(indIglm) = 0;
            else
                rtQA_matlab.ROI(i).tn.neg(indIglm) = geomean(tn.neg(inds));
            end
            rtQA_matlab.ROI(i).var(indIglm) =  geomean(e2n(ROIs(i).voxelIndex,:));
        end
    end

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

    % shared for SPM matlab helper
    m = evalin('base', 'mmStatVol');
    m.Data.negStatVol = statMap3D_neg;

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
mainLoopData.iGLM_diff(indVol) = tStopIGLM-tStopSm;
mainLoopData.tStopMC(indVol) = tStopMC;
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
            
            ROIsAnat(iROI).vol(isnan(ROIsAnat(iROI).vol))=0;

            ROIsGlmAnat(iROI).vol(indNFTrial+1) = ...
                {statMap3D_pos & ROIsAnat(iROI).vol};

            clear tmpVect
            tmpVect = find(cell2mat(ROIsGlmAnat(iROI).vol(indNFTrial+1))>0);
            if ~isempty(tmpVect) && length(tmpVect)>10
                ROIsGlmAnat(iROI).meanGlmAnatROI(indNFTrial+1) = ...
                    mean(statMap3D_pos(tmpVect));
            else
                ROIsGlmAnat(iROI).meanGlmAnatROI(indNFTrial+1) = 0;
            end
            if (indNFTrial+1) > 1
                % for at least 2 ROIsGlmAnat, there is always one ROIoptimGlmAnat
                [val, nrROIoptimGlmAnat] = ...
                    max(ROIsGlmAnat(iROI).meanGlmAnatROI);
                ROIoptimGlmAnat(iROI).vol(indNFTrial+1) = ...
                    ROIsGlmAnat(iROI).vol(nrROIoptimGlmAnat);
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
