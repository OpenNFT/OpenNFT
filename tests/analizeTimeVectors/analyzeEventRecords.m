function [tv, ts] = analyzeEventRecords(eventrecordsFileName, eventrecordsFileName_display, paramsFileName, startScan, nfbType)
% This function analyses output of eventRecorder and computes main timings for OpenNFT
%
% Usage:
% For continouous PSC feedback,
% [tv, ts] = analyzeEventRecords('path\to\TimeVectors_*.txt', 'path\to\TimeVectors_display_*.txt', 'path\to\*_*_P.mat', 6, 'pscCont');
% For intermittent PSC feedback,
% [tv, ts] = analyzeEventRecords('path\to\TimeVectors_*.txt', 'path\to\TimeVectors_display_*.txt', 'path\to\*_*_P.mat', 6, 'pscInt');
% For continouous SVM feedback,
% [tv, ts] = analyzeEventRecords('path\to\TimeVectors_*.txt', 'path\to\TimeVectors_display_*.txt', 'path\to\*_*_P.mat', 6, 'svmCont');
% For intermittent DCM feedback,
% [tv, ts] = analyzeEventRecords('path\to\TimeVectors_*.txt', 'path\to\TimeVectors_display_*.txt', 'path\to\*_*_P.mat', 11, 'dcmInt');
% For Resting state,
% [tv, ts] = analyzeEventRecords('path\to\TimeVectors_*.txt', '', 'path\to\*_*_P.mat', 7, 'autoRtqa');
% For Task,
% [tv, ts] = analyzeEventRecords('path\to\TimeVectors_*.txt', 'path\to\TimeVectors_display_*.txt', 'path\to\*_*_P.mat', 7, 'task');
%
% Based on eventrecorder.py:
%     # Events timestamps
%     t0 = 0      # MR pulse time in online mode
%
%     t1 = 1      # start file reading from the export folder in online mode
%                 # first non-zero time in online mode, if there is no trigger signal
%     t2 = 2      # finish file reading from the export folder,
%                 # first non-zero time in offline mode
%     t3 = 3      # end of prepossessing routine
%     t4 = 4      # end of spatial-temporal data processing
%     t5 = 5      # end of feedback computation
%     t6 = 6      # begin of display instruction in Python Core process
%     t7 = 7      # begin of display instruction in Python PtbScreen class
%     t8 = 8      # begin of display feedback in Python PtbScreen class
%     t9 = 9      # end of display instruction in Matlab PTB Helper
%     t10 = 10    # end of display feedback in Matlab PTB Helper
%
%     # optional timestamps
%     # DCM special timestamps
%     t11 = 11    # first DCM model computation started
%     t12 = 12    # last DCM model computation is done
%
%     # Events durations
%     d0 = 13     # elapsed time per iteration
%
%   Note that for simplicity, the time events t6 - t12 are named differently in the manuscript
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Yury Koush, Artem Nikonorov

    tv = load(eventrecordsFileName);
    if ~isempty(eventrecordsFileName_display)
        additional_tv = load(eventrecordsFileName_display);
    else
        additional_tv = zeros(length(tv),4);
    end
    tv = [tv, additional_tv];

    P = load(paramsFileName);
    maxCount = max(tv(1,:)) + 1;

    if strcmp(nfbType,'pscCont')
        % cumulative time stamps
        % 1st column is trigger-pulse time, not taken into account here
        ts = tv(startScan + 1:maxCount, 2:6) - repmat(tv(startScan + 1:maxCount, 2), 1, 5);
        ts(ts<0)=0;
        % msec
        ts = ts*1000;
    
        % time stamp differences
        % 1st column is trigger-pulse time, not taken into account here
        ds = tv(startScan + 1:maxCount, 3:6) - tv(startScan + 1:maxCount, 2:5);
        ds(ds<0) = 0;
        % msec
        ds = ds*1000;
        m = round(mean(ds(:,1:4)),1);
        s = round(std(ds(:,1:4)),1);
        
        % t8-t5, time until feedback display (Python)
        ds_t8t5 = tv(startScan + 1:maxCount, 9) - tv(startScan + 1:maxCount, 6);
        % t10-t8, display feedback time (Matlab)
        ds_t10t8 = tv(startScan + 1:maxCount, 16) - tv(startScan + 1:maxCount, 9);

        m(5) = round(mean(ds_t8t5)*1000,1);
        s(5) = round(std(ds_t8t5)*1000,1);
        m(6) = round(mean(ds_t10t8)*1000,1);
        s(6) = round(std(ds_t10t8)*1000,1);
              
        % Matlab PTB Helper absolute display time
        % for feedback
        m(7) = round(mean(tv(startScan + 1:maxCount, end))*1000,1);
        s(7) = round(std(tv(startScan + 1:maxCount, end))*1000,1);
                
        disp('Durations mean and std (msec.):')
        fprintf('\tt2-t1\tt3-t2\tt4-t3\tt5-t4\tt8-t5\tt10-t8\ttAbs(fb)\n')
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            m(1), m(2), m(3), m(4), m(5), m(6), m(7))
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            s(1), s(2), s(3), s(4), s(5), s(6), s(7))

        % Total display time, here, equal for instruction and feedback.
        ds_t8t5_ms = ds_t8t5 + ds_t10t8;
        m_fb_displ = round(mean(ds_t8t5_ms)*1000,1); % t8-t5 in the ms
        s_fb_displ = round(std(ds_t8t5_ms)*1000,1);
        m_instr_displ = 0;
        s_instr_displ = 0;
        
        elapsedTime = tv(startScan + 1:maxCount, 14)*1000;
        
    elseif strcmp(nfbType,'svmCont')
        % cumulative time stamps
        % 1st column is trigger-pulse time, not taken into account here
        ts = tv(startScan + 1:maxCount, 2:6) - repmat(tv(startScan + 1:maxCount, 2), 1, 5);
        ts(ts<0)=0;
        % msec
        ts = ts*1000;
    
        % time stamp differences
        % 1st column is trigger-pulse time, not taken into account here
        ds = tv(startScan + 1:maxCount, 3:6) - tv(startScan + 1:maxCount, 2:5);
        ds(ds<0) = 0;
        % msec
        ds = ds*1000;
        m = round(mean(ds(:,1:4)),1);
        s = round(std(ds(:,1:4)),1);
        
        % t7-t6, instruction display time (Python)
        ds_t7t6 = tv(startScan + 1:maxCount, 8) - tv(startScan + 1:maxCount, 7);
        % t8-t5, feedback display time (Python)
        ds_t8t5 = tv(startScan + 1:maxCount, 9) - tv(startScan + 1:maxCount, 6);
        
        m(5) = round(mean(ds_t7t6)*1000,1);
        s(5) = round(std(ds_t7t6)*1000,1);
        m(6) = round(mean(ds_t8t5)*1000,1);
        s(6) = round(std(ds_t8t5)*1000,1);
               
        disp('Durations mean and std (msec.):')
        fprintf('\tt2-t1\tt3-t2\tt4-t3\tt5-t4\tt7-t6\tt8-t5\n')
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            m(1), m(2), m(3), m(4), m(5), m(6))
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            s(1), s(2), s(3), s(4), s(5), s(6))
        
        % Total display time, here, just sending out the value using UDP.
        m_fb_displ = m(5); % t8-t5 in the ms
        s_fb_displ = s(5);
        m_instr_displ = [];
        s_instr_displ = [];
                
        elapsedTime = tv(startScan + 1:maxCount, 14)*1000;
        
    elseif strcmp(nfbType,'pscInt')
        % get instritions and FB display indices
        indCond = find(P.vectEncCond~=3);
        indFB = find(P.vectEncCond==3);
        % cumulative time stamps
        % 1st column is trigger-pulse time, not taken into account here
        ts = tv(startScan + 1:maxCount, 2:6) - repmat(tv(startScan + 1:maxCount, 2), 1, 5);
        ts(ts<0)=0;
        % msec
        ts = ts*1000;
    
        % time stamp differences
        % 1st column is trigger-pulse time, not taken into account here
        ds = tv(startScan + 1:maxCount, 3:6) - tv(startScan + 1:maxCount, 2:5);
        ds(ds<0) = 0;
        % msec
        ds = ds*1000;
        m = round(mean(ds(:,1:4)),1);
        s = round(std(ds(:,1:4)),1);
        
        % t7-t6, time until instruction and feedback display (Python)
        ds_t7t6_instr = tv(startScan + indCond, 8) - tv(startScan + indCond, 7);
        ds_t7t6_fb = tv(startScan + indFB, 9) - tv(startScan + indFB, 7);
        % t9-t7, display instruction time (Matlab)
        ds_t9t7_instr = tv(startScan + indCond, 15) - tv(startScan + indCond, 8);
        % t9-t7, display feedback time (Matlab)
        ds_t9t7_fb = tv(startScan + indFB, 16) - tv(startScan + indFB, 9);
                      
        m(5) = round(mean(ds_t7t6_instr)*1000,1);
        s(5) = round(std(ds_t7t6_instr)*1000,1);
        m(6) = round(mean(ds_t7t6_fb)*1000,1);
        s(6) = round(std(ds_t7t6_fb)*1000,1);
        
        m(7) = round(mean(ds_t9t7_instr)*1000,1);
        s(7) = round(std(ds_t9t7_instr)*1000,1);
        m(8) = round(mean(ds_t9t7_fb)*1000,1);
        s(8) = round(std(ds_t9t7_fb)*1000,1);
        
        % Matlab PTB Helper absolute display time
        % for instruction
        m(9) = round(mean(tv(startScan + indCond, 17))*1000,1);
        s(9) = round(std(tv(startScan + indCond, 17))*1000,1);
        % for feedback
        m(10) = round(mean(tv(startScan + indFB, 18))*1000,1);
        s(10) = round(std(tv(startScan + indFB, 18))*1000,1);
                
        disp('Durations mean and std (msec.):')
        fprintf('\tt2-t1\tt3-t2\tt4-t3\tt5-t4\tt7-t6(in)\tt7-t6(fb)\tt9-t7(in)\tt9-t7(fb)\ttAbs(in)\ttAbs(fb)\n')
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            m(1), m(2), m(3), m(4), m(5), m(6), m(7), m(8), m(9), m(10))
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            s(1), s(2), s(3), s(4), s(5), s(6), s(7), s(8), s(9), s(10))
        
        % Total display time, here, NOT equal for instruction and feedback.
        ds_t7t6_ms_instr = ds_t9t7_instr + ds_t7t6_instr;
        ds_t7t6_ms_fb = ds_t9t7_fb + ds_t7t6_fb;
        m_fb_displ = round(mean(ds_t7t6_ms_fb)*1000,1); % t8-t5 in the ms
        s_fb_displ = round(std(ds_t7t6_ms_fb)*1000,1);
        m_instr_displ = round(mean(ds_t7t6_ms_instr)*1000,1); % t7-t6 in the ms
        s_instr_displ = round(std(ds_t7t6_ms_instr)*1000,1);
        
        elapsedTime = tv(startScan + indCond, 14)*1000;
        
    elseif strcmp(nfbType,'dcmInt')
        % get instritions and FB display indices
        indCond = find(P.vectEncCond~=3 & P.vectEncCond~=4);
        indFB = find(P.vectEncCond==4);
        
        % cumulative time stamps
        % 1st column is trigger-pulse time, not taken into account here
        ts = tv(startScan + 1:maxCount, 2:5) - repmat(tv(startScan + 1:maxCount, 2), 1, 4);
        ts(ts<0)=0;
        % msec
        ts = ts*1000;
        
        % time stamp differences
        % 1st column is trigger-pulse time, not taken into account here
        ds = tv(startScan + 1:maxCount, 3:5) - tv(startScan + 1:maxCount, 2:4);
        ds(ds<0) = 0;
        % msec
        ds = ds*1000;
               
        m = round(mean(ds(indCond,1:3)),1);
        s = round(std(ds(indCond,1:3)),1);
        mx = max(ds(:,1:3));
               
        % t5
        indEndFBcomput = find(tv(:, 6) > 0);
        endFBcomput = tv(indEndFBcomput(2:end), 6);
        % t4
        endSTPreprComput = tv(indEndFBcomput(2:end), 5);
        % t5-t4
        m(4) = round(mean(endFBcomput - endSTPreprComput)*1000,1);
        s(4) = round(std(endFBcomput - endSTPreprComput)*1000,1);
       
        % t7-t6, time until instruction display (Python)
        ds_t7t6 = tv(startScan + 1:maxCount, 8) - tv(startScan + 1:maxCount, 7);
        % t9-t6, display instruction time (Matlab)
        % For nfb, this time implies flashing specified in
        % displayFeedback.m, i.e pause(randi([600,800])/1000);
        % Note that time t5 is provided ass soon as the feedback is
        % estimated, i.e. within the blank period, however, here we are
        % interested in time spent to display the feedback value.
        ds_t9t7 = tv(startScan + 1:maxCount, 10) - tv(startScan + 1:maxCount, 8);
                      
        m(5) = round(mean(ds_t7t6(indCond))*1000,1);
        s(5) = round(std(ds_t7t6(indCond))*1000,1);
        m(6) = round(mean(ds_t7t6(indFB))*1000,1);
        s(6) = round(std(ds_t7t6(indFB))*1000,1);
        
        m(7) = round(mean(ds_t9t7(indCond))*1000,1);
        s(7) = round(std(ds_t9t7(indCond))*1000,1);
        m(8) = round(mean(ds_t9t7(indFB))*1000,1);
        s(8) = round(std(ds_t9t7(indFB))*1000,1);
        
        % Matlab PTB Helper absolute display time
        % for instruction
        m(9) = round(mean(tv(startScan + indCond, 15))*1000,1);
        s(9) = round(std(tv(startScan + indCond, 15))*1000,1);
        % for feedback
        m(10) = round(mean(tv(startScan + indFB, 15))*1000,1);
        s(10) = round(std(tv(startScan + indFB, 15))*1000,1);
        
        disp('Durations - mean, std, max (msec.):')
        fprintf('\tt2-t1\tt3-t2\tt4-t3\tt5-t4\tt7-t6(in)\tt7-t6(fb)\tt9-t7(in)\tt9-t7(fb)\ttAbs(in)\ttAbs(fb)\n')
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            m(1), m(2), m(3), m(4), m(5), m(6), m(7), m(8), m(9), m(10))
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            s(1), s(2), s(3), s(4), s(5), s(6), s(7), s(8), s(9), s(10))
      
        fprintf('\t%5.1f\t%5.1f\t%5.1f\n', mx(1), mx(2), mx(3))
        
        % DCM times t11, t12
        startDcm = tv(tv(:, 12) > 0, 12);
        endDcm = tv(tv(:, 13) > 0, 13);
        startDcm = startDcm(2:end);
        endDcm = endDcm(2:end);
        resDcm = endDcm - startDcm;
        
        % Total display time, here, NOT equal for instruction and feedback.
        ds_t9t6_ms = ds_t9t7 + ds_t7t6;
        m_fb_displ = round(mean(ds_t9t6_ms(indFB))*1000,1); % t8-t5 in the ms
        s_fb_displ = round(std(ds_t9t6_ms(indFB))*1000,1);
        m_instr_displ = round(mean(ds_t9t6_ms(indCond))*1000,1); % t7-t6 in the ms
        s_instr_displ = round(std(ds_t9t6_ms(indCond))*1000,1);
       
        fprintf('DCM calculation time (sec.) mean = %f, std = %f\n', round(mean(resDcm),1), round(std(resDcm),1))
              
        elapsedTime = [tv(startScan + indCond, 14)]*1000;
    
    elseif strcmp(nfbType,'task')
        % cumulative time stamps
        % 1st column is trigger-pulse time, not taken into account here
        ts = tv(startScan + 1:maxCount, 2:6) - repmat(tv(startScan + 1:maxCount, 2), 1, 5);
        ts(ts<0)=0;
        % msec
        ts = ts*1000;
    
        % time stamp differences
        % 1st column is trigger-pulse time, not taken into account here
        ds = tv(startScan + 1:maxCount, 3:6) - tv(startScan + 1:maxCount, 2:5);
        ds(ds<0) = 0;
        % msec
        ds = ds*1000;
        m = round(mean(ds(:,1:4)),1);
        s = round(std(ds(:,1:4)),1);
              
        % Matlab PTB Helper absolute display time
        % for feedback
        m(7) = round(mean(tv(startScan + 1:maxCount, 16))*1000,1);
        s(7) = round(std(tv(startScan + 1:maxCount, 16))*1000,1);
                
        disp('Durations mean and std (msec.):')
        fprintf('\tt2-t1\tt3-t2\tt4-t3\tt5-t4\n')
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            m(1), m(2), m(3), m(4))
        fprintf('\t%5.1f\t%5.1f\t%5.1f\t%5.1f\n', ...
            s(1), s(2), s(3), s(4))
                
        % No nfb display in task
        m_fb_displ = 0;
        s_fb_displ = 0;
        m_instr_displ = 0;
        s_instr_displ = 0;
        
        elapsedTime = tv(startScan + 1:maxCount, 14)*1000;
        
    elseif strcmp(nfbType,'autoRtqa')
        % cumulative time stamps
        % 1st column is trigger-pulse time, not taken into account here
        ts = tv(startScan + 1:maxCount, 2:6) - repmat(tv(startScan + 1:maxCount, 2), 1, 5);
        ts(ts<0)=0;
        % msec
        ts = ts*1000;
        
        % time stamp differences
        % 1st column is trigger-pulse time, not taken into account here
        ds = tv(startScan + 1:maxCount, 3:5) - tv(startScan + 1:maxCount, 2:4);
        ds(ds<0) = 0;
        % msec
        ds = ds*1000;
        m = round(mean(ds(:,1:3)),1);
        s = round(std(ds(:,1:3)),1);
                
        disp('Durations mean and std (msec.):')
        fprintf('\tt2-t1\tt3-t2\tt4-t3\t\n')
        fprintf('\t%5.1f\t%5.1f\t%5.1f\n', ...
            m(1), m(2), m(3))
        fprintf('\t%5.1f\t%5.1f\t%5.1f\n', ...
            s(1), s(2), s(3))
        
        elapsedTime = tv(startScan + 1:maxCount, 14)*1000;
        
    end
    
    if exist('m_fb_displ','var')
        fprintf('Display feedback time (msec.) mean = %f, std = %f\n', m_fb_displ, s_fb_displ)
    end
    if exist('m_instr_displ','var')
        fprintf('Display instruction time (msec.) mean = %f, std = %f\n', m_instr_displ, s_instr_displ)
    end
    fprintf('Elapsed time (msec.) mean = %f, std = %f\n', round(mean(elapsedTime),1), round(std(elapsedTime),1))

    
