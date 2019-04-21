function ptbBlankScreen()
% Function to blank the neurofeedback display screen using PTB.
%
% Note, synchronization issues are simplified, e.g. sync tests are skipped.
% End-user is adviced to configure the use of PTB on their own workstation
% and justify more advanced configuration for PTB.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Artem Nikonorov, Yury Koush

P = evalin('base', 'P');

Screen(P.Screen.wPtr, 'FillRect', [0 0 0]);
P.Screen.vbl = Screen('Flip', P.Screen.wPtr, P.Screen.vbl+P.Screen.ifi/2);

assignin('base', 'P', P);

