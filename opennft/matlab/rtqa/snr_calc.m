function [ snrVol, meanNonSmoothed, m2NonSmoothed, meanSmoothed, m2Smoothed ] = snr_calc( iteration, vol, volSmoothed, meanNonSmoothed, m2NonSmoothed, meanSmoothed, m2Smoothed, isSmoothed )
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
    n = double(iteration);
    shape = size(vol);
    snrVol = zeros(shape);
    if isempty(meanNonSmoothed) & isempty(m2NonSmoothed) & isempty(meanSmoothed) & isempty(m2Smoothed)
        meanNonSmoothed = vol;
        m2NonSmoothed = zeros(shape);
        meanSmoothed = volSmoothed;
        m2Smoothed = zeros(shape);
        return;
    end;

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

    if any(variance)
        if isSmoothed
            snrVol = meanSmoothed ./ (variance.^.5);
        else
            snrVol = meanNonSmoothed ./ (variance.^.5);
        end        
    end

end

