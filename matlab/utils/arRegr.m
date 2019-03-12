function [dataOut] = arRegr(a, dataIn)
% Function for AR(1) filtering.
%
% input:
% a          - alpha 
% dataIn     - input matrix
% 
% output: 
% dataOut    - output matrix
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Yury Koush, Dimitri Van De Ville

for col = 1:size(dataIn,2)   
    for t = 1:size(dataIn,1)
        if t == 1
            dataOut(t,col) = (1-a) * dataIn(t,col);
        else
            dataOut(t,col) = dataIn(t,col) - a * dataOut(t-1,col);
        end
    end
end

%figure,plot(dataIn), hold on, plot(dataOut,'.-')