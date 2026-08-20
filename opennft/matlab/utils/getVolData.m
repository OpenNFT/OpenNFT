function [vol, mat, dim] = getVolData(dataType, fileName, indVol, useGetMAT, useTCPData)

P = evalin('base', 'P');
mainLoopData = evalin('base', 'mainLoopData');
if P.isGE
    GE_filelist = evalin('base', 'GE_filelist');
end

if useTCPData, tcp = evalin('base', 'tcp'); end

if isfield(mainLoopData,'matTemplMotCorr')
    matTemplMotCorr = mainLoopData.matTemplMotCorr;
    dimTemplMotCorr = mainLoopData.dimTemplMotCorr;
else
    matTemplMotCorr = [];
    dimTemplMotCorr = [];
end

vol = [];
dim = [];
mat = [];

switch dataType
    case 'DICOM'
        if useTCPData && (indVol > 1)
            while ~tcp.BytesAvailable, pause(0.01); end
            [hdr, vol] = tcp.ReceiveScan;
            dim = hdr.Dimensions;
            mat = hdr.mat;
        else
            while isempty(vol) || contains(lastwarn,'Suspicious fragmentary file')
                vol = double(dicomread(fileName));
            end
            if P.isDicomSiemensXA30
                % for new 4D Siemens XA30 data format
                if isempty(matTemplMotCorr)
                    dicomInfoVol = dicominfo(fileName);
                    dim = [double(dicomInfoVol.Rows), double(dicomInfoVol.Columns), double(dicomInfoVol.NumberOfFrames)];
                else
                    dim = dimTemplMotCorr;
                end
                vol = squeeze(vol);
                tmpData = zeros(dim);
                for i=1:dim(3)
                    tmpData(:,:,i) = imrotate(vol(:,:,i),-90);
                end
                vol = tmpData;
            else
                if isempty(matTemplMotCorr)
                    dicomInfoVol = dicominfo(fileName);
                    mxAct      = double(dicomInfoVol.AcquisitionMatrix(1));
                    if (mxAct == 0)
                        mxAct = double(dicomInfoVol.AcquisitionMatrix(3));
                    end
                    MatrixSizeX_Act = mxAct;
                    dim = [MatrixSizeX_Act, MatrixSizeX_Act, double(P.NrOfSlices)];
                else
                    dim = dimTemplMotCorr;
                end
                [slNrImg2DdimX, slNrImg2DdimY, img2DdimX, img2DdimY] = getMosaicDim(dim);
                vol = img2Dvol3D(vol, slNrImg2DdimX, slNrImg2DdimY, dim);
            end

            if useGetMAT && isempty(matTemplMotCorr)
                mat = getMAT(dicomInfoVol, dim, P);
            else
                mat = matTemplMotCorr;
            end

        end
        if P.isZeroPadding
            zeroPadVol = zeros(dim(1),dim(2),P.nrZeroPadVol);
            dim(3) = dim(3)+P.nrZeroPadVol*2;
            vol = cat(3, cat(3, zeroPadVol, dcmData), zeroPadVol);
        end
	case 'GE'
        % Get volume from bin
        if evalin('base', 'exist(''GE_bin_path'', ''var'')')
            binPath = evalin('base', 'GE_bin_path');
            
            mat = matTemplMotCorr;
            dim = dimTemplMotCorr;
            
            % Read bin file
            fid = fopen(binPath, 'r');
            
            % Read raw doubles. Inf implies "read until EOF"
            raw_data = fread(fid, Inf, 'double');
            fclose(fid);
            
            vol = reshape(raw_data, dim(1), dim(2), dim(3));
            
            % Clean up the workspace variable
            evalin('base', 'clear GE_bin_path');
            % Delete the actual file from disk
            if indVol > 0
				delete(binPath);
			end
            
        else
            error('CRITICAL: GE_bin_path missing. Python did not inject data.');
        end
        if P.isZeroPadding
            zeroPadVol = zeros(dim(1),dim(2),P.nrZeroPadVol);
            dim(3) = dim(3)+P.nrZeroPadVol*2;
            vol = cat(3, cat(3, zeroPadVol, vol), zeroPadVol);
        end
    case 'IMAPH'
        % Note, possibly corrupted Phillips rt data export
        vol  = spm_read_vols(spm_vol(fileName));
        % If necessary, flip rt time-series so that it matches the template
        % set in setupFirstVolume.m, setupProcParams.m, selectROI.m
        vol  = fliplr(vol);
        mat = matTemplMotCorr;
        dim = dimTemplMotCorr;
        if P.isZeroPadding
            zeroPadVol = zeros(dim(1),dim(2),P.nrZeroPadVol);
            dim(3) = dim(3)+P.nrZeroPadVol*2;
            vol = cat(3, cat(3, zeroPadVol, vol), zeroPadVol);
        end
    case 'NII'
        vol_info = spm_vol(fileName);
        mat = vol_info.mat;
        dim = vol_info.dim;
        vol = spm_read_vols(spm_vol(fileName));
        if P.isZeroPadding
            zeroPadVol = zeros(dim(1),dim(2),P.nrZeroPadVol);
            dim(3) = dim(3)+P.nrZeroPadVol*2;
            vol = cat(3, cat(3, zeroPadVol, vol), zeroPadVol);
        end
end

end