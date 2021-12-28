function offlineImageSwitch

    P = evalin('base', 'P');
    isShowRtqaVol = evalin('base', 'isShowRtqaVol');
    mainLoopData = evalin('base', 'mainLoopData');
    rtQA_matlab = evalin('base', 'rtQA_matlab');
    rtQAMode = evalin('base', 'rtQAMode');
    dimVol = mainLoopData.dimVol;

    if isShowRtqaVol

        ROIs = evalin('base', 'ROIs');
        indx = ROIs(end).voxelIndex;
        rtqaVol = rtQA_matlab.rtqaVol;
        if ~rtQAMode || P.isAutoRTQA
            rtqaVol(indx) = rtQA_matlab.snrData.snrVol(indx);
        else
            rtqaVol(indx) = rtQA_matlab.cnrData.cnrVol(indx);
        end

        fname = strrep(P.memMapFile, 'shared', 'RTQAVol');
        m_out = memmapfile(fname, 'Writable', true, 'Format',  {'double', dimVol, 'rtQAVol'});
        m_out.Data.rtQAVol = rtqaVol;
        
    end

end
