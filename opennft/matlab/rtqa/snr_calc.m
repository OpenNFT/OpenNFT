function [ snrData ] = snr_calc( iteration, volSmoothed, snrData, isSmoothed )
% Function to calculate Signal-to-Noise Ratio for volume
%
% input:
% iteration   - which volume is now processing
% volSmoothed - smoothed volume for processing
% snrData - structure with values of smoothed and non-smoothed mean, m2 and SNR values
%
% output:
% snrVol   - updated structure of SNR data
%
    
    meanSmoothed = snrData.meanSmoothed;
    m2Smoothed = snrData.m2Smoothed;
    
    shape = size(volSmoothed);
    snrData.snrVol = zeros(shape);
    if isempty(meanSmoothed)
        snrData.meanSmoothed = volSmoothed;
        snrData.m2Smoothed = zeros(shape);
        snrData.iteration = 1;
        return;
    end

    snrData.iteration = snrData.iteration + 1;
    n = double(snrData.iteration);
    
    meanPrev = meanSmoothed;
    meanSmoothed = meanSmoothed + (volSmoothed - meanSmoothed) / n;
    m2Smoothed = m2Smoothed + (volSmoothed - meanPrev).*(volSmoothed - meanSmoothed);
    variance = m2Smoothed / (n-1);
    snrData.snrVol = meanSmoothed ./ (variance.^.5);
    
    snrData.meanSmoothed = meanSmoothed;
    snrData.m2Smoothed = m2Smoothed;

end
