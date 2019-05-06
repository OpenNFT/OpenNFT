function [ snrVol, mean, m2 ] = snr_calc( iteration, vol, mean, m2 )
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
    
    if isempty(mean) & isempty(m2)
        mean = vol;
        m2 = zeros(shape);
        return;
    end;
    
    meanPrev = mean;
    mean = mean + (vol - mean) / n;
    m2 = m2 + (vol - meanPrev).*(vol - mean);
    variance = m2 / (n-1);
    if any(variance)
        snrVol = mean ./ (variance.^.5);
    end
    
%     for i=1:shape(3)
%         mean(:,:,i) = mean(:,:,i) + (vol(:,:,i) - mean(:,:,i)) ./ n;
%         m2(:,:,i) = m2(:,:,i) + (vol(:,:,i) - meanPrev(:,:,i)).*(vol(:,:,i) - mean(:,:,i));
%         variance = m2(:,:,i) / (n-1);
%         if any(variance)
%             snrVol(:,:,i) = mean(:,:,i) ./ (variance.^.5);
%         end
%     end

end

