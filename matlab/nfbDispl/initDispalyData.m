function displayData = initDispalyData(indVol)
% Function to initialize the PTB display data structure from main loop
% data structure.
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Artem Nikonorov, Yury Koush

mainLoopData = evalin('base', 'mainLoopData');

% displayData contains fields:
% {'feedbackType', 'condition', 'dispValue', 'Reward', 
%  'displayStage','displayBlankScreen', 'iteration'};

if isfield(mainLoopData, 'displayData')
    displayData = mainLoopData.displayData;
else
    displayData = struct;
end

