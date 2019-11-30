function offlineImageSwitch

    P = evalin('base', 'P');
    isShowRtqaVol = evalin('base', 'isShowRtqaVol');
    mainLoopData = evalin('base', 'mainLoopData');
    rtQA_matlab = evalin('base', 'rtQA_matlab');
    rtQAMode = evalin('base', 'rtQAMode');

    dimVol = mainLoopData.dimVol;
    slNrImg2DdimX = mainLoopData.slNrImg2DdimX;
    slNrImg2DdimY = mainLoopData.slNrImg2DdimY;
    img2DdimX = mainLoopData.img2DdimX;
    img2DdimY = mainLoopData.img2DdimY;

    if isShowRtqaVol
       
        if ~rtQAMode || P.isRestingState
            % 0 - SNR mode, 2 - CNR mode
            outputVol = rtQA_matlab.snrData.snrVol;
        else
            outputVol = rtQA_matlab.cnrData.cnrVol;
        end

        fname = strrep(P.memMapFile, 'shared', 'RTQAVol');
        m_out = memmapfile(fname, 'Writable', true, 'Format',  {'double', prod(dimVol), 'rtQAVol'});
        m_out.Data.rtQAVol = double(outputVol(:));

        statMap2D = vol3Dimg2D(outputVol, slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY, dimVol);
        statMap2D = statMap2D-min(statMap2D(:));
        statMap2D = (statMap2D / max(statMap2D(:))) * 255;
        m_out =  evalin('base', 'mmStatMap');
        m_out.Data.statMap = uint8(statMap2D);
        assignin('base', 'statMap2D', statMap2D); 
        
    else          
                       
        m_out =  evalin('base', 'mmStatMap');
        m_out.Data.statMap = uint8(mainLoopData.statMap2D_pos);
        assignin('base', 'statMap2D', mainLoopData.statMap2D_pos);
        
        m_out =  evalin('base', 'mmStatMap_neg');
        m_out.Data.statMap_neg = uint8(mainLoopData.statMap2D_neg);
        assignin('base', 'statMap2D_neg', mainLoopData.statMap2D_neg);
        
    end


end

