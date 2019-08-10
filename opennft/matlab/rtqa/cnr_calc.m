function [ cnrData ] = cnr_calc( index, vol, volSmoothed, cnrData, isSmoothed )

    shape = size(vol);
    cnrData.cnrVol = zeros(shape);
    
    basData = cnrData.basData;
    condData = cnrData.condData;
    
    if ismember(index,basData.indexesBas)
        if isempty(basData.mean)
            basData.mean = vol;
            basData.m2 = zeros(shape);
            basData.meanSmoothed = volSmoothed;
            basData.m2Smoothed = zeros(shape);
            return;
        end
        
        meanPrev = basData.mean;
        basData.iteration = basData.iteration + 1;
        
        basData.mean = basData.mean + (vol - basData.mean) / basData.iteration;
        basData.m2 = basData.m2 + (vol - meanPrev).*(vol - basData.mean);

        meanPrev = basData.meanSmoothed;
        
        basData.meanSmoothed = basData.meanSmoothed + (volSmoothed - basData.meanSmoothed) / basData.iteration;
        basData.m2Smoothed = basData.m2Smoothed + (volSmoothed - meanPrev).*(volSmoothed - basData.meanSmoothed);
        
    end
    
    if ismember(index,condData.indexesCond)
        if isempty(condData.mean)
            condData.mean = vol;
            condData.m2 = zeros(shape);
            condData.meanSmoothed = volSmoothed;
            condData.m2Smoothed = zeros(shape);
            return
        end
        
        meanPrev = condData.mean;
        condData.iteration = condData.iteration + 1;

        condData.mean = condData.mean + (vol - condData.mean) / condData.iteration;
        condData.m2 = condData.m2 + (vol - meanPrev).*(vol - condData.mean);

        meanPrev = condData.meanSmoothed;

        condData.meanSmoothed = condData.meanSmoothed + (volSmoothed - condData.meanSmoothed) / condData.iteration;
        condData.m2Smoothed = condData.m2Smoothed + (volSmoothed - meanPrev).*(volSmoothed - condData.meanSmoothed);

    end
    
    if ~isempty(condData.mean)
    
        if isSmoothed
            meanBas = basData.meanSmoothed;
            meanCond = condData.meanSmoothed;
            varianceBas = basData.m2Smoothed / (basData.iteration - 1);
            varianceCond = condData.m2Smoothed / (condData.iteration - 1);
        else
            meanBas = basData.mean;
            meanCond = condData.mean;
            varianceBas = basData.m2 / (basData.iteration - 1);
            varianceCond = condData.m2 / (condData.iteration - 1);
        end
               
        cnrData.cnrVol = (meanCond - meanBas) ./ ((varianceBas + varianceCond).^.5);
        
        % filtering
%         meanCNR = mean(cnrVol(:));
%         stdCNR = std(cnrVol(:));
%         
%         cnrVol = cnrVol - meanCNR;
%         cnrVol = cnrVol ./ stdCNR;
%         meanCNR = mean(cnrVol(:));
%         stdCNR = std(cnrVol(:));
%         
%         for i=1:shape(1)
%             for j=1:shape(2)
%                 for k=1:shape(3)
%                     if cnrVol(i,j,k) < meanCNR+stdCNR
%                         cnrVol(i,j,k) = 0;
%                     end
%                 end
%             end
%         end    
        
    end
        
    cnrData.basData = basData;
    cnrData.condData = condData;
    
end

