function helperUpdateOrthView(cursorPos, flagsPlanes, bgType, isShowRTQA)
% Function to update orthogonal viewer.
%
% input:
% cursorPos   - cursor position as of the mouse click
% flagsPlanes - current projection/orthogonal plane index
% bgType      - time of the overlay background as defined by GUI view mode
%
% output:
% Output is assigned to workspace variables.
%
% Note,
% newCoord = [60,50; 0,0; 0,0];  % new coordinates on [T; S; C] planes
% flagsPlanes = [1 0 0]; % click was on [transverse, sagital, coron]
%
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Adopted by Yury Koush based on SPM (see spm_orthviews.m)

global strParam;

flagsPlanes = cell2mat(flagsPlanes);
cursorPos = cell2mat(cursorPos);

proj = find(flagsPlanes);

newCoord = [0, 0; 0, 0; 0, 0];
newCoord(proj, :) = cursorPos;

%disp('New cursor coordinates:')
%disp(newCoord)

P = evalin('base', 'helperP');
ROIsOverlay = evalin('base', 'ROIsOverlay');
dimTemplMotCorr = evalin('base', 'dimTemplMotCorr');
matTemplMotCorr = evalin('base', 'matTemplMotCorr');
displBackgr = evalin('base', 'displBackgr');

displayBgAnat = evalin('base', 'displayBgAnat');   
displayBgEpi = evalin('base', 'displayBgEpi');   

if strcmpi(bgType, 'bgEPI')
    displBackgr = displayBgEpi;
else
    displBackgr = displayBgAnat;
end

strParam.centre = findcent(newCoord, flagsPlanes);
% TODO GUI: Display modes: [Background + Stat + ROIs, 
%                                     Background + Stat, Background + ROIs]
strParam.modeDispl = [1 0 0]; 
displImg_neg = [];

if isShowRTQA
   fname = strrep(P.memMapFile, 'shared', 'RTQAVol');
   snr = memmapfile(fname, 'Writable', false, 'Format',  {'double', prod(displayBgEpi.dim), 'rtQAVol'});
   rtqaVolTRaw = reshape(snr.Data.rtQAVol,displayBgEpi.dim);
   displImg.vol = rtqaVolTRaw;
   displImg.mat = matTemplMotCorr;
else
   fname = strrep(P.memMapFile, 'shared', 'statVol');
   m_in = memmapfile(fname, 'Writable', false, 'Format',  {'double', displayBgEpi.dim, 'posStatVol'; 'double', displayBgEpi.dim, 'negStatVol'});
   displImg.vol = m_in.Data.posStatVol;
   displImg.mat = matTemplMotCorr;   
   displImg_neg.vol = m_in.Data.negStatVol;
   displImg_neg.mat = matTemplMotCorr; 
end

[backg_imgt,backg_imgc,backg_imgs, stat_imgt, stat_imgc, stat_imgs, P] = redrawall(displBackgr.vol, displBackgr.mat, ROIsOverlay, displImg, P);
if ~isempty(displImg_neg)
    [backg_imgt,backg_imgc,backg_imgs, stat_imgt_neg, stat_imgc_neg, stat_imgs_neg, P] = redrawall(displBackgr.vol, displBackgr.mat, ROIsOverlay, displImg_neg, P);
    
    stat_imgt_neg = uint8(stat_imgt_neg / max(stat_imgt_neg(:)) * 255);
    stat_imgc_neg = uint8(double(stat_imgc_neg) / max(stat_imgc_neg(:)) * 255);
    stat_imgs_neg = uint8(double(stat_imgs_neg) / max(stat_imgs_neg(:)) * 255);

    assignin('base', 'stat_imgt', stat_imgt_neg);
    assignin('base', 'stat_imgc', stat_imgc_neg);
    assignin('base', 'stat_imgs', stat_imgs_neg);
    
    fname = strrep(P.memMapFile, 'shared', 'OrthView_neg');
    m_out = memmapfile(fname, 'Writable', true, 'Format', 'uint8');
    l1 = prod(size(stat_imgt_neg));
    m_out.Data(1:l1) = stat_imgt_neg(:);
    l2 = prod(size(stat_imgc_neg));
    m_out.Data(l1+1:l1+l2) = stat_imgc_neg(:);
    l3 = prod(size(stat_imgs_neg));
    m_out.Data(l1+l2+1:l1+l2+l3) = stat_imgs_neg(:);
end
    
backg_imgt = uint8(backg_imgt / max(backg_imgt(:)) * 255);
backg_imgc = uint8(double(backg_imgc) / max(backg_imgc(:)) * 255);
backg_imgs = uint8(double(backg_imgs) / max(backg_imgs(:)) * 255);

assignin('base', 'imgt', backg_imgt);
assignin('base', 'imgc', backg_imgc);
assignin('base', 'imgs', backg_imgs);

stat_imgt = uint8(stat_imgt / max(stat_imgt(:)) * 255);
stat_imgc = uint8(double(stat_imgc) / max(stat_imgc(:)) * 255);
stat_imgs = uint8(double(stat_imgs) / max(stat_imgs(:)) * 255);

assignin('base', 'stat_imgt', stat_imgt);
assignin('base', 'stat_imgc', stat_imgc);
assignin('base', 'stat_imgs', stat_imgs);

%% images for OrthView in GUI from helper matlab
fname = strrep(P.memMapFile, 'shared', 'BackgOrthView');
m_out = memmapfile(fname, 'Writable', true, 'Format', 'uint8');
l1 = prod(size(backg_imgt));
m_out.Data(1:l1) = backg_imgt(:);
l2 = prod(size(backg_imgc));
m_out.Data(l1+1:l1+l2) = backg_imgc(:);
l3 = prod(size(backg_imgs));
m_out.Data(l1+l2+1:l1+l2+l3) = backg_imgs(:);

fname = strrep(P.memMapFile, 'shared', 'OrthView');
m_out = memmapfile(fname, 'Writable', true, 'Format', 'uint8');
l1 = prod(size(stat_imgt));
m_out.Data(1:l1) = stat_imgt(:);
l2 = prod(size(stat_imgc));
m_out.Data(l1+1:l1+l2) = stat_imgc(:);
l3 = prod(size(stat_imgs));
m_out.Data(l1+l2+1:l1+l2+l3) = stat_imgs(:);

assignin('base', 'helperP', P);

disp('sending images to python GUI...');


function [backg_imgt, backg_imgc, backg_imgs, stat_imgt, stat_imgc, stat_imgs, P] = redrawall(Vol, mat, ROIs, Image, P)
global strParam

%% Calculate Background
bb   = strParam.bb;
Dims = round(diff(bb)'+1);
is   = inv(strParam.Space);
cent = is(1:3,1:3) * strParam.centre(:) + is(1:3,4);

M = strParam.Space\strParam.premul*mat;
TM0 = [ 1 0 0 -bb(1,1)+1
        0 1 0 -bb(1,2)+1
        0 0 1  -cent(3)
        0 0 0     1     ];
TM = inv(TM0 * M);
TD = Dims([1 2]);

CM0 = [ 1 0 0 -bb(1,1)+1
        0 0 1 -bb(1,3)+1
        0 1 0  -cent(2)
        0 0 0     1     ];
CM = inv(CM0 * M);
CD = Dims([1 3]);

if strParam.mode == 0
    SM0 = [ 0 0 1 -bb(1,3)+1
            0 1 0 -bb(1,2)+1
            1 0 0  -cent(1)
            0 0 0     1     ];
    SM = inv(SM0 * M);
    SD = Dims([3 2]);
else
    SM0 = [ 0 -1 0 +bb(2,2)+1
            0  0 1 -bb(1,3)+1
            1  0 0 -cent(1)
            0  0 0    1];
    SM = inv(SM0 * M);
    SD = Dims([2 3]);
end;

% Template parameters, used for ROIs and Stat map
coordParam.TM0 = TM0; coordParam.CM0 = CM0; coordParam.SM0 = SM0; 
coordParam.TD  = TD;  coordParam.CD  = CD;  coordParam.SD = SD;

try
    % background slicing
    [ backg_imgt, backg_imgc, backg_imgs ]  = getOrthVol(coordParam, Vol, mat);
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
    backg_imgt = max(backg_imgt, mn); backg_imgt = min(backg_imgt, mx);
    backg_imgc = max(backg_imgc, mn); backg_imgc = min(backg_imgc, mx);
    backg_imgs = max(backg_imgs, mn); backg_imgs = min(backg_imgs, mx);
    
    % recompute min/max for display
    mx = -inf; mn = inf;

    if ~isempty(backg_imgt)
        tmp = backg_imgt(isfinite(backg_imgt));
        mx = max([mx max(max(tmp))]);
        mn = min([mn min(min(tmp))]);
    end;
    if ~isempty(backg_imgc)
        tmp = backg_imgc(isfinite(backg_imgc));
        mx = max([mx max(max(tmp))]);
        mn = min([mn min(min(tmp))]);
    end;
    if ~isempty(backg_imgs)
        tmp = backg_imgs(isfinite(backg_imgs));
        mx = max([mx max(max(tmp))]);
        mn = min([mn min(min(tmp))]);
    end;
    if mx == mn, mx = mn + eps; end;
else
    backg_imgt = [];
    backg_imgc = [];
    backg_imgs = [];
end

% Calculate Stat
[stat_imgt, stat_imgc, stat_imgs] = getOrthVol(coordParam, Image.vol, Image.mat);

if strParam.modeDispl(1)
    % Calculate ROIs
    roiCount = length(ROIs);

    P.tRoiBoundaries = cell(1, roiCount);
    P.cRoiBoundaries = cell(1, roiCount);
    P.sRoiBoundaries = cell(1, roiCount);

    for j = 1:roiCount
        [tRoiImg, cRoiImg, sRoiImg] = getOrthVol(coordParam, ROIs(j).vol, ROIs(j).mat);

        P.tRoiBoundaries{j} = roiBoundary(tRoiImg);
        P.cRoiBoundaries{j} = roiBoundary(cRoiImg);
        P.sRoiBoundaries{j} = roiBoundary(sRoiImg);
    end
else
    P.tRoiBoundaries = {};
    P.cRoiBoundaries = {};
    P.sRoiBoundaries = {};
end

return

function boundary = roiBoundary(roi)
[row, col] = find(roi ~= 0 & ~isnan(roi));

if ~isempty(row)
    boundary = bwtraceboundary(roi, [row(1), col(1)], 'N');
else
    boundary = [];
end

function [imgt, imgc, imgs] = getOrthVol(coordParam, vol3D, volMat)
global strParam
% get blob data
M    = strParam.Space \ strParam.premul * volMat;
imgt = spm_slice_vol(vol3D,inv(coordParam.TM0*M),coordParam.TD, [0 NaN])';
imgc = spm_slice_vol(vol3D,inv(coordParam.CM0*M),coordParam.CD, [0 NaN])';
imgs = fliplr(spm_slice_vol(vol3D,inv(coordParam.SM0*M),coordParam.SD, [0 NaN])');

return

function centre = findcent(CoordLoc, flagsPlanes)
% newCoord = [0,0; 0,0; 100,100]; % new coordinates on [T; S; C]
% flagsPlanes = [0 0 1]; % click was on [transverse, sagital, coron]
global strParam
%obj    = get(st.fig,'CurrentObject');
centre = [];
cent   = [];
cp     = [];
for j=1:3
    if flagsPlanes(j) % new coordinates on Transverse
        cp = CoordLoc(j,:);  
    end
    if ~isempty(cp)
        cp   = cp(1,1:2);
        is   = inv(strParam.Space);
        cent = is(1:3,1:3) * strParam.centre(:) + is(1:3,4);
        switch j
            case 1 % click was on Transverse: s and t need to change
                cent([1 2])=[cp(1) + strParam.bb(1,1) - 1 ...
                             cp(2) + strParam.bb(1,2) - 1];
            case 2 % click was on Saggital: t and c need to change
                cent([1 3])=[cp(1) + strParam.bb(1,1) - 1 ...
                             cp(2) + strParam.bb(1,3) - 1];
            case 3 % click was on Coronal: t ans s need to change
                if strParam.mode == 0
                    cent([3 2])=[cp(1) + strParam.bb(1,3) - 1 ...
                                 cp(2) + strParam.bb(1,2) - 1];
                else
                    cent([2 3])=[strParam.bb(2,2) + 1 - cp(1) ...
                                 cp(2) + strParam.bb(1,3) - 1];
                end;
        end;
        break;
    end;
end;
if ~isempty(cent)
    centre = strParam.Space(1:3,1:3)*cent(:) + strParam.Space(1:3,4); 
end;
return;