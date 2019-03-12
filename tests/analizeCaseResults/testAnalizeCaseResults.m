
% This wrapper performs the comparison between the custom case run on 
% Demo data and our in-house reference run on Demo data.
% The comparison is performed in terms of the processed time-series after
% Kalman filter denoising, and resultant non-avergaed neurofeedback values.
%
% Note, the reference data is made using OpenNFT v1.0 rc0 and its settings.
%
% Note, the test time-series are of different lengths and contain different 
% number of ROIs. 
% Note, the vectors of feedback values are specific to the feedback type.
%
% Usage: 
% Unpack .zip folders with data structures and corrsponding reference .mat
% files.
% Copy-paste your test NF_Data_* time-series and feedback values, i.e.
%  *_proc_tsROIs.mat and *_NFBs.mat into the corresponding nfData folder. 
%
% Initial check:
% To verify this test performance, duplicate the corresponding reference
% directory (i.e., .\refData\*) into the case neurofeedback directory 
% (i.e., .\nfData\*). This check will provide the '100% test passed.'
% messages.
% 
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

clc
clear
close all

%% paths to reference and cse-study folders
refDir = '.\refData\';
nfDir = '.\nfData\';
dataRefDirs    = dir([refDir 'ref*']);
dataNfDirs = dir([nfDir 'nf*']);

% specify indices as xdxTrials = [1:4], or [2,4], or 3
% 1: DCM; 2: PSC_cont; 3: PSC_int; 4: SVM
idxTypes = [1:4];
for iTest = idxTypes
    %% time-series
    % get file names
    refTSFileName = ls([refDir dataRefDirs(iTest).name '\*tsROIs.mat']);
    nfTSFileName = ls([nfDir dataNfDirs(iTest).name '\*tsROIs.mat']);   
    refTSFile = fullfile(refDir,dataRefDirs(iTest).name,refTSFileName);    
    nfTSFile = fullfile(nfDir,dataNfDirs(iTest).name,nfTSFileName);
    
    % visualize data parameters  
    % referential Demo data trials
    refTS = load(refTSFile);    
    [refNrROIs lrefTS] = size(refTS.kalmanProcTimeSeries);
    disp([char(10), refTSFile, ': ']);
    disp([char(10), 'Number of ROIs: ', num2str(refNrROIs),...
        ',  Time-series length: ', num2str(lrefTS)]);
    % local Demo case-study trials
    nfTS = load(nfTSFile); 
    [nfNrROIs lnfTS] = size(nfTS.kalmanProcTimeSeries);
    disp([char(10), refTSFile, ': ']);
    disp([char(10), 'Number of ROIs: ', num2str(nfNrROIs),...
        ',  Time-series length: ', num2str(lnfTS), char(10)]);
    
    % compare time-series data structures
    analizeCaseResults(nfTSFile, refTSFile);
    clear nfTSFile refTSFile refTS nfTS
    
    %% feedback values    
    % get file names
    refNFBFileName = ls([refDir dataRefDirs(iTest).name '\*NFBs.mat']);
    nfNFBFileName = ls([nfDir dataNfDirs(iTest).name '\*NFBs.mat']);   
    refNFBFile = fullfile(refDir,dataRefDirs(iTest).name,refNFBFileName);    
    nfNFBFile = fullfile(nfDir,dataNfDirs(iTest).name,nfNFBFileName);
    
    % visualize data parameters  
    % referential Demo data trials
    refNFB = load(refNFBFile);    
    lrefNFB = length(refNFB.vectNFBs);
    disp([char(10), refNFBFile, ': ']);
    disp([char(10), 'Length of presented feedback vector: ', ...
        num2str(lrefNFB)]);
    % local Demo case-study trials
    nfNFB = load(nfNFBFile); 
    lnfNFB = size(nfNFB.vectNFBs);
    disp([char(10), refNFBFile, ': ']);
    disp([char(10), 'Length of presented feedback vector: ', ...
        num2str(lnfNFB), char(10)]);
    
    figure('name',dataNfDirs(iTest).name),
    plot(1:lrefNFB, refNFB.vectNFBs,'.-r'), 
    legend('Reference run');
    
    % compare time-series data structures
    analizeCaseResults(nfNFBFile, refNFBFile);
    clear nfNFBFile refNFBFile refNFB nfNFB    
end
