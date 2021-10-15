% This class can have properties which changes according to the progress
% TODO: consider less dynamic behaviour

classdef mutableClass < dynamicprops
    properties
        indN = 0 % counter set by user
    end
    
    properties (SetAccess = private)
        stageN = 0 % internal counter of stages which increases at certain indNs as specified in switchIndices
    end
    
    properties (Access = private)
        switchIndices = [] % specifies indNs when switching stages
    end
    
    methods
        function obj = mutableClass(switchIndices, varargin)
            % switchIndices is an array of indices
            % varargin (optional) is a pair(s) of inputs specifying property name and property value at each stage
            
            assert(numel(switchIndices)>0, '"switchIndices" has to have at least one index');
            
            obj.switchIndices = switchIndices;
            for v = 1:numel(varargin)/2
                obj.addProp(varargin{(v-1)*2+1:(v-1)*2+2});
            end
        end
        
        function set.indN(obj,val)
            obj.indN = val;
            if numel(obj.switchIndices) && obj.indN >= obj.switchIndices(1)
                obj.switchIndices(1) = [];
                obj.stageN = obj.stageN+1;
            end
        end
        
        function addProp(obj,propname,val)
            % propname is a string specifying property name
            % val is a cell of property value at each stage
            
            assert(iscell(val), '"%s": property value has to be a cell of values', propname)
            assert(numel(val) >= numel(obj.switchIndices), '"%s": property must have value for each %d stages', propname, numel(obj.switchIndices))
            if numel(val) > numel(obj.switchIndices)
                warning('"%s": property have more then %d values. Some values will not be used', propname, numel(obj.switchIndices)); 
            end
            
            function val = getProp(obj)
                if ~obj.stageN, val = [];
                else, val = obj.(propname){obj.stageN}; end
            end
            prop = obj.addprop(propname);
            prop.SetAccess = 'private';
            obj.(propname) = val;
            prop.GetMethod = @getProp;
        end
    end
end
