function addMatlabDirs()
% Function to add OpenNFT Matlab directories
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Artem Nikonorov, Yury Koush

addpath(pathdef);
folders = {'utils', 'nfbDCM', 'nfbPreprSig', 'nfbPreprVol', 'nfbDispl', 'mlniexp', fullfile('..','plugins')};
for i = 1:length(folders)
    folder = [pwd filesep folders{i}];
    if exist(folder,'dir')
        addpath(folder);
    end
end