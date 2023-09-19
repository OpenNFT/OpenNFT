function displayFeedback(displayData)
% Function to display feedbacks using PTB functions
%
% input:
% displayData - input data structure
%
% Note, synchronization issues are simplified, e.g. sync tests are skipped.
% End-user is advised to configure the use of PTB on their own workstation
% and justify more advanced configuration for PTB.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

tDispl = tic;

P = evalin('base', 'P');
Tex = evalin('base', 'Tex');

% Note, don't split cell structure in 2 lines with '...'.
fieldNames = {'feedbackType', 'condition', 'dispValue', 'Reward', 'blockNF', 'displayStage','displayBlankScreen', 'iteration'};
defaultFields = {'', 0, 0, '', 0, '', '', 0};
% disp(displayData)
eval(varsFromStruct(displayData, fieldNames, defaultFields));

indVolNorm = iteration - P.nrSkipVol;

if ~strcmp(feedbackType, 'DCM')
    dispColor = [255, 255, 255];
    instrColor = [155, 150, 150];
end

switch feedbackType
    %% Continuous PSC
    case 'bar_count'
        dispValue  = dispValue*(floor(P.Screen.h/2) - floor(P.Screen.h/10))/100;
        switch condition
            case 1 % Baseline
                % Text "COUNT"
                Screen('TextSize', P.Screen.wPtr , P.Screen.h/10);
                Screen('DrawText', P.Screen.wPtr, 'COUNT', ...
                    floor(P.Screen.w/2-P.Screen.h/4), ...
                    floor(P.Screen.h/2-P.Screen.h/10), instrColor);
            case 2 % Regualtion
                % Fixation Point
                Screen('FillOval', P.Screen.wPtr, [255 255 255], ...
                    [floor(P.Screen.w/2-P.Screen.w/200), ...
                    floor(P.Screen.h/2-P.Screen.w/200), ...
                    floor(P.Screen.w/2+P.Screen.w/200), ...
                    floor(P.Screen.h/2+P.Screen.w/200)]);
                % draw target bar
                Screen('DrawLines', P.Screen.wPtr, ...
                    [floor(P.Screen.w/2-P.Screen.w/20), ...
                    floor(P.Screen.w/2+P.Screen.w/20); ...
                    floor(P.Screen.h/10), floor(P.Screen.h/10)], ...
                    P.Screen.lw, [255 0 0]);
                % draw activity bar
                Screen('DrawLines', P.Screen.wPtr, ...
                    [floor(P.Screen.w/2-P.Screen.w/20), ...
                    floor(P.Screen.w/2+P.Screen.w/20); ...
                    floor(P.Screen.h/2-dispValue), ...
                    floor(P.Screen.h/2-dispValue)], P.Screen.lw, [0 255 0]);
        end
        P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
            P.Screen.vbl + P.Screen.ifi/2);
    
    %% Continuous PSC with task block
    case 'bar_count_task'
        dispValue  = dispValue*(floor(P.Screen.h/2) - floor(P.Screen.h/10))/100;
        switch condition
            case 1 % Baseline
                % Text "COUNT"
                Screen('TextSize', P.Screen.wPtr , P.Screen.h/10);
                Screen('DrawText', P.Screen.wPtr, 'COUNT', ...
                    floor(P.Screen.w/2-P.Screen.h/4), ...
                    floor(P.Screen.h/2-P.Screen.h/10), instrColor);
                
                 P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                     P.Screen.vbl + P.Screen.ifi/2);
                
            case 2 % Regualtion
                % Fixation Point
                Screen('FillOval', P.Screen.wPtr, [255 255 255], ...
                    [floor(P.Screen.w/2-P.Screen.w/200), ...
                    floor(P.Screen.h/2-P.Screen.w/200), ...
                    floor(P.Screen.w/2+P.Screen.w/200), ...
                    floor(P.Screen.h/2+P.Screen.w/200)]);
                % draw target bar
                Screen('DrawLines', P.Screen.wPtr, ...
                    [floor(P.Screen.w/2-P.Screen.w/20), ...
                    floor(P.Screen.w/2+P.Screen.w/20); ...
                    floor(P.Screen.h/10), floor(P.Screen.h/10)], ...
                    P.Screen.lw, [255 0 0]);
                % draw activity bar
                Screen('DrawLines', P.Screen.wPtr, ...
                    [floor(P.Screen.w/2-P.Screen.w/20), ...
                    floor(P.Screen.w/2+P.Screen.w/20); ...
                    floor(P.Screen.h/2-dispValue), ...
                    floor(P.Screen.h/2-dispValue)], P.Screen.lw, [0 255 0]);
                
                    P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                        P.Screen.vbl + P.Screen.ifi/2);
            case 3
                % ptbTask sequence called seperetaly in python
                
        end
        
    %% Intermittent PSC
    case 'value_fixation'
        indexSmiley = round(dispValue/10);
        if indexSmiley == 0
            indexSmiley = 1;
        elseif indexSmiley > 10
            indexSmiley = 10;
        end
        switch condition
            case 1  % Baseline
                Screen(P.Screen.wPtr, 'FillRect', [100 100 100]);
                % fixation cross
                Screen('DrawLines', P.Screen.wPtr, ...
                    [floor(P.Screen.w/2-P.Screen.w/20), ...
                    floor(P.Screen.w/2+P.Screen.w/20); ...
                    floor(P.Screen.h/2), floor(P.Screen.h/2)], ...
                    P.Screen.lw, [200 200 200]);
                Screen('DrawLines', P.Screen.wPtr, ...
                    [floor(P.Screen.w/2), ...
                    floor(P.Screen.w/2); ...
                    floor(P.Screen.h/2+P.Screen.w/20), floor(P.Screen.h/2-P.Screen.w/20)], ...
                    P.Screen.lw, [200 200 200]);

                 P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                     P.Screen.vbl + P.Screen.ifi/2);

            case 2  % Regualtion 1
                % Text
                Screen(P.Screen.wPtr, 'FillRect', [100 100 100]);
                Screen('TextSize', P.Screen.wPtr , P.Screen.h/10);
                Screen('DrawText', P.Screen.wPtr, 'IMAGINE  TAPPING', ...
                    floor(P.Screen.w/2-P.Screen.h/3), ...
                    floor(P.Screen.h/2-P.Screen.h/10), instrColor);
                % Fixation Point
                Screen('FillOval', P.Screen.wPtr, [200 200 200], ...
                    [floor(P.Screen.w/2-P.Screen.w/200), ...
                    floor(P.Screen.h/2-P.Screen.w/200), ...
                    floor(P.Screen.w/2+P.Screen.w/200), ...
                    floor(P.Screen.h/2+P.Screen.w/200)]);

                 P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                     P.Screen.vbl + P.Screen.ifi/2);
            case 3  % Regualtion 2
                if P.vectList(indVolNorm) == 1
                    wordDisp = char(P.wordList(indVolNorm));
                    jitterDisp = P.jitterList(indVolNorm);
                    fprintf(['case 3 volume ' mat2str(indVolNorm) ' jitter set ' mat2str(jitterDisp) '\n'])
                    % Text
                    Screen(P.Screen.wPtr, 'FillRect', [100 100 100]);
                    Screen('TextSize', P.Screen.wPtr , P.Screen.h/10);
                    Screen('DrawText', P.Screen.wPtr, wordDisp, ...
                        floor(P.Screen.w/2-P.Screen.h/10), ...
                        floor(P.Screen.h/2-P.Screen.h/10), instrColor);
                    % Fixation Point
                    Screen('FillOval', P.Screen.wPtr, [200 200 200], ...
                        [floor(P.Screen.w/2-P.Screen.w/200), ...
                        floor(P.Screen.h/2-P.Screen.w/200), ...
                        floor(P.Screen.w/2+P.Screen.w/200), ...
                        floor(P.Screen.h/2+P.Screen.w/200)]);

                     pause(jitterDisp);

                     P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                         P.Screen.vbl + P.Screen.ifi/2);

                     nPause = P.dispStimTime-P.Screen.ifi/2;
                     pause(nPause);

                    % blanck screen
                     Screen(P.Screen.wPtr, 'FillRect', [100 100 100]);
                     % Fixation Point
                     Screen('FillOval', P.Screen.wPtr, [200 200 200], ...
                         [floor(P.Screen.w/2-P.Screen.w/200), ...
                         floor(P.Screen.h/2-P.Screen.w/200), ...
                         floor(P.Screen.w/2+P.Screen.w/200), ...
                         floor(P.Screen.h/2+P.Screen.w/200)]);

                     P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                         P.Screen.vbl + P.Screen.ifi/2);
                end
            case 4  % Regualtion 3
                if P.vectList(indVolNorm) == 2
                    wordDisp = char(P.wordList(indVolNorm));
                    jitterDisp = P.jitterList(indVolNorm);
                    fprintf(['case 4 volume ' mat2str(indVolNorm) ' jitter set ' mat2str(jitterDisp) '\n'])

                    % Text
                    Screen(P.Screen.wPtr, 'FillRect', [100 100 100]);
                    Screen('TextSize', P.Screen.wPtr , P.Screen.h/10);
                    Screen('DrawText', P.Screen.wPtr, wordDisp, ...
                        floor(P.Screen.w/2-P.Screen.h/10), ...
                        floor(P.Screen.h/2-P.Screen.h/10), instrColor);
                    % Fixation Point
                    Screen('FillOval', P.Screen.wPtr, [200 200 200], ...
                        [floor(P.Screen.w/2-P.Screen.w/200), ...
                        floor(P.Screen.h/2-P.Screen.w/200), ...
                        floor(P.Screen.w/2+P.Screen.w/200), ...
                        floor(P.Screen.h/2+P.Screen.w/200)]);

                     pause(jitterDisp);

                     P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                         P.Screen.vbl + P.Screen.ifi/2);

                     nPause = P.dispStimTime-P.Screen.ifi/2;
                     pause(nPause);

                     % blanck screen
                     Screen(P.Screen.wPtr, 'FillRect', [100 100 100]);
                     % Fixation Point
                     Screen('FillOval', P.Screen.wPtr, [200 200 200], ...
                         [floor(P.Screen.w/2-P.Screen.w/200), ...
                         floor(P.Screen.h/2-P.Screen.w/200), ...
                         floor(P.Screen.w/2+P.Screen.w/200), ...
                         floor(P.Screen.h/2+P.Screen.w/200)]);
                     P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                         P.Screen.vbl + P.Screen.ifi/2);
                end
            case 5  % Rest
                % blanck screen
                 Screen(P.Screen.wPtr, 'FillRect', [0 0 0]);
                 P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                     P.Screen.vbl + P.Screen.ifi/2);

            case 6 % NF
                if P.isPrePostTest
                    % blanck screen
                     Screen(P.Screen.wPtr, 'FillRect', [0 0 0]);
                     P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                         P.Screen.vbl + P.Screen.ifi/2);
                else
                    % random NFB values
                    if P.isRandTrials
                        dispValue = P.perRunValRandNFB(blockNF);
                    end
                    %
                    Screen(P.Screen.wPtr, 'FillRect', [0 0 0]);
                    % feedback value
                    Screen('DrawText', P.Screen.wPtr, mat2str(dispValue), ...
                        P.Screen.w/2 - P.Screen.w/30+0, ...
                        P.Screen.h/2 - P.Screen.h/4, dispColor);
                    % smiley
                    Screen('DrawTexture', P.Screen.wPtr, ...
                        Tex(indexSmiley), ...
                        P.Screen.rectSm, P.Screen.dispRect+[0 0 0 0]);
                    % display
                    P.Screen.vbl = Screen('Flip', P.Screen.wPtr, ...
                        P.Screen.vbl + P.Screen.ifi/2);
                end
        end
        
    %% Trial-based DCM
    case 'DCM'
        nrP = P.nrP;
        nrN = P.nrN;
        imgPNr = P.imgPNr;
        imgNNr = P.imgNNr;
        switch condition
            case 1 % Neutral textures
                % Define texture
                nrP = 0;
                nrN = nrN + 1;
                if (nrN == 1) || (nrN == 5) || (nrN == 9)
                    imgNNr = imgNNr + 1;
                    disp(['Neut Pict:' mat2str(imgNNr)]);
                end
                if nrN < 5
                    basImage = Tex.N(imgNNr);
                elseif (nrN > 4) && (nrN < 9)
                    basImage = Tex.N(imgNNr);
                elseif nrN > 8
                    basImage = Tex.N(imgNNr);
                end
                % Draw Texture
                Screen('DrawTexture', P.Screen.wPtr, basImage);
                P.Screen.vbl=Screen('Flip', P.Screen.wPtr, ...
                    P.Screen.vbl+P.Screen.ifi/2);

            case 2 % Positive textures
                % Define texture
                nrN = 0;
                nrP = nrP + 1;
                if (nrP == 1) || (nrP == 5) || (nrP == 9)
                    imgPNr = imgPNr + 1;
                    disp(['Posit Pict:' mat2str(imgPNr)]);
                end
                if nrP < 5
                    dispImage = Tex.P(imgPNr);
                elseif (nrP > 4) && (nrP < 9)
                    dispImage = Tex.P(imgPNr);
                elseif nrP > 8
                    dispImage = Tex.P(imgPNr);
                end
                % Draw Texture
                Screen('DrawTexture', P.Screen.wPtr, dispImage);
                P.Screen.vbl=Screen('Flip', P.Screen.wPtr, ...
                    P.Screen.vbl+P.Screen.ifi/2);

            case 3 % Rest epoch
                % Black screen case is called seaprately in Python to allow
                % using PTB Matlab Helper process for DCM model estimations

            case 4 % NF display
                nrP = 0;
                nrN = 0;
                % red if positive, blue if negative
                if dispValue >0
                    dispColor = [255, 0, 0];
                else
                    dispColor = [0, 0, 255];
                end
                % instruction reminder
                Screen('DrawText', P.Screen.wPtr, 'UP', ...
                    P.Screen.w/2 - P.Screen.w/15, ...
                    P.Screen.h/2 - P.Screen.w/8, [255, 0, 0]);
                % feedback value
                Screen('DrawText', P.Screen.wPtr, ...
                    ['(' mat2str(dispValue) ')'], ...
                    P.Screen.w/2 - P.Screen.w/7, ...
                    P.Screen.h/2 + P.Screen.w/200, dispColor);
                % monetary reward value
                Screen('DrawText', P.Screen.wPtr, ['+' Reward 'CHF'], ...
                    P.Screen.w/2 - P.Screen.w/7, ...
                    P.Screen.h/2 + P.Screen.w/7, dispColor);
                P.Screen.vbl=Screen('Flip', P.Screen.wPtr, ...
                    P.Screen.vbl + P.Screen.ifi/2);
                % basic flickering given TR
                if 1
                    pause(randi([600,800])/1000);
                    P.Screen.vbl=Screen('Flip', P.Screen.wPtr, ...
                        P.Screen.vbl + P.Screen.ifi/2);
                end
        end
        P.nrP = nrP;
        P.nrN = nrN;
        P.imgPNr = imgPNr;
        P.imgNNr = imgNNr;
end

% EventRecords for PTB
% Each event row for PTB is formatted as
% [t9, t10, displayTimeInstruction, displayTimeFeedback]
t = posixtime(datetime('now','TimeZone','local'));
tAbs = toc(tDispl);
if strcmp(displayStage, 'instruction')
    P.eventRecords(1, :) = repmat(iteration,1,4);
    P.eventRecords(iteration + 1, :) = zeros(1,4);
    P.eventRecords(iteration + 1, 1) = t;
    P.eventRecords(iteration + 1, 3) = tAbs;
elseif strcmp(displayStage, 'feedback')
    P.eventRecords(1, :) = repmat(iteration,1,4);
    P.eventRecords(iteration + 1, :) = zeros(1,4);
    P.eventRecords(iteration + 1, 2) = t;
    P.eventRecords(iteration + 1, 4) = tAbs;
end
recs = P.eventRecords;
save(P.eventRecordsPath, 'recs', '-ascii', '-double');

assignin('base', 'P', P);
