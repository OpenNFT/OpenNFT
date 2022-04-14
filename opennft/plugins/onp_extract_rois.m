function S = onp_extract_rois

ROIs = evalin('base', 'ROIs');
mainLoopData = evalin('base', 'mainLoopData');

R = false([ROIs(1).dim 0]);
for r = 1:numel(ROIs)
    roi = false(ROIs(r).dim);
    roi(ROIs(r).voxelIndex) = true;
    R(:,:,:,r) = roi;
end

map = reshape(mainLoopData.tn.pos,[size(R,1) size(R,2) size(R,3)]);
for r = 1:size(R,4)
    S(r) = mean(map(R(:,:,:,r)));
end
end