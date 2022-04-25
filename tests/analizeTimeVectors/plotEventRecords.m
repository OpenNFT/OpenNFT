function plotEventRecords(tv, startScan, nfbType)
% This function plot output from analyzeEventRecorder for OpenNFT
            
    % t2-t1, volume reading
    figure; plot(tv(startScan+1:end,3)-tv(startScan+1:end,2));
    title("t2-t1: Volume reading");
    xlim([1 length(tv)-startScan])
    % t3-t2, volume processing
    figure; plot(tv(startScan+1:end,4)-tv(startScan+1:end,3));
    title("t3-t2: Volume processing");
    xlim([1 length(tv)-startScan])
    % t4-t3, signal processing
    figure; plot(tv(startScan+1:end,5)-tv(startScan+1:end,4)); 
    title("t4-t3: Signal processing"); 
    xlim([1 length(tv)-startScan])

    if strcmp(nfbType,'pscCont')

        % t8-t5, time until feedback display (Python)
        figure; plot(tv(startScan+1:end,9)-tv(startScan+1:end,6)); 
        title("t8-t5: Before feedback display (Python)");
        xlim([1 length(tv)-startScan])

        % t10-t8, display feedback time (Matlab)
        figure; plot(tv(startScan+1:end,16)-tv(startScan+1:end,9)); 
        title("t10-t8: Display feedback time (Matlab)");
        xlim([1 length(tv)-startScan])

        % Matlab PTB Helper absolute display time
        % for feedback        
        figure; plot(tv(startScan + 1:end, end)); 
        title("Absolute display feedback time (Matlab PTB Helper)");
        xlim([1 length(tv)-startScan])
        
    elseif strcmp(nfbType,'svmCont')

        % t7-t6, instruction display time (Python)
        figure; plot(tv(startScan+1:end,8)-tv(startScan+1:end,7)); 
        title("t7-t6: Instruction display time (Python)");
        xlim([1 length(tv)-startScan])

        % t8-t5, feedback display time (Python)
        figure; plot(tv(startScan+1:end,9)-tv(startScan+1:end,6)); 
        title("t8-t5: Feedback display time (Python)");
        xlim([1 length(tv)-startScan])
        
    elseif strcmp(nfbType,'pscInt')

    elseif strcmp(nfbType,'dcmInt')

        % t7-t6, time until instruction display (Python)
        ds_t7t6 = tv(startScan + 1:end, 8) - tv(startScan + 1:end, 7);
        ds_t7t6(ds_t7t6 < 0 ) = 0;
        figure; plot(ds_t7t6); 
        title("t7-t6: Before instruction display (Python)");
        xlim([1 length(tv)-startScan])

        % t9-t6, display instruction time (Matlab)
        figure; plot(tv(startScan+1:end,10)-tv(startScan+1:end,8)); 
        title("t9-t6: Display instruction time (Matlab)");
        xlim([1 length(tv)-startScan])

    
    elseif strcmp(nfbType,'task')

        % Matlab PTB Helper absolute display time
        % for feedback
        figure; plot(tv(startScan+1:end,16)); 
        title("Absolute display feedback time (Matlab PTB Helper)");
        xlim([1 length(tv)-startScan]) 

    end

    % Elapsed time
    figure; plot(tv(startScan+1:end,14)); 
    title("Elapsed time");
    xlim([1 length(tv)-startScan]) 

end