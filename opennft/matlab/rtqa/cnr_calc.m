function [ cnrData ] = cnr_calc( index, volSmoothed, cnrData )
% Function to calculate Contrast-to-Noise Ratio for volume
%
% input:
% iteration   - which volume is now processing
% volSmoothed - smoothed volume for processing
% cnrData - structure with values of smoothed and non-smoothed mean, m2, СNR values and baseline and condition indexes
%
% output:
% cnrVol   - updated structure of CNR data
%
    shape = size(volSmoothed);
    cnrData.cnrVol = zeros(shape);
    
    basData = cnrData.basData;
    condData = cnrData.condData;
    
    if ismember(index,basData.indexesBas)
        if basData.iteration == 0
            basData.meanSmoothed = volSmoothed;
            basData.m2Smoothed = zeros(shape);
            basData.iteration = basData.iteration + 1;
            cnrData.basData = basData;
        else
            basData.iteration = basData.iteration + 1;
            meanPrev = basData.meanSmoothed;

            basData.meanSmoothed = basData.meanSmoothed + (volSmoothed - basData.meanSmoothed) / basData.iteration;
            basData.m2Smoothed = basData.m2Smoothed + (volSmoothed - meanPrev).*(volSmoothed - basData.meanSmoothed);
        end
    end
    
    if ismember(index,condData.indexesCond)
        if condData.iteration == 0
            condData.meanSmoothed = volSmoothed;
            condData.m2Smoothed = zeros(shape);
            condData.iteration = condData.iteration + 1;
            cnrData.condData = condData;
        else
            condData.iteration = condData.iteration + 1;
            meanPrev = condData.meanSmoothed;
            condData.meanSmoothed = condData.meanSmoothed + (volSmoothed - condData.meanSmoothed) / condData.iteration;
            condData.m2Smoothed = condData.m2Smoothed + (volSmoothed - meanPrev).*(volSmoothed - condData.meanSmoothed);
        end
    end
    
    if condData.iteration > 0

        meanBas = basData.meanSmoothed;
        meanCond = condData.meanSmoothed;
        varianceBas = basData.m2Smoothed / (basData.iteration - 1);
        varianceCond = condData.m2Smoothed / (condData.iteration - 1);
           
        cnrData.cnrVol = (meanCond - meanBas) ./ ((varianceBas + varianceCond).^.5);
        
    end
        
    cnrData.basData = basData;
    cnrData.condData = condData;
    
end
