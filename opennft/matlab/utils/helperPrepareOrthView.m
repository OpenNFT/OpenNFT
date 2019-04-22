function helperPrepareOrthView(P, bgType)
% Function to prepare orthogonal viewer.
%
% input:
% P - parameter structure
% bgType - time of the overlay background as defined by GUI view mode
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Adopted by Yury Koush based on SPM (see spm_orthviews.m)

P.bgType = bgType;

%% Background: EPI template or Anatomy
%% default values
fAnatomyBacgkr = false;
fEpiBackgr = true;

if strcmp(bgType, 'bgMosaic')
	fAnatomyBacgkr = false;
    fEpiBackgr = true;
end;
if strcmp(bgType, 'bgEPI')
    fAnatomyBacgkr = false;
	fEpiBackgr = true;
end;
if strcmp(bgType, 'bgAnat')
    fAnatomyBacgkr = true;
	fEpiBackgr = false;
end;

dirAnatBackgr = P.AnatBgFolder;
dirEpiBackgr = P.MCTempl;

[isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P);

%% Background
if fAnatomyBacgkr
    displBackgrDir = dirAnatBackgr;
elseif fEpiBackgr
    displBackgrDir = dirEpiBackgr;
end

displBackgrDir = dirEpiBackgr;

displBackgrName = {};
%displBackgrDir = strrep(displBackgrDir, '/', '\');
displBackgrName = cellstr([spm_select('FPList',displBackgrDir,'^.*.img$'); ...
    spm_select('FPList',displBackgrDir,'^.*.nii$')]);

[displBackgr.voxelCoord, displBackgr.voxelIntens, displBackgr.voxelIndex, ...
    displBackgr.mat, displBackgr.dim, displBackgr.vol] = ...
                                               readVol(displBackgrName{1});

displayBgEpi= displBackgr;

displBackgrDir = dirAnatBackgr;

displBackgrName = {};
%displBackgrDir = strrep(displBackgrDir, '/', '\');
displBackgrName = cellstr([spm_select('FPList',displBackgrDir,'^.*.img$'); ...
    spm_select('FPList',displBackgrDir,'^.*.nii$')]);

[displBackgr.voxelCoord, displBackgr.voxelIntens, displBackgr.voxelIndex, ...
    displBackgr.mat, displBackgr.dim, displBackgr.vol] = ...
                                               readVol(displBackgrName{1});

displayBgAnat = displBackgr;

%% ROIs
if isDCM
    ROIsAnat = evalin('base', 'ROIsAnat');
    ROIsOverlay = ROIsAnat;
end
if isPSC || isSVM
    ROIs = evalin('base', 'ROIs');
    ROIsOverlay = ROIs;
end

%% set structure for Display and draw a first overlay
global strParam
strParam = struct('n', 0, 'bb',[],'Space',eye(4),'centre',[0 0 0],'mode',1,...
    'area',[0 0 1 1],'premul',eye(4),'hld',1,'modeDispl',[0, 0, 0]);
strParam.Space = spm_matrix([0 0 0  0 pi -pi/2])*strParam.Space;    

%% get bounding box and resolution
if isempty(strParam.bb), 
     strParam.maxBB = maxbb(displBackgrName{1}); 
     strParam.bb = strParam.maxBB;    
end
resolution(displBackgr.mat);

%% Draw at initial location, center of bounding box
mmcentre     = mean(strParam.Space*[strParam.maxBB';1 1],2)';
strParam.centre    = mmcentre(1:3);
% Display modes: [Background+Stat+ROIs, Background+Stat, Background+ROIs]
strParam.modeDispl = [0 0 1]; 
displStat = [];
if isDCM
    [imgt,imgs,imgc] = redrawall(displBackgr.vol, displBackgr.mat, ...
                         ROIsAnat, displStat); % ?imgs/imgc names under spm
else
    [imgt,imgs,imgc] = redrawall(displBackgr.vol,displBackgr.mat, ...
                             ROIs, displStat); % ?imgs/imgc names under spm
end
disp('prepareOrthView() in helper matlab');

format = {'uint8', size(imgt), 'imgt';...
'uint8', size(imgs), 'imgs';...
'uint8', size(imgc), 'imgc'};

imgt = uint8(imgt / max(max(max(imgt))) * 255);
imgs = uint8(double(imgs) / max(max(max(imgs))) * 255);
imgc = uint8(double(imgc) / max(max(max(imgc))) * 255);
data = [imgt(:); imgs(:); imgc(:)];
assignin('base', 'imgt', imgt);
assignin('base', 'imgs', imgs);
assignin('base', 'imgc', imgc);   

assignin('base', 'displBackgr', displBackgr);   
assignin('base', 'displayBgAnat', displayBgAnat);   
assignin('base', 'displayBgEpi', displayBgEpi);   

assignin('base', 'ROIsOverlay', ROIsOverlay);   

%% images for OrthView in GUI from helper matlab
initMemmap(P.memMapFile, 'OrthView', data, 'uint8', 'mmOrthView', format);

% figure('Name', 'Bounding box center')
% subplot(2,2,1),imshow(imgs,[]),title('Saggital') % 256x256
% subplot(2,2,3),imshow(imgt,[]),title('Transversal') % 192x256
% subplot(2,2,2),imshow(imgc,[]),title('Coronal') % 256x192

assignin('base', 'helperP', P);

%% ********************************************************************* %%

%% functions for redrawall()

function [drawimgt,drawimgc,drawimgs] = redrawall(Vol,mat,ROIs,Stat)
global strParam

%% Calculate Background
bb   = strParam.bb;
Dims = round(diff(bb)'+1);
is   = inv(strParam.Space);
cent = is(1:3,1:3)*strParam.centre(:) + is(1:3,4);

M = strParam.Space\strParam.premul*mat;
TM0 = [ 1 0 0 -bb(1,1)+1
        0 1 0 -bb(1,2)+1
        0 0 1  -cent(3)
        0 0 0     1     ];
TM = inv(TM0 * M);
TD = Dims([1 2]);

CM0 = [ 1 0 0 -bb(1,1)+1
        0 0 1 -bb(1,3)+1
        0 1 0   -cent(2)
        0 0 0      1    ];
CM = inv(CM0 * M);
CD = Dims([1 3]);

if strParam.mode == 0
    SM0 = [ 0 0 1 -bb(1,3)+1
            0 1 0 -bb(1,2)+1
            1 0 0   -cent(1)
            0 0 0      1    ];
    SM = inv(SM0 * M);
    SD = Dims([3 2]);
else
    SM0 = [ 0 -1 0 +bb(2,2)+1
            0  0 1 -bb(1,3)+1
            1  0 0  -cent(1)
            0  0 0     1     ];
    SM = inv(SM0 * M);
    SD = Dims([2 3]);
end;

try
    imgt  = spm_slice_vol(Vol, TM, TD, strParam.hld)';
    imgc  = spm_slice_vol(Vol, CM, CD, strParam.hld)';
    imgs  = fliplr(spm_slice_vol(Vol, SM, SD, strParam.hld)');
    ok    = true;
catch
    'Image can not be resampled\n';
    ok     = false;
end
if ok
    % get min/max threshold
    mn = -Inf;
    mx = Inf;
    % threshold images
    imgt = max(imgt,mn); imgt = min(imgt,mx);
    imgc = max(imgc,mn); imgc = min(imgc,mx);
    imgs = max(imgs,mn); imgs = min(imgs,mx);
    
    % recompute min/max for display
    mx = -inf; mn = inf;

    if ~isempty(imgt)
        tmp = imgt(isfinite(imgt));
        mx = max([mx max(max(tmp))]);
        mn = min([mn min(min(tmp))]);
    end;
    if ~isempty(imgc)
        tmp = imgc(isfinite(imgc));
        mx = max([mx max(max(tmp))]);
        mn = min([mn min(min(tmp))]);
    end;
    if ~isempty(imgs)
        tmp = imgs(isfinite(imgs));
        mx = max([mx max(max(tmp))]);
        mn = min([mn min(min(tmp))]);
    end;
    if mx == mn, mx = mn + eps; end;
else
    imgt = [];
    imgc = [];
    imgs = [];
end

% Template parameters, used for ROIs and Stat map
coordParam.TM0 = TM0; coordParam.CM0 = CM0; coordParam.SM0 = SM0; 
coordParam.TD  = TD;  coordParam.CD  = CD;  coordParam.SD  = SD;
coordParam.mx  = mx;  coordParam.mn  = mn;  coordParam.eps = eps;

if ~isempty(Stat)
    % Calculate Stat
    [imgt, imgc, imgs, tmpt, tmpc, tmps, actc, actp, gryc] = ...
             getOrthStat(imgt, imgc, imgs, coordParam, Stat.vol, Stat.mat);
    % Calculate ROIs    
    [drawRoiImgt, drawRoiImgc, drawRoiImgs, cimgt, cimgc, cimgs] = ...
                           getOrthROIs(imgt, imgc, imgs, ROIs, coordParam);    
else
    gryc = (0:63)' * ones(1,3) /63;
    % Calculate ROIs      
    [drawRoiImgt, drawRoiImgc, drawRoiImgs, cimgt, cimgc, cimgs] = ...
                           getOrthROIs(imgt, imgc, imgs, ROIs, coordParam);
end

%% Draw
if ~isempty(Stat)
    if strParam.modeDispl(1)
        %% Background + Stat + ROIs
        % combine gray and blob data to truecolour
        % imgt(gray) + tmpt(actc*actp) + cimgt(binary_blob)
        drawimgt = reshape(actc(tmpt(:),:)*actp+gryc(imgt(:),:)*(1-actp), ...
                                                   [size(imgt) 3]) + cimgt;
        drawimgc = reshape(actc(tmpc(:),:)*actp+gryc(imgc(:),:)*(1-actp), ...
                                                   [size(imgc) 3]) + cimgc;
        drawimgs = reshape(actc(tmps(:),:)*actp+gryc(imgs(:),:)*(1-actp), ...
                                                   [size(imgs) 3]) + cimgs;
    end
    if strParam.modeDispl(2)
        %% Background + Stat
        % combine gray and blob data to truecolour
        % imgt(gray) + tmpt(actc*actp) + cimgt(binary_blob)    
        drawimgt = reshape(actc(tmpt(:),:)*actp+gryc(imgt(:),:)*(1-actp), ...
                                                           [size(imgt) 3]);
        drawimgc = reshape(actc(tmpc(:),:)*actp+gryc(imgc(:),:)*(1-actp), ...
                                                           [size(imgc) 3]);
        drawimgs = reshape(actc(tmps(:),:)*actp+gryc(imgs(:),:)*(1-actp), ...
                                                           [size(imgs) 3]);
    end
else
    if strParam.modeDispl(1) || strParam.modeDispl(2)
        %% Background
        drawimgt = cimgt;
        drawimgc = cimgc;
        drawimgs = cimgs;
    end
end
if strParam.modeDispl(3)
    %% Background + ROIs   
    drawimgt = drawRoiImgt;
    drawimgc = drawRoiImgc;
    drawimgs = drawRoiImgs;
end
return;

function [imgt, imgc, imgs, tmpt, tmpc, tmps, actc, actp, gryc] = ...
                getOrthStat(imgt, imgc, imgs, coordParam, StatVol, StatMat)
global strParam
% Add blobs for display using a defined colourmap
cmapStat = jet(64);
intensityToGrayImage = 0.4;

mx = coordParam.mx;
mn = coordParam.mn;
eps = coordParam.eps;

% colourmaps
gryc = (0:63)' * ones(1,3) /63;
actc = cmapStat;
actp = intensityToGrayImage;

% scale grayscale image, not isfinite -> black
imgt = scaletocmap(imgt, mn, mx, gryc, 65);
imgc = scaletocmap(imgc, mn, mx, gryc, 65);
imgs = scaletocmap(imgs, mn, mx, gryc, 65);
gryc = [gryc; 0 0 0];

% get max for blob image
cmx = max([eps maxval(StatVol)]);
cmn = -cmx;

% get blob data
M    = strParam.Space\strParam.premul*StatMat;
tmpt = spm_slice_vol(StatVol,inv(coordParam.TM0*M),coordParam.TD,[0 NaN])';
tmpc = spm_slice_vol(StatVol,inv(coordParam.CM0*M),coordParam.CD,[0 NaN])';
tmps = fliplr(spm_slice_vol(StatVol,inv(coordParam.SM0*M),coordParam.SD, ...
                                                                [0 NaN])');

% actimg scaled round 0, black NaNs
topc = size(actc,1)+1;
tmpt = scaletocmap(tmpt, cmn, cmx, actc, topc);
tmpc = scaletocmap(tmpc, cmn, cmx, actc, topc);
tmps = scaletocmap(tmps, cmn, cmx, actc, topc);
actc = [actc; 0 0 0];
return

function [drawimgt, drawimgc, drawimgs, cimgt, cimgc, cimgs] = ...
                            getOrthROIs(imgt, imgc, imgs, ROIs, coordParam)
global strParam
% 6 colors, extend if >6  ROIs
colour=[0 1 0;0 1 1;0 0 1;1 0 1;1 0 0;1 1 0];%pink(3); %flipud(pink(3));
mx = coordParam.mx;
mn = coordParam.mn;
eps = coordParam.eps;
scal  = 1 / (mx - mn);
dcoff = -mn * scal;

wt = zeros(size(imgt));
wc = zeros(size(imgc));
ws = zeros(size(imgs));

imgt  = repmat(imgt * scal + dcoff,[1,1,3]);
imgc  = repmat(imgc * scal + dcoff,[1,1,3]);
imgs  = repmat(imgs * scal + dcoff,[1,1,3]);

cimgt = zeros(size(imgt));
cimgc = zeros(size(imgc));
cimgs = zeros(size(imgs));

for j=1:length(ROIs)
    mx = max([eps max(ROIs(j).vol(:))]);
    ROIs(j).max = mx;    
    mn = min([0 min(ROIs(j).vol(:))]);
    ROIs(j).min = mn;
       
    vol  = ROIs(j).vol;
    M    = strParam.Space \ strParam.premul * ROIs(j).mat;
    tmpt = spm_slice_vol(vol,inv(coordParam.TM0*M),coordParam.TD,[0 NaN])';
    tmpc = spm_slice_vol(vol,inv(coordParam.CM0*M),coordParam.CD,[0 NaN])';
    tmps = fliplr(spm_slice_vol(vol,inv(coordParam.SM0*M),coordParam.SD,...
                                                                [0 NaN])');
    % check min/max of sampled image
    % against mn/mx as given in st
    tmpt(tmpt(:) < mn) = mn;
    tmpc(tmpc(:) < mn) = mn;
    tmps(tmps(:) < mn) = mn;
    tmpt(tmpt(:) > mx) = mx;
    tmpc(tmpc(:) > mx) = mx;
    tmps(tmps(:) > mx) = mx;
    tmpt = (tmpt - mn) / (mx - mn);
    tmpc = (tmpc - mn) / (mx - mn);
    tmps = (tmps - mn) / (mx - mn);
    tmpt(~isfinite(tmpt)) = 0;
    tmpc(~isfinite(tmpc)) = 0;
    tmps(~isfinite(tmps)) = 0;
    % get roi contour
    tmpt = double(bwperim(tmpt,4));
    tmpc = double(bwperim(tmpc,4));
    tmps = double(bwperim(tmps,4));
    % making 3 x dim(1,2) mask for blob color display
    cimgt = cimgt + cat(3, tmpt * colour(j,1), ...
                           tmpt * colour(j,2), ...
                           tmpt * colour(j,3));
    cimgc = cimgc + cat(3, tmpc * colour(j,1), ...
                           tmpc * colour(j,2), ...
                           tmpc * colour(j,3));
    cimgs = cimgs + cat(3, tmps * colour(j,1), ...
                           tmps * colour(j,2), ...
                           tmps * colour(j,3));
    
    wt = wt + tmpt;
    wc = wc + tmpc;
    ws = ws + tmps;
    %cdata=permute(shiftdim((1/64:1/64:1)'* ...
    %    colour(j,:),-1),[2 1 3]);
    %redraw_colourbar(i,j,[mn mx],cdata);
end;

drawimgt = repmat(1-wt,[1 1 3]).*imgt+cimgt;
drawimgc = repmat(1-wc,[1 1 3]).*imgc+cimgc;
drawimgs = repmat(1-ws,[1 1 3]).*imgs+cimgs;

imgt(imgt < 0) = 0; imgt(imgt > 1) = 1;
imgc(imgc < 0) = 0; imgc(imgc > 1) = 1;
imgs(imgs < 0) = 0; imgs(imgs > 1) = 1;

return;

function mx = maxval(vol)
if isstruct(vol)
    mx = -Inf;
    for i=1:vol.dim(3)
        tmp = spm_slice_vol(vol, spm_matrix([0 0 i]), vol.dim(1:2), 0);
        imx = max(tmp(isfinite(tmp)));
        if ~isempty(imx),mx = max(mx,imx);end
    end;
else
    mx = max(vol(isfinite(vol)));
end;

function img = scaletocmap(inpimg, mn, mx, cmap, miscol)
if nargin < 5, miscol=1;end
cml = size(cmap,1);
scf = (cml - 1) / (mx - mn);
img = round((inpimg - mn) * scf)+1;
img(img < 1)   = 1;
img(img > cml) = cml;
img(~isfinite(img))  = miscol;
return;

function bb = maxbb(fileName)
global strParam
mn = [Inf Inf Inf];
mx = -mn;
premul = strParam.Space \ strParam.premul;
bb = spm_get_bbox(fileName, 'fv', premul);
mx = max([bb ; mx]);
mn = min([bb ; mn]);
bb = [mn ; mx];
return;

function resolution(mat)
global strParam
resDefault = 1; % Default minimum resolution 1mm
res = min([resDefault,sqrt(sum((mat(1:3,1:3)).^2))]);
res      = res / mean(svd(strParam.Space(1:3,1:3)));
Mat      = diag([res res res 1]);
strParam.Space = strParam.Space * Mat;
strParam.bb    = strParam.bb / res;
return;

