function S = onp_extract_rois

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');

R = logical(spm_read_vols(cell2mat(spm_vol(P.ROINames))));
map = reshape(mainLoopData.tn.pos,[size(R,1) size(R,2) size(R,3)]);
for r = 1:size(R,4)
    S(r) = mean(map(R(:,:,:,r)));
end
end