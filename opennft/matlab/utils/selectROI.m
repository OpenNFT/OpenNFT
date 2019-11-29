function selectROI(pathName)
% Function to select ROIs given the specified ROI folder and assigns
% ROI information structures.
% Note, Phillips data could be corrupted, e.g. without hearder info, 
% flipped, etc. 
% End user is adviced to check ROIs, EPI template and rt time-series for 
% spatial orientation.
%
% input:
% pathName - ROI directory
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');

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

P.DynROI = false;

%% ROIs in a single folder
if isPSC || P.isRestingState
    roiDir = pathName;
    roiNames = {};
    roiNames = cellstr([spm_select('FPList', roiDir, '^.*.img$'); ...
                        spm_select('FPList', roiDir, '^.*.nii$')]);

    P.NrROIs = length(roiNames);
    P.ROINames = roiNames;
 
    for iFile = 1:P.NrROIs
        [ROIs(iFile).voxelCoord, ROIs(iFile).voxelIntens, ...
         ROIs(iFile).voxelIndex, ROIs(iFile).mat, ...
         ROIs(iFile).dim, ROIs(iFile).vol] = readVol(roiNames{iFile});   
        [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
                                             getMosaicDim(ROIs(iFile).dim);      
        ROIs(iFile).vol(ROIs(iFile).vol < 0.5) = 0;
        ROIs(iFile).vol(ROIs(iFile).vol >= 0.5) = 1;
        ROIs(iFile).mask2D = vol3Dimg2D(ROIs(iFile).vol, slNrImg2DdimX, ...
                     slNrImg2DdimY, img2DdimX, img2DdimY, ROIs(iFile).dim);
    end
    
    assignin('base', 'ROIs', ROIs);    
end

%% ROIs in single folder
if isSVM
    
    %% ROIs
    roiDir = pathName;
    roiNames = {};
    roiNames = cellstr([spm_select('FPList', roiDir, '^.*.img$'); ...
                        spm_select('FPList', roiDir, '^.*.nii$')]);

    P.NrROIs = length(roiNames);
    P.ROINames = roiNames;
    
    for iFile = 1:P.NrROIs
        [ROIs(iFile).voxelCoord, ROIs(iFile).voxelIntens, ...
         ROIs(iFile).voxelIndex, ROIs(iFile).mat, ...
         ROIs(iFile).dim, ROIs(iFile).vol] = readVol(roiNames{iFile});
        [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
                                             getMosaicDim(ROIs(iFile).dim);   
        ROIs(iFile).vol(ROIs(iFile).vol < 0.5) = 0;
        ROIs(iFile).vol(ROIs(iFile).vol >= 0.5) = 1;
        ROIs(iFile).mask2D = vol3Dimg2D(ROIs(iFile).vol, slNrImg2DdimX, ...
                     slNrImg2DdimY, img2DdimX, img2DdimY, ROIs(iFile).dim);
    end
   
    %% Weights   
    weightDir = P.WeightsFileName;
    weightNames = {};
    weightNames = cellstr([spm_select('FPList', weightDir, '^.*.img$'); ...
                           spm_select('FPList', weightDir, '^.*.nii$')]);

    P.NrWEIGHTs = length(weightNames);
    for iFile = 1:P.NrWEIGHTs
        [WEIGHTs(iFile).voxelCoord, WEIGHTs(iFile).voxelIntens, ...
         WEIGHTs(iFile).voxelIndex, WEIGHTs(iFile).mat, ...
         WEIGHTs(iFile).dim, WEIGHTs(iFile).vol] = ...
                                               readVol(weightNames{iFile});
        [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
                                          getMosaicDim(WEIGHTs(iFile).dim);         
        WEIGHTs(iFile).mask2D = vol3Dimg2D(WEIGHTs(iFile).vol, ...
                                  slNrImg2DdimX, slNrImg2DdimY, img2DdimX, ...
                                    img2DdimY, WEIGHTs(iFile).dim);
    end
    
    assignin('base', 'ROIs', ROIs); 
    assignin('base', 'WEIGHTs', WEIGHTs);            
end


%% Anatomy & group ROIs
if isDCM
    %% Anat
    roiDirAnat = pathName{1};
    roiNamesAnat = {};
    roiNamesAnat = cellstr([spm_select('FPList', roiDirAnat, '^.*.img$');...
                            spm_select('FPList', roiDirAnat, '^.*.nii$')]);

    P.NrROIs = length(roiNamesAnat);
    
    % 1 = AMY_L, 2 = AMY_R, 3 = PFC
    for iFile = 1:P.NrROIs
        [ROIsAnat(iFile).voxelCoord, ROIsAnat(iFile).voxelIntens, ...
         ROIsAnat(iFile).voxelIndex, ROIsAnat(iFile).mat, ...
         ROIsAnat(iFile).dim, ROIsAnat(iFile).vol] = ...
                                              readVol(roiNamesAnat{iFile});
        [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
                                         getMosaicDim(ROIsAnat(iFile).dim);          
        ROIsAnat(iFile).vol(ROIsAnat(iFile).vol < 0.5) = 0;
        ROIsAnat(iFile).vol(ROIsAnat(iFile).vol >= 0.5) = 1;
        ROIsAnat(iFile).mask2D = vol3Dimg2D(ROIsAnat(iFile).vol, ...
                                   slNrImg2DdimX, slNrImg2DdimY, img2DdimX, ...
                                     img2DdimY, ROIsAnat(iFile).dim);
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
        [ROIsGroup(iFile).voxelCoord, ROIsGroup(iFile).voxelIntens, ...
         ROIsGroup(iFile).voxelIndex, ROIsGroup(iFile).mat, ...
         ROIsGroup(iFile).dim, ROIsGroup(iFile).vol] = ...
                                             readVol(roiNamesGroup{iFile});
        [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = ...
                                        getMosaicDim(ROIsGroup(iFile).dim);           
        ROIsGroup(iFile).vol(ROIsGroup(iFile).vol < 0.5) = 0;
        ROIsGroup(iFile).vol(ROIsGroup(iFile).vol >= 0.5) = 1;
        ROIsGroup(iFile).mask2D = vol3Dimg2D(ROIsGroup(iFile).vol, ...
                                   slNrImg2DdimX, slNrImg2DdimY, img2DdimX, ...
                                     img2DdimY, ROIsGroup(iFile).dim);

    end
    assignin('base', 'ROIsGroup', ROIsGroup);
    assignin('base', 'ROIsAnat', ROIsAnat);
    assignin('base', 'ROIsGlmAnat', []);
    assignin('base', 'ROIoptimGlmAnat', []);
end

assignin('base', 'P', P);

