function analizeCaseResults(curDataPath, refDataPath)
% This function performs the functional test on the current run output
% comparing it with reference output data
%
% Usage example:
% testCaseResults('C:\_RT\rtData\NF_PSC\NF_Data_1\foo_1_proc_tsROIs.mat', ...
%    'C:\_RT\rtData\NF_PSC\RefData\foo_1_proc_tsROIs.mat');
%__________________________________________________________________________
% Copyright (C) 2016-2021 OpenNFT.org
%
% Written by Artem Nikonorov

curData = importdata(curDataPath);
refData = importdata(refDataPath);

[r, failIter] = ind2sub(size(curData), find(curData ~= refData > 0));
[r, iterCount] = size(curData);
if length(failIter) > 0
	failRatio = round(length(failIter) / iterCount * 100, 3);
	disp([mat2str(failRatio) '% tests failed on iterations: '])
	disp(failIter)
else
	disp('100% tests passed.')
end
