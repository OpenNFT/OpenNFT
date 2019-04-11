function ptbPreparation(screenId, workFolder, protName)
% Function to prepare PTB parameters to use them during setup and
% run-time within the Matlab Helper process.
%
% input:
% screenId   - screen number from GUI ('Display Feedback on')
% workFolder - path to work folder to get the Settings and picture sets to
%              load
% protName   - name of the neurofeedback protocol from GUI
%
% output:
% Output is assigned to workspace variables.
%
% Note, synchronization issues are simplified, e.g. sync tests are skipped.
% End-user is adviced to configure the use of PTB on their own workstation
% and justify more advanced configuration for PTB.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

P = evalin('base', 'P');

Screen('CloseAll');
Screen('Preference', 'SkipSyncTests', 2);

if ~ismac
    % Because this command messes the coordinate system on the Mac OS
    Screen('Preference', 'ConserveVRAM', 64);
end

AssertOpenGL();

myscreens = Screen('Screens');
if length(myscreens) == 3
    % two monitors: [0 1 2]
    screenid = myscreens(screenId + 1);
elseif length(myscreens) == 2
    % one monitor: [0 1]
    screenid = myscreens(screenId);
else
    % if different, configure your mode
    screenid = 0;
end

fFullScreen = P.DisplayFeedbackFullscreen;

if ~fFullScreen
    % part of the screen, e.g. for test mode
    if strcmp(protName, 'Cont')
        P.Screen.wPtr = Screen('OpenWindow', screenid, [125 125 125], ...
            [40 40 640 520]);
    else
        P.Screen.wPtr = Screen('OpenWindow', screenid, [125 125 125], ...
            [40 40 640 520]);
    end
else
    % full screen
    P.Screen.wPtr = Screen('OpenWindow', screenid, [125 125 125]);
end

[w, h] = Screen('WindowSize', P.Screen.wPtr);
P.Screen.ifi = Screen('GetFlipInterval', P.Screen.wPtr);

% settings
P.Screen.vbl=Screen('Flip', P.Screen.wPtr);
P.Screen.h = h;
P.Screen.w = w;
P.Screen.lw = 5;

% Each event row for PTB is formatted as
% [t9, t10, displayTimeInstruction, displayTimeFeedback]
P.eventRecords = [0, 0, 0, 0];

%% PSC
if strcmp(protName, 'Cont')
    % fixation
    P.Screen.fix = [w/2-w/150, h/2-w/150, w/2+w/150, h/2+w/150];
    Screen('FillOval', P.Screen.wPtr, [255 255 255], P.Screen.fix);
    P.Screen.vbl=Screen('Flip', P.Screen.wPtr,P.Screen.vbl+P.Screen.ifi/2);
    Tex = struct;
end

if strcmp(protName, 'ContTask')
    % Set up alpha-blending for smooth (anti-aliased) lines
    Screen('BlendFunction', P.Screen.wPtr, 'GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA');
    
    % fixation cross settings
    P.Screen.fixCrossDimPix = 40;
    
    % Set the line width for fixation cross
    P.Screen.lineWidthPix = 4;

    % Setting the coordinates
    P.Screen.wRect = [0, 0, P.Screen.w, P.Screen.h];
    [P.Screen.xCenter, P.Screen.yCenter] = RectCenter(P.Screen.wRect);
    P.Screen.xCoords = [-P.Screen.fixCrossDimPix P.Screen.fixCrossDimPix 0 0];
    P.Screen.yCoords = [0 0 -P.Screen.fixCrossDimPix P.Screen.fixCrossDimPix];
    P.Screen.allCoords = [P.Screen.xCoords; P.Screen.yCoords];
    
    % scramble-image presentation parameters
    P.Screen.numSecs = 1;    % presentation dur in sec (500ms)
    P.Screen.numFrames = round(P.Screen.numSecs / P.Screen.ifi);    % in frames
    
    % get some color information
    P.Screen.white = WhiteIndex(screenid);
    P.Screen.black = BlackIndex(screenid);
    P.Screen.grey  = P.Screen.white / 2;

    % response option coords on the x and y axis relative to center 
    P.Screen.option_lx = -250;    % left option     x
    P.Screen.option_rx = 150;     % right option    x
    P.Screen.option_ly = 300;     % left option     y
    P.Screen.option_ry = 300;     % right option    y
    
    % accepted response keys
    P.Screen.leftKey = KbName('1');
    P.Screen.rightKey = KbName('2');

    % show initial fixation dot
    P.Screen.fix = [w/2-w/150, h/2-w/150, w/2+w/150, h/2+w/150];
    Screen('FillOval', P.Screen.wPtr, [255 255 255], P.Screen.fix);
    P.Screen.vbl=Screen('Flip', P.Screen.wPtr,P.Screen.vbl+P.Screen.ifi/2);

    %% Prepare PTB Sprites
    stimPath = P.TaskFolder;
    load([stimPath filesep 'stimNames.mat'])
    
    sz = size(stimNames,2);             % nr of unique images
    P.Screen.nrims = 10;                % how many repetitions of an image
    Tex = zeros(sz,P.Screen.nrims);     % initialize pointer matrix
    for i = 1:sz
        for j = 1:P.Screen.nrims 
            imgArr = imread([stimPath filesep stimNames{i} filesep num2str(j) '.png']);
            Tex(i,j) = Screen('MakeTexture', P.Screen.wPtr, imgArr);
            clear imgArr
        end
    end
    
    % text font, size and style
    Screen('TextFont',P.Screen.wPtr, 'Courier New');
    Screen('TextSize', P.Screen.wPtr, 12);
    Screen('TextStyle',P.Screen.wPtr, 3);
    
    % initiate trial counter variable for keeping track of task trials.
    % Counter values will be used to index images in texture pointer mat.
    P.Task.trialCounter = 1;
   
end

if strcmp(protName, 'Inter')
    for i = 1:10
        imgSm = imread([workFolder filesep 'Settings' filesep ...
            'Smiley' filesep 'Sm' sprintf('%02d', i)], 'bmp');
        Tex(i) = Screen('MakeTexture', P.Screen.wPtr, imgSm);
        clear imgSm
    end
    P.Screen.rectSm = Screen('Rect', Tex(i));
    
    w_dispRect = round(P.Screen.rectSm(4)*1.5);
    w_offset_dispRect = 0;
    P.Screen.dispRect =[(w/2 - w_dispRect/2), ...
        (h/2 + w_offset_dispRect), (w/2 + w_dispRect/2), ...        
        (h/2 + w_offset_dispRect+w_dispRect)];
    
    %% Dots
    % MRI screen parameters
    dist_mri = 44.3; % distance to the screen, cm
    scrw_mri = [34.8 25.8]; % cm
    
    % MRI screen scaling
    screenpix = [w h]; %pixel resolution
    screen_VA = [( 2 * atan(scrw_mri(1) / (2*dist_mri)) ), ...
        ( 2 * atan(scrw_mri(2) / (2*dist_mri)) )]; % the screens visual 
    % angle in radians
    screen_VA = screen_VA * 180/pi; % the screens visual angle in degrees
    degrees_per_pixel = screen_VA ./ screenpix; % degrees per pixel
    degrees_per_pixel_mean = mean(degrees_per_pixel); % approximation of 
    % the average number of degrees per pixel
    pixels_per_degree = 1 ./ degrees_per_pixel;
    pixels_per_degree_mean = 1 ./ degrees_per_pixel_mean;
    
    % circle prescription, via dots
    ddeg = 1:10:360; % degree
    drad = ddeg * pi/180; % rad
    P.Screen.dsize = 5; % dot size
    cs = [cos(drad); sin(drad)];
    % dot positions
    d=round(P.TargDIAM .* pixels_per_degree_mean);
    P.Screen.xy = cs * d / 2;
    r_offset = P.TargRAD * pixels_per_degree(1);
    loc_xy = round(r_offset * [cosd(P.TargANG) sind(P.TargANG)]);
    P.Screen.db = [w/2 h/2] + [+loc_xy(1)  -loc_xy(2)];
    
    % color
    P.Screen.dotCol = 200;
    
    % fixation
    P.Screen.fix = [w/2-w/150, h/2-w/150, w/2+w/150, h/2+w/150];
    Screen('FillOval', P.Screen.wPtr, [155 0 0], P.Screen.fix);
    P.Screen.vbl=Screen('Flip', P.Screen.wPtr,P.Screen.vbl+P.Screen.ifi/2);
    
    % pointing arrow
    P.Screen.arrow.rect = [w/2-w/100, h/2-w/40, w/2+w/100, h/2-w/52];
    P.Screen.arrow.poly_right = [w/2+w/100, h/2-w/32; ...
        w/2+w/50,  h/2-w/46; w/2+w/100, h/2-w/74];
    P.Screen.arrow.poly_left  = [w/2-w/100, h/2-w/32; ...
        w/2-w/50,  h/2-w/46; w/2-w/100, h/2-w/74];
    
    Screen('TextSize',P.Screen.wPtr, 100);
    
end

%% DCM
% Note that images are subject of copyright and thereby replaced.
% Note that pictures and names are not randomized in our example for
% simplicity. The randomization could be done on the level of
% namePictP.mat and namePictN.mat structures given unique pictures per
% NF run in .\nPict and .\nPict folders.
if strcmp(protName, 'InterBlock')
    
    P.nrN = 0;
    P.nrP = 0;
    P.imgPNr = 0;
    P.imgNNr = 0;
    
    %% Prepare PTB Sprites
    % positive pictures
    basePath = strcat(workFolder, filesep, 'Settings', filesep);
    load([basePath 'namePictP.mat']);
    sz = size(namePictP,1);
    Tex.P = zeros(1,sz);
    for i = 1:sz
        fname = strrep(namePictP(i,:), ['.' filesep], basePath);
        imgArr = imread(fname);
        dimImgArr = size(imgArr);
        Tex.P(i) = Screen('MakeTexture', P.Screen.wPtr, imgArr);
        clear imgArr
    end
    
    % neutral pictures
    basePath = strcat(workFolder, filesep, 'Settings', filesep);
    load([basePath 'namePictN.mat']);
    sz = size(namePictN,1);
    Tex.N = zeros(1,sz);
    for i = 1:sz
        fname = strrep(namePictN(i,:), ['.' filesep], basePath);
        imgArr = imread(fname);
        dimImgArr = size(imgArr);
        Tex.N(i) = Screen('MakeTexture', P.Screen.wPtr, imgArr);
        clear imgArr
    end
    
    % text font, style and size
    Screen('TextFont',P.Screen.wPtr, 'Courier New');
    Screen('TextSize',P.Screen.wPtr, 40);
    Screen('TextStyle',P.Screen.wPtr, 3);
    
    %% Draw initial fixation
    Screen('FillOval', P.Screen.wPtr, [150 150 150], ...
        [P.Screen.w/2-w/100, P.Screen.h/2-w/100, ...
        P.Screen.w/2+w/100, P.Screen.h/2+w/100]);
    P.Screen.vbl=Screen('Flip', P.Screen.wPtr,P.Screen.vbl+P.Screen.ifi/2);
end

assignin('base', 'P', P);
assignin('base', 'Tex', Tex);

