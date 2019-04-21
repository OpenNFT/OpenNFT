function fileName = initMemmap(fileName, newName, initData, ...
    dataType, refName, mmFormat)
% Function to initialize memory mapped files for data exchange with Python.
%
% input:
% newName  - new file name for the memory mapped file
% initData - data to write
% dataType - date type
% refName  - reference variable for memory mapped file
% mmFormat - memory map file format
% 
% output: 
% fileName - new memory map file name 
%__________________________________________________________________________
% Copyright (C) 2016-2019 OpenNFT.org
%
% Written by Artem Nikonorov

fileName = strrep(fileName, 'shared', newName);
fileID = fopen(fileName, 'w');
fwrite(fileID, initData, dataType);
fclose(fileID);
if nargin == 6
    m = memmapfile(fileName, 'Writable', true, 'Format', mmFormat);
else
    m = memmapfile(fileName, 'Writable', true);
end
assignin('base', refName, m)
