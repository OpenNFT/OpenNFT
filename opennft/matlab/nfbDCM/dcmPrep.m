function [DCM_EN, dcmParTag, dcmParOpp] = dcmPrep(SPM)
    % Function to prepare initial DCM structure from parameters coded in the
    % protocol JSON file and the SPM structure.
    
    % input:
    % SPM - SPM structure
    %
    % output:
    % DCM_EN    - initial DCM structure
    % dcmParTag - model-defining structure for a target model (model 1)
    % dcmParOpp - model-defining structure for an opposed model (model 2)
    %
    % Written by Yury Koush, adapted by Moritz Gruber.
    % -------------------------------------------------------------------------
    
    % -- Get P struct from workspace ------------------------------------------
    jsonfile = evalin('base', 'P.ProtocolFile');
    
    % -- Load DCM specification from JSON file --------------------------------
    dcmDef = parseDCMdef(jsonfile);
    
    dcmParTag.tdcmName = ['DCM_MTag_' date];
    dcmParTag.dcm      = dcmDef.target;
    
    dcmParOpp.tdcmName = ['DCM_MOpp_' date];
    dcmParOpp.dcm      = dcmDef.opposed;
    
    DCM_EN.options     = dcmDef.options;
    
    % -- Fill DCM_EN based on SPM ---------------------------------------------
    
    % Adapt this for multiple inputs eventually
    DCM_EN.Y.dt     = SPM.xY.RT;
    DCM_EN.U.dt     = SPM.Sess.U(2).dt;
    DCM_EN.U.name   = SPM.Sess.U(2).name;
    DCM_EN.U.u      = SPM.Sess.U(2).u(33:end,1);  %SPM, 1 = 'Bas'; 2 = 'Cond';
    DCM_EN.TE       = 0.03;
    DCM_EN.n        = length(dcmDef.target.a); % number of ROIs in a single DCM model
    DCM_EN.delays   = repmat(SPM.xY.RT,DCM_EN.n,1);
    DCM_EN.d        = zeros(DCM_EN.n,DCM_EN.n,0);
    DCM_EN.Y.X0     = []; % initializing regressors for DCM model
    DCM_EN.roiNames = dcmDef.roiNames;
    
    end
