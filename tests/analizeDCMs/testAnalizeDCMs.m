%
% Package to perform the  Offline Test of real-time DCM adaptations
% on SPM8 and SPM12 DCM packages.
%
% This package provides a possibility to check target vs. opposed DCM model
% comparison using a set of functions that maximally preserve the OpenNFT
% implementation to facilitate an integration of the offline tests into the
% real-time extension using OpenNFT.
%
% Special attention needs to be paid to setting the DCM.options which we
% implemented in dcmPrep.m and the differences between default settings in
% SPM8 and SPM12. To change between SPM8 and SPM12, set flag isSPM8 in
% dcmEst() function (dcmCalc.m).
%
% Note that mean-centering of the regressors and priors for the log
% precision of the observation noise are set differently in SPM8 and SPM12,
% which could result in differences of the logBF estimations given
% different assumptions about observation noise in data.
% We hard-coded the SPM8 settings in SPM12 functions for M.hE
% (the expected log precision of the noise) and  M.hC (the uncertainty).
% Matching both the mean-centring and noise prior gives similar results for
% both SPM8 and SPM12.
% M.hE effectively sets a prior on how complex you expect your target and
% opposed models to be. If you tell DCM that you believe the signal is
% very noisy (e.g. hE=0 (SPM8)), then it will favour a simpler model that
% only explains some of the variance. If you tell DCM that you believe the
% signal is very clean, with very little noise (e.g. hE=6 (SPM12)), then it
% will favour a more complex model that explains more of the variance.
% To make this comparison fairly, you might check the number of iterations
% to fit the model properly. Currently, the estimation is limited at 30
% iterations, therefore, the simpler model is favoured to converge quickly.
% If you want to use DCM to ask what is the best setting of M.hE in your
% data, you may check the estimations using 128 maximum iterations and
% pilot data (see Koush et al. 2013).
%
% For generic aspects see:
% Koush Y, Rey G, Pichon S, Rieger S, Linden D, Van De Ville D,
% Vuilleumier P, Scharnowski F (2015): Learning control over emotion
% networks through connectivity-based neurofeedback.(2017) 27(2):1193-1202.
%
% Koush Y, Rosa MJ, Robineau F, Heinen K, Rieger S, Weiskopf N,
% Vuilleumier P, van de Ville D, Scharnowski F (2013): Connectivity-based
% neurofeedback: dynamic causal modeling for real-time fMRI.
% Neuroimage 81:422-30.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush, Peter Zeidman
%
%

clc
clear
% add path to offline DCM functions
addpath('.\nfbDCM_Offl');

% path to NF_Data_* folder (DCM run outcome) or copy in the same directory
dataDir            = '.\NF_Data_1\';
timeseriesFileName = [dataDir 'foo_1_proc_tsROIs.mat'];
parametersFileName = [dataDir 'foo_1_P.mat'];
% path(rename) to SPM.mat or copy in the same directory.
% It is generated in the \Settings.
spmFileName        = ['.\SPM_DCM.mat'];

% Calculate DCM for NF trial indices,
% specify indices as xdxTrials = 1:7, or 2:4, or 5
idxTrials = 1%:7;
logBF_Offl = analyzeDCMs(idxTrials, parametersFileName, ...
    spmFileName, timeseriesFileName);
disp([char(10), 'OFFL logBF values: ', num2str(logBF_Offl(idxTrials))]);

% Compare with online logBFs stored in mainLoopData
mainLoopData = load([dataDir 'foo_1_mainLoopData' '.mat']);
logBF = mainLoopData.logBF;
disp([char(10), 'RT   logBF values: ', num2str(logBF(idxTrials))]);
