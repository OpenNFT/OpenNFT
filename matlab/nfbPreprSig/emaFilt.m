function [emaOut, filtInput] = emaFilt(a, emaIn, filtInput)
% Function toperform basic EMA high-pass filtering filtering to remove to
% remove signal drift.
%
% input:
% a         - alpha 
% emaIn     - current raw data
% filtInput - previous filtered data
% 
% output: 
% emaOut    - current filtered data
% filtInput - updated filtered data
%
% Note, EMA filtering is replaced with CGLM time-series processing.
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush

A = [a (1-a)];
filtInput = A*[filtInput;emaIn];
emaOut = emaIn - filtInput;
