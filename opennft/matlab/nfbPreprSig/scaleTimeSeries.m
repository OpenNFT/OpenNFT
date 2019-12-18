function [outData, tmp_posMin, tmp_posMax] = ...
    scaleTimeSeries(inTimeSeries, indVol, lengthSlWind, ...
    initLim, tmp_posMin, tmp_posMax, P)
% Function to scale time-series.
%
% input:
% inTimeSeries - input cumulative time-series
% indVol       - volume(scan) index
% lengthSlWind - sliding window length 
% blockLength  - length of the vaselien condition block
% initLim      - initial time-series limits, see preprSig.m
% vectEncCond  - encoded vector of experimental conditions
% tmp_posMin   - recursive dynamic lower limit
% tmp_posMax   - recursive dynamic upper limit
%
% output: 
% outData       - scaled current time-series point
% tmp_posMin    - updated recursive dynamic lower limit
% tmp_posMax    - updated recursive dynamic upper limit
%
% Note, scaling based on sliding window is disabled using a very big 
% number of inclusive points, i.e. it is larger than a run. For algorithms
% involving sliding-window, the simulations and clear hypothesis are
% adviced, because of the very high influence on operant conditioning.
%
% For generic aspects see: 
% Koush Y., Ashburner J., Prilepin E., Ronald S., Zeidman P., Bibikov S., 
% Scharnowski F., Nikonorov A., Van De Ville D.: OpenNFT: An open-source
% Python/Matlab framework for real-time fMRI neurofeedback training based 
% on activity, connectivity and multivariate pattern analysis.(pending)
%
% Koush Y., Zvyagintsev M., Dyck M., Mathiak K.A., Mathiak K. (2012): 
% Signal quality and Bayesian signal processing in neurofeedback based on 
% real-time fMRI. Neuroimage 59:478-89.
% 
% Scharnowski F., Hutton C., Josephs O., Weiskopf N., Rees G. (2012): 
% Improving visual perception through neurofeedback. JofNeurosci,
% 32(49), 17830-17841. 
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

if indVol <21
    % max & min, Koush et al., 2012, Scharnowski et al., 2012
    tmp_max = max(inTimeSeries);
    tmp_min = min(inTimeSeries);
else
    % 5% of the length of the acquired tme-series
    sKalmanProcTimeSeries = sort(inTimeSeries);
    nrElem = round(0.05*length(sKalmanProcTimeSeries));
    tmp_max = median(sKalmanProcTimeSeries(end-nrElem:end));
    tmp_min = median(sKalmanProcTimeSeries(1:nrElem+1));
end
if ~P.isRestingState
    if (indVol<=P.basBlockLength) || (indVol < lengthSlWind)
        % First period or user defined time scaleTimeSeries
        % max
        if (tmp_max > initLim)
            tmp_posMax = tmp_max;
        else
            tmp_posMax = initLim;
        end
        if (tmp_min < -initLim)
            tmp_posMin = tmp_min;
        else
            tmp_posMin = -initLim;
        end
    else
        chk_max = max(inTimeSeries(indVol - lengthSlWind + 1:indVol));
        chk_min = min(inTimeSeries(indVol - lengthSlWind + 1:indVol));
        if (indVol>P.basBlockLength) && ~(P.vectEncCond(indVol)==P.vectEncCond(indVol-1))
            if (tmp_max > chk_max)
                tmp_posMax = chk_max;
            else
                tmp_posMax = tmp_max;
            end
            if (tmp_min < chk_min)
                tmp_posMin = chk_min;
            else
                tmp_posMin = tmp_min;
            end
        else
            if (inTimeSeries(indVol) > tmp_posMax)
                tmp_posMax = inTimeSeries(indVol);
            end
            if (inTimeSeries(indVol) < tmp_posMin)
                tmp_posMin = inTimeSeries(indVol);
            end
        end
    end
else
    if (tmp_max > initLim)
        tmp_posMax = tmp_max;
    else
        tmp_posMax = initLim;
    end
    if (tmp_min < -initLim)
        tmp_posMin = tmp_min;
    else
        tmp_posMin = -initLim;
    end
end
outData = (inTimeSeries(indVol) - tmp_posMin) / (tmp_posMax - tmp_posMin);
