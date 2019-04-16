function evals = varsFromStruct(S, fieldNames, defaultValues)
% Function to load variables to workspace from structure.
%
% input:
% S - input structure
% fieldNames - cell structure of variable names
% defualtValues - default values for variables
% 
% output: 
% evals - output structure with fieldNames
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Artem Nikonorov

evals = '';
for i = 1:length(fieldNames)
    f = cell2mat(fieldNames(i));
    if isfield(S, f)
        val = S.(f);
    else
        val = cell2mat(defaultValues(i));
    end
    if ischar(val)
        val = ['''' val ''''];
    end
    evals = [evals [f, '=', num2str(val)] ';'];
end

