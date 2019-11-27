function [isPSC, isDCM, isSVM, isIGLM] = getFlagsType(P)
% Function to set feedback type and iGLM flags.
%
% input:
% P - parameter structure
%
% output:
% flags
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Artem Nikonorov, Yury Koush

isIGLM = false;
isSVM = false;
isPSC = false;
isDCM = false;

if strcmp(P.Type, 'DCM')
    isDCM = true;
    isIGLM = true;
elseif strcmp(P.Type, 'PSC')
    isPSC = true;
    isIGLM = true;
elseif strcmp(P.Type, 'SVM')
    isSVM = true;
    isIGLM = true;
elseif strcmp(P.Type, 'None')
    isIGLM = true;
end

