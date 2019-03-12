function [o] = matData2strData(x)
% Function fast converts Matlab data into a string.
% It is used to transfer medium-size data to Python.
%
% input:
% x - input uint8 matrix 
%
% output: 
% o - output string
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Artem Nikonorov

maxvalue = max(x(:));
required_digits = ceil(log(double(maxvalue + 1)) / log(10));
o = zeros(size(x, 1), required_digits); % initialize array of required size
for c = size(o,2) : -1 : 1
    o(:, c) = mod(x, 10);
    x = (x - o(:,c)) / 10;
end
o = char(o + '0');
o(:, required_digits + 1) = ';';
o = reshape(o', 1, size(o, 1) * (required_digits + 1));

