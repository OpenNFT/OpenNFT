function flags = getFlagsType(P)
% Function to set feedback type and iGLM flags.
%
% input:
% P - parameter structure
%
% output:
% flags
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Artem Nikonorov, Yury Koush

flags.isDCM = strcmp(P.Type, 'DCM');
flags.isPSC = strcmp(P.Type, 'PSC');
flags.isSVM = strcmp(P.Type, 'SVM');
flags.isCorr = strcmp(P.Type, 'Corr');

flags.isNone = strcmp(P.Type, 'None');

flags.isIGLM = isfield(P,'isIGLM') && P.isIGLM;

