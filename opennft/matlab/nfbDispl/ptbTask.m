function ptbTask()

% Scanner PTB task function. This function can be used when you want to
% implement a task condition in addition to the NFB (baseline and
% feedback).It corresponds to condition 3 from the json file and is called
% only once at the onset of a task block. In this sense ptbdisplay is
% temporarily uncoupled from the incoming data which allows you to flip the 
% screen many times and record subject responses without interruption. 

% Below you  can implement any stimulation using psychtoolbox functions, 
% just make sure that your parameters are defined in the ptbPreperation 
% function and that the duration of your stimulation doesn't exceed the
% time specified in your json file. 
%__________________________________________________________________________
%
% Written by Lucas Peek (lucaspeek@live.nl)

P   = evalin('base', 'P');
Tex = evalin('base', 'Tex');

% fixation cross
Screen('DrawLines', P.Screen.wPtr, P.Screen.allCoords,...
4, 1, [P.Screen.xCenter P.Screen.yCenter], 2);
P.Task.fixOns = Screen('Flip', P.Screen.wPtr);

% wait a bit
WaitSecs(2)

% re-adjust textsize for response options on screen
Screen('TextSize',P.Screen.wPtr, 18);

% (re)setting parameters for each trial
task_text={{{'MALE'},{'FEMALE'}}, {{'HAPPY'} {'SAD'}}};

% button response counters to direct visualisation of responses
left_button_count = 0;
right_button_count = 0;

% counter to manage responses and adjust display accordingly
qc=1;
resp_c = 1;

% start listening to key input
KbQueueCreate();
KbQueueStart();

% flip once
P.Screen.vbl = Screen('Flip', P.Screen.wPtr);

% get trial onset
P.trialOns(1,P.Task.trialCounter) = GetSecs;
for ii = 1: P.Screen.nrims             

    waitframes = 1;
    for frame = 1:P.Screen.numFrames
        % draw the response options to buffer
        DrawFormattedText(P.Screen.wPtr, task_text{qc}{1}{1}, P.Screen.xCenter+P.Screen.option_lx,...
            P.Screen.yCenter+P.Screen.option_ly, [0 0 0]);
        DrawFormattedText(P.Screen.wPtr, task_text{qc}{2}{1}, P.Screen.xCenter+P.Screen.option_rx,...
            P.Screen.yCenter+P.Screen.option_ry, [0 0 0]);

        % Draw the image to buffer
        Screen('DrawTexture', P.Screen.wPtr,  Tex(P.Task.trialCounter,ii));

        % Flip the screen
        P.Screen.vbl = Screen('Flip', P.Screen.wPtr, P.Screen.vbl + (waitframes - 0.5) * P.Screen.ifi);
    end

    % Start recording and evalutating responses. In this example, responses
    % are evaluated after every image displayed. As this is a highly simplified
    % version of a real task it makes less sense in its current form.
    [pressed, firstPress]=KbQueueCheck();
    if pressed && resp_c < 3
         % first response male
         if firstPress(P.Screen.leftKey) && resp_c == 1
             % record type, frame and time of response
             P.Task.responses.answer{1,P.Task.trialCounter} = 'male';
             P.Task.responses.detection_frame(1,P.Task.trialCounter)=ii;
             P.Task.responses.timing(1,P.Task.trialCounter) = GetSecs;

             % update counters
             left_button_count = 1;
             qc = 2;
             resp_c = resp_c+1;

             % second response happy (left)
             elseif firstPress(P.Screen.leftKey) && resp_c == 2
                 P.Task.responses.answer{2,P.Task.trialCounter} = 'happy';
                 P.Task.responses.detection_frame(2,P.Task.trialCounter)=ii;
                 P.Task.responses.timing(2,P.Task.trialCounter) = GetSecs;

                 task_text{qc}{2}{1} = '';
                 resp_c = resp_c+1;
             % second response sad (right)
             elseif firstPress(P.Screen.rightKey) && resp_c == 2
                 P.Task.responses.answer{2,P.Task.trialCounter} = 'sad';
                 P.Task.responses.detection_frame(2,P.Task.trialCounter)=ii;
                 P.Task.responses.timing(2,P.Task.trialCounter) = GetSecs;

                 task_text{qc}{1}{1} = '';
                 resp_c = resp_c+1;

         % first response female
         elseif firstPress(P.Screen.rightKey) && resp_c == 1
             P.Task.responses.answer{1,P.Task.trialCounter} = 'female';
             P.Task.responses.detection_frame(1,P.Task.trialCounter)=ii;                 
             P.Task.responses.timing(1,P.Task.trialCounter) = GetSecs;

             right_button_count = 1;
             qc = 2;
             resp_c = resp_c+1;

            % second response happy (left)
             elseif firstPress(P.Screen.leftKey) && resp_c == 2
                 P.Task.responses.answer{2,P.Task.trialCounter} = 'happy';
                 P.Task.responses.detection_frame(2,P.Task.trialCounter)=ii;
                 P.Task.responses.timing(2,P.Task.trialCounter) = GetSecs;

                 task_text{qc}{2}{1} = '';
                 resp_c = resp_c+1;
             % second response sad (right)
             elseif firstPress(P.Screen.rightKey) && resp_c == 2
                 P.Task.responses.answer{2,P.Task.trialCounter} = 'sad';
                 P.Task.responses.detection_frame(2,P.Task.trialCounter)=ii;                     
                 P.Task.responses.timing(2,P.Task.trialCounter) = GetSecs;

                 task_text{qc}{1}{1} = '';
                 resp_c = resp_c+1;         

         % if no response we break the loop after the last image of
         % the trial was displayed
         elseif ii == P.Screen.numFrames
                 P.Task.responses.answer{1,trial} = 'no resp';
                 P.Task.responses.detection_frame(1,P.Task.trialCounter)=NaN;
                 P.Task.responses.detection_frame(2,P.Task.trialCounter)=NaN;          
                 P.Task.responses.timing(1,P.Task.trialCounter) = NaN;
                 P.Task.responses.timing(2,P.Task.trialCounter) = NaN;
            break          
         end
    end
end

% update trial counter
P.Task.trialCounter = P.Task.trialCounter +1;
assignin('base', 'P', P);

% fixation cross for the remainder of the task block
Screen('DrawLines', P.Screen.wPtr, P.Screen.allCoords,...
4, 1, [P.Screen.xCenter P.Screen.yCenter], 2);
Screen('Flip', P.Screen.wPtr);

end



