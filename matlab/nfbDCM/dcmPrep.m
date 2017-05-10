function [DCM_EN, dcmParTag, dcmParOpp] = dcmPrep(SPM)
% Function to prepare initial DCM structure from hrad-coded paprameters
% and SPM structure.
%
% input:
% SPM - SPM structure
%
% output:
% DCM_EN    - initial DCM structure
% dcmParTag - model-defining structure for a target model (model 1)
% dcmParOpp - model-defining structure for an opposed model (model 2)
%__________________________________________________________________________
% Copyright (C) 2016-2017 OpenNFT.org
%
% Written by Yury Koush

%% define structure/network
dcmParTag.tdcmName      = ['DCM_MTag_' date];
dcm.a         = [1 0 1; 0 1 1; 1 1 1];
dcm.b         = [0 0 1; 0 0 1; 0 0 0];
dcm.c         = [0; 0; 1];
dcmParTag.dcm = dcm;

dcmParOpp.tdcmName      = ['DCM_MOpp_' date];
dcm.a         = [1 0 1; 0 1 1; 1 1 1];
dcm.b         = [0 0 0; 0 0 0; 1 1 0];
dcm.c         = [1; 1; 0];
dcmParOpp.dcm = dcm;

%% Settings, SPM settings, condition definition
DCM_EN.options.nonlinear  = 0;
DCM_EN.options.two_state  = 0;
DCM_EN.options.stochastic = 0;
DCM_EN.options.nograph    = 1;
% mean-centering of regressors
% Importantly, this option is set differently in default SPM8 (TRUE) and
% SPM12 (FALSE)
DCM_EN.options.centre     = 1;

DCM_EN.Y.dt    = SPM.xY.RT;
DCM_EN.U.dt    = SPM.Sess.U(1).dt;
DCM_EN.U.name  = [SPM.Sess.U(1).name];
DCM_EN.U.u     = [SPM.Sess.U(1).u(33:end,1)];  %SPM, 1 = 'Cond'; 2 = 'Bas';
DCM_EN.TE      = 0.03;
DCM_EN.n       = 3; % number of ROIs in a single DCM model
DCM_EN.delays  = repmat(SPM.xY.RT,DCM_EN.n,1);
DCM_EN.d       = zeros(DCM_EN.n,DCM_EN.n,0);
DCM_EN.Y.X0    = []; % intializing regressors for DCM model

