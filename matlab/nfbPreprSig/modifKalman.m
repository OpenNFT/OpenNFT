function [kalmOut, S, fPositDerivSpike, fNegatDerivSpike] = ...
    modifKalman(kalmTh, kalmIn, S, fPositDerivSpike, fNegatDerivSpike)
% Function to perform Kalman low-pass filtering and despiking
%
% input:
% kalmTh           - spike-detection threshold
% kalmIn           - input data
% S                - parameter structure
% fPositDerivSpike - counter for spikes with positive derivative
% fNegatDerivSpike - counter for spikes with negative derivative
% 
% output: 
% kalmOut          - filtered otuput
% S                - parameters structure
% fPositDerivSpike - counter for spikes with positive derivative
% fNegatDerivSpike - counter for spikes with negative derivative
%
% For generic aspects see: 
% Koush Y., Zvyagintsev M., Dyck M., Mathiak K.A., Mathiak K. (2012): 
% Signal quality and Bayesian signal processing in neurofeedback based on 
% real-time fMRI. Neuroimage 59:478-89.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

% Preset
A = 1;
H = 1;
I = 1;

% Kalman filter
S.x = A * S.x;
S.P = A * S.P * A' + S.Q;
K = S.P * H' * pinv( H * S.P * H' + S.R );
tmp_x = S.x;
tmp_p = S.P;
diff = K * (kalmIn - H * S.x);
S.x = S.x + diff;
S.P = (I - K * H) * S.P;

% spikes identification and correction
if abs(diff) < kalmTh
    kalmOut = H * S.x;
    fNegatDerivSpike = 0;
    fPositDerivSpike = 0;
else
    if diff > 0
        if  fPositDerivSpike < 1
            kalmOut = H * tmp_x;
            S.x = tmp_x;
            S.P = tmp_p;
            fPositDerivSpike = fPositDerivSpike + 1;
        else
            kalmOut = H * S.x;
            fPositDerivSpike = 0;
        end
    else
        if  fNegatDerivSpike < 1
            kalmOut = H * tmp_x;
            S.x = tmp_x;
            S.P = tmp_p;
            fNegatDerivSpike = fNegatDerivSpike + 1;
        else
            kalmOut = H * S.x;
            fNegatDerivSpike = 0;
        end
    end
end
