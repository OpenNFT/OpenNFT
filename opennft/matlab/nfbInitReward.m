function nfbInitReward()
% Function to initialize the reward vector.
% Note, the reward mechanism is exemplified for an Intermittent PSC
% feedback only.
%
% output:
% Output is assigned to workspace variables.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

P = evalin('base', 'P');

flags = getFlagsType(P);

if P.NFRunNr > 1
    folder = [P.WorkFolder filesep 'NF_Data_' num2str(P.NFRunNr - 1)];

    if strcmp(P.Prot, 'Inter') && (flags.isPSC || flags.isCorr)
        load([folder filesep 'reward_' ...
            sprintf('%02d',P.NFRunNr-1) '.mat']);
        P.prev_actValue = prev_actValue;
        assignin('base', 'prev_actValue', prev_actValue);
    end
else
    fprintf('\nPut previous Reward file into the Work Folder!\n');
    P.prev_actValue = [];
end

assignin('base', 'P', P);
