function [ snrData ] = snr_calc( iteration, vol, volSmoothed, snrData, isSmoothed )
% Function to calculate Signal-Noise Ratio for volume
% 
% input:
% iteration   - which volume is now processing
% vol - the volume for processing
% mean      - mean value of previous iterations
% m2      - the second moment of the signal
%
% output:
% snrVol   - SNR volume statistic
% mean  - the new mean value of the signal
% m2 - the new second moment of the signal
%
    
    meanSmoothed = snrData.meanSmoothed;
    m2Smoothed = snrData.m2Smoothed;
    meanNonSmoothed = snrData.meanNonSmoothed;
    m2NonSmoothed = snrData.m2NonSmoothed;
    
    shape = size(vol);
    snrData.snrVol = zeros(shape);
    if isempty(meanSmoothed)
        snrData.meanNonSmoothed = vol;
        snrData.m2NonSmoothed = zeros(shape);
        snrData.meanSmoothed = volSmoothed;
        snrData.m2Smoothed = zeros(shape);
        snrData.iteration = 1;
        return;
    end;

    snrData.iteration = snrData.iteration + 1;
    n = double(snrData.iteration);
    
    meanPrev = meanSmoothed;
    meanSmoothed = meanSmoothed + (volSmoothed - meanSmoothed) / n;
    m2Smoothed = m2Smoothed + (volSmoothed - meanPrev).*(volSmoothed - meanSmoothed);

    meanPrev = meanNonSmoothed;
    meanNonSmoothed = meanNonSmoothed + (vol - meanNonSmoothed) / n;
    m2NonSmoothed = m2NonSmoothed + (vol - meanPrev).*(vol - meanNonSmoothed);

    if isSmoothed
        variance = m2Smoothed / (n-1);
    else
        variance = m2NonSmoothed / (n-1);
    end

    if isSmoothed
        snrData.snrVol = meanSmoothed ./ (variance.^.5);
    else
        snrData.snrVol = meanNonSmoothed ./ (variance.^.5);
    end
    
    snrData.meanSmoothed = meanSmoothed;
    snrData.m2Smoothed = m2Smoothed;
    snrData.meanNonSmoothed = meanNonSmoothed;
    snrData.m2NonSmoothed = m2NonSmoothed;

end

