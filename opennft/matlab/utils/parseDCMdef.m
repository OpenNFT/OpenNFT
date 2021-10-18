function out = parseDCMdef(jsonfile)
% usage DCM = parseDCMdef(jsonfile)
%
% Takes in the protocol JSON file, parses the a,b,c,d arrays that
% specify the DCM topology and returns the DCM struct.
%
% EXPECTS: jsonfile {str} ..... path to JSON file containing a field named
%                               "dcmdef" containing target and opposed model
%                               definitions, roiNames and options
%                               (see example below)
%
% RETURNS: out {struct} ....... with fields 'target' and 'opposed', which
%                               are structs containing a,b,c,d fields and
%                               'roiNames' and 'options'
%                               (see example below)
%
% For information % on how a,b,c,d matrices encode topology, please consult
% DCM literature, e.g.,
%
%   Stephan KE, Kasper L, Harrison LM, et al., Nonlinear dynamic causal
%   models for fMRI, Neuroimage 2008;42(2):649–662.
%
%   K.J. Friston et al., Dynamic Causal Modeling,
%   NeuroImage 2003;19:1273–1302
%
%           ------------------------------------------------------
%
% Here is an example JSON definition of a set of two two-region DCMs.
%
%
%     {
%         "dcmdef": {
%
%             "target": {
%
%             "a": [[1, 0],
%                   [0,1]],
%
%             "b": [[[0,0],
%                    [0,0]],
%                   [[1,1],
%                    [1,1]]],
%
%             "c": [1,1],
%
%             "d": []
%                      },
%
%             "opposed": {
%
%                 "a": [[1, 1],
%                       [1,1]],
%
%                 "b": [[[1,1],
%                        [1,1]],
%                       [[0,0],
%                        [0,0]]],
%
%                 "c": [1,0],
%
%                 "d": []
%                     },
%
%             "roiNames": ["L-SMA", "Precentral-G"],
%
%             "options": {
%                 "nonlinear": 0,
%                 "two_state": 0,
%                 "stochastic": 0,
%                 "nograph": 1,
%                 "centre": 1
%             }
%
%          }
%     }
%
% This example JSON file will produce the following output:
%
% out =
%
%   struct with fields:
%
%      target: [1×1 struct]
%     opposed: [1×1 struct]
%    roiNames: {["L-SMA"]  ["Precentral-G"]}
%     options: [1x1 struct]
%
% Both structs contain a,b,c,d matrices as fields. If you wish, you can run
% the function on the example JSON above to inspect the fields further.
%
% Note: This function requires 'loadjson', which is part of the JSONLab
% toolbox (http://iso2mesh.sf.net/cgi-bin/index.cgi?jsonlab).
%
%
% Moritz Gruber, SNS Lab, May 2019
% -------------------------------------------------------------------------

% -- Load json file -------------------------------------------------------
try
    in = loadjson(jsonfile);
catch
    error('Invalid json file')
end

% -- Get options if specified ---------------------------------------------
try
    out.options = in.dcmdef.options;
catch
    out.options = makeDefaultOptions();
end

% -- Extract model definition of target and opposed model -----------------

for model = {'target','opposed'}
    
    fprintf('Parsing %s model definition...\n',model{:})
    
    % -- Get ABCD fields --------------------------------------------------
    try
        dcmdefRaw = in.dcmdef.(model{:});
    catch
        error(['The JSON file does not contain a field called dcmdef.%s. ' ...
               'Please consult the docstring for input format.'],model{:})
    end

    % -- Check for completeness and make fieldnames lower case -- %
    dcmdefRaw = makeFieldnamesLowercase(dcmdefRaw);

    fnamesSorted = fieldnames(dcmdefRaw);

    for fn = {'a','b','c'}

        if ~contains(fn,fnamesSorted)
            error('Field "%s" not specified.', fn{:})
        end

    end

    % -- Get and check dimensions -----------------------------------------

    nRegions = length(dcmdefRaw.a);
    nInputs  = max(size(dcmdefRaw.c));

    % -- Reshape b correctly -- %
    if iscell(dcmdefRaw.b) % 3-d arrays in JSON become cell arrays here

        try
            DCM.b = reshape(cell2mat(dcmdefRaw.b)',nRegions,nRegions,nInputs);
        catch
            error('DCM.b could not be reshaped. Please verify dimensions')
        end

    elseif isequal(size(dcmdefRaw.b), [nRegions nRegions])

        DCM.b = dcmdefRaw.b;

    else

        error('"b" has incorrect dimensions.')

    end
    
    if out.options.nonlinear

        % -- Reshape d correctly -- %
        if ~isempty(dcmdefRaw.d)

            if iscell(dcmdefRaw.d) % 3-d arrays in JSON become cell arrays here

                try
                    DCM.d = reshape(cell2mat(dcmdefRaw.d)',nRegions,nRegions,nRegions);
                catch
                    error('DCM.d could not be reshaped. Please verify dimensions.')
                end

            elseif isequal(size(dcmdefRaw.d), [nRegions nRegions])

                DCM.d = dcmdefRaw.d;

            end
        end
    end

    % -- Finish building output struct ------------------------------------
    DCM.a = dcmdefRaw.a;
    DCM.c = dcmdefRaw.c';
    
    % -- Pack up ----------------------------------------------------------
    out.(model{:}) = sortFieldnames(DCM);

end

% -- Get ROI names if specified -------------------------------------------

try
    out.roiNames = in.dcmdef.roiNames;
catch
    warning('No ROI names specified. Creating default names.')
    out.roiNames = makeDefaultRoiNames(nRegions);
end

end

% =========================== AUXILIARIES =================================

function outstruct = makeFieldnamesLowercase(instruct)

for fx = fieldnames(instruct)'
    outstruct.(lower(fx{:})) = instruct.(fx{:});
end

end

function outstruct = sortFieldnames(instruct)
% Sorts the fieldnames of the input struct alphabetically.

fnamesSorted = sort(fieldnames(instruct));

for fx = 1:length(fnamesSorted)
    outstruct.(fnamesSorted{fx}) = instruct.(fnamesSorted{fx});
end

end

function roiNames = makeDefaultRoiNames(nRegions)
% Returns a cell array {'ROI-1',...,'ROI-N'} where N is the number of ROIs.

roiNames = {};
for roi = 1:nRegions
    roiNames{end+1} = ['ROI-' num2str(roi)];
end

end

function options = makeDefaultOptions()
% Consult DCM or SPM documentation for an explBgStruction of those fields.
options.two_state  = 0;
options.stochastic = 0;
options.nograph    = 1;
options.centre     = 1;
end
