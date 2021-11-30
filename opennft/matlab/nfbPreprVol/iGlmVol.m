function [idxActVox, recTh, tTh, Cn, Dn, sigma2n, tn, neg_e2n, Bn, e2n] = ...
    iGlmVol(Cn, Dn, sigma2n, tn, Yn, n, nrBasFct, contr, basFct, ...
    pVal, recTh, tTh, spmMaskTh)
% Core function to compute incemental GLM.
%
% input:
% Cn         - matrix for Cholesky decomposition (Eq. 15)
% Dn         - sum of (Yn * Ft') at time n-1
% sigma2n    - reqursive sigma square estimate
% tn         - t-variate at time n
% Yn         - observation vector at time point n
% n          - time point
% nrBasFct   - number of basis functions
% contr      - contrast vector
% basFct     - basis functions, i.e. regressors
% pVal       - p-value
% recTh      - recursive threshold
% tTh        - t-variate estimate given p-value and df
% spmMaskTh  - (SPM.xM.TH) nVar x nScan matrix of analysis thresholds,
%              one per image
%
% output:
% idxActVox  - indices of identified activation voxels
% recTh      - updated recursive threshold
% tTh        - updated t-variate at time n
% Cn         - updated matrix for Cholesky decomposition (Eq. 15)
% Dn         - sum of (Yn * Ft') at time n
% sigma2n    - updated recursive sigma square estimate
% tn         - t-statistics at time n
% neg_e2n    - flag on negative mean scquare error
%
% Note, initialization, recursion and application is coded in preprVol.m
% Note, a handle for negative and zero e2n is introduced to stabilize the algorithm.
%
% For generic aspects and equation numbers see:
% Bagarinao, E., Matsuo, K., Nakai, T., Sato, S., 2003. Estimation of
% general linear model coefficients for real-time application. NeuroImage
% 19, 422-429.
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Adopted by Yury Koush, Dimitri Van De Ville

pTh = 1-pVal;
df = n-nrBasFct; % degrees of freedom
if n > nrBasFct+2
    tTh(n) = spm_invTcdf(pTh,df);
end

Ft = basFct(n,:)'; % basis function vector at time n
Dn = Dn + Yn * Ft'; % Eq. (17)
Cn = (n - 1) / n * Cn  + Ft * Ft' / n; % Eq. (18)
sigma2n = sigma2n + Yn .* Yn; % Eq. (9), without factor 1/n, see below
Bn = zeros(size(Dn));
e2n = zeros(size(sigma2n));

[Nn,p] = chol(Cn); % normalization matrix
if p == 0 && n > nrBasFct+2
    invNn = inv(Nn');
    An = Dn * invNn' / n; % Eq. (14)
    Bn = An * invNn; % Eq. (16)
    e2n = n / df * (sigma2n / n - sum(An .* An, 2)); % Eqs. (8,9,22)
    
    % handle negative e2n
    neg_e2n = find(e2n < 0.0);
    if ~isempty(neg_e2n)
        e2n(neg_e2n) = abs(e2n(neg_e2n));
    end
    
    % handle zero e2n
    zero_e2n = find(e2n == 0.0);
    if ~isempty(zero_e2n)
        e2n(zero_e2n) = 1e10;
    end
    
    eqContr = invNn * contr.pos; % equivalent positive contrast
    tn.pos = (An*eqContr) ./ sqrt(e2n / n .* (eqContr' * eqContr)); % Eq. (23)
    eqContr = invNn * contr.neg; % negative contrast
    tn.neg = (An*eqContr) ./ sqrt(e2n / n .* (eqContr' * eqContr)); % Eq. (23)
else
    neg_e2n = [];
end

% thresholding with analysis threshold
iglmActVox.pos = find(tn.pos > tTh(n));
iglmActVox.neg = find(tn.neg > tTh(n));

% statistical image masking, as set by SPM structure, see
% setupProcParams.m
recTh = recTh + spmMaskTh(n) * spmMaskTh(n); % cumulative sum of squares
spmActVox = sigma2n > recTh;
idxSPMAct = find(spmActVox);

% intersect of iGLM and SPM indexes
idxActVox.pos = intersect(iglmActVox.pos, idxSPMAct);
idxActVox.neg = intersect(iglmActVox.neg, idxSPMAct);
clear iglmActVox spmActVox
