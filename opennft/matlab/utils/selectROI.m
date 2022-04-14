function selectROI(pathName)
% Function to select ROIs given the specified ROI folder and assigns
% ROI information structures.
% Note, Phillips data could be corrupted, e.g. without hearder info,
% flipped, etc.
% End user is advised to check ROIs, EPI template and rt time-series for
% spatial orientation.
%
% input:
% pathName - ROI directory
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');

flags = getFlagsType(P);

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

P.DynROI = false;

%% ROIs in a single folder
if flags.isPSC || flags.isSVM || flags.isCorr || P.isAutoRTQA
    roiDir = pathName;
    roiNames = {};
    roiNames = cellstr([spm_select('FPList', roiDir, '^.*.img$'); ...
                        spm_select('FPList', roiDir, '^.*.nii$')]);

    P.NrROIs = length(roiNames);
    P.ROINames = roiNames;

    for iFile = 1:P.NrROIs
        [ROIs(iFile).mat, ROIs(iFile).dim, ROIs(iFile).vol] = ...
            readVol(roiNames{iFile});
        ROIs(iFile).vol(ROIs(iFile).vol < 0.5) = 0;
        ROIs(iFile).vol(ROIs(iFile).vol >= 0.5) = 1;
        ROIs(iFile).voxelIndex = find(ROIs(iFile).vol);
    end

    assignin('base', 'ROIs', ROIs);
end

if flags.isSVM
    %% Weights
    weightDir = P.WeightsFileName;
    weightNames = {};
    weightNames = cellstr([spm_select('FPList', weightDir, '^.*.img$'); ...
                           spm_select('FPList', weightDir, '^.*.nii$')]);

    P.NrWEIGHTs = length(weightNames);
    for iFile = 1:P.NrWEIGHTs
        [WEIGHTs(iFile).mat, WEIGHTs(iFile).dim, WEIGHTs(iFile).vol] = ...
            readVol(weightNames{iFile});
    end

    assignin('base', 'WEIGHTs', WEIGHTs);
end


%% Anatomy & group ROIs
if flags.isDCM
    %% Anat
    roiDirAnat = pathName{1};
    roiNamesAnat = {};
    roiNamesAnat = cellstr([spm_select('FPList', roiDirAnat, '^.*.img$');...
                            spm_select('FPList', roiDirAnat, '^.*.nii$')]);

    P.NrROIs = length(roiNamesAnat);
    
    % 1 = AMY_L, 2 = AMY_R, 3 = PFC
    for iFile = 1:P.NrROIs
        [ROIsAnat(iFile).mat, ROIsAnat(iFile).dim, ROIsAnat(iFile).vol] = ...
            readVol(roiNamesAnat{iFile});
        ROIsAnat(iFile).vol(ROIsAnat(iFile).vol < 0.5) = 0;
        ROIsAnat(iFile).vol(ROIsAnat(iFile).vol >= 0.5) = 1;
        ROIsAnat(iFile).voxelIndex = find(ROIsAnat(iFile).vol);
    end

    %% Group
    roiDirGroup = pathName{2};
    roiNamesGroup = {};
    roiNamesGroup = cellstr([spm_select('FPList',roiDirGroup,'^.*.img$'); ...
                             spm_select('FPList',roiDirGroup,'^.*.nii$')]);

    P.NrROIs = length(roiNamesGroup);
    
    P.ROINames = roiNamesGroup;
    P.DynROI = true;
    
    % 1 = AMY_L, 2 = AMY_R, 3 = PFC
    for iFile = 1:P.NrROIs
        [ROIsGroup(iFile).mat, ROIsGroup(iFile).dim, ROIsGroup(iFile).vol] = ...
            readVol(roiNamesGroup{iFile});
        ROIsGroup(iFile).vol(ROIsGroup(iFile).vol < 0.5) = 0;
        ROIsGroup(iFile).vol(ROIsGroup(iFile).vol >= 0.5) = 1;
        ROIsGroup(iFile).voxelIndex = find(ROIsGroup(iFile).vol);
    end

    assignin('base', 'ROIsGroup', ROIsGroup);
    assignin('base', 'ROIsAnat', ROIsAnat);
    assignin('base', 'ROIsGlmAnat', []);
    assignin('base', 'ROIoptimGlmAnat', []);
end

% For rtQA, nrROIs includes whole-brain EPI ROI initialized in epiWholeBrainROI.m
if P.isRTQA
    P.NrROIs = P.NrROIs + 1;
end

assignin('base', 'P', P);
