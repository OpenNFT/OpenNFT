function offlineImageSwitch

    P = evalin('base', 'P');
    isShowRtqaVol = evalin('base', 'isShowRtqaVol');
    mainLoopData = evalin('base', 'mainLoopData');
    rtQA_matlab = evalin('base', 'rtQA_matlab');
    rtQAMode = evalin('base', 'rtQAMode');
    dimVol = mainLoopData.dimVol;

    if isShowRtqaVol
       
        if ~rtQAMode || P.isRestingState
            % 0 - SNR mode, 2 - CNR mode
            outputVol = rtQA_matlab.snrData.snrVol;
        else
            outputVol = rtQA_matlab.cnrData.cnrVol;
        end

        ROIs = evalin('base', 'ROIs');
        indx = ROIs(end).voxelIndex;
        idx=ismember(1:numel(outputVol),indx);
        outputVol(~idx) = 0;
        outputVol = (outputVol./max(outputVol(:)))*255;

        fname = strrep(P.memMapFile, 'shared', 'RTQAVol');
        m_out = memmapfile(fname, 'Writable', true, 'Format',  {'double', dimVol, 'rtQAVol'});
        m_out.Data.rtQAVol = outputVol;
        
    end

end
