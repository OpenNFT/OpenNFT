# -*- coding: utf-8 -*-
import numpy as np
import matlab
import multiprocessing as mp

from opennft import config
from scipy.io import savemat
from loguru import logger


class RTQACalculation(mp.Process):
    """Real-time quality assessment methods class
    """

    # --------------------------------------------------------------------------
    def __init__(self, input, output):

        mp.Process.__init__(self)
        self.input = input
        self.output = output

        # parent data transfer block
        sz = int(input["nr_rois"])
        self.nrROIs = sz
        self.first_snr_vol = config.FIRST_SNR_VOLUME

        if input["is_auto_rtqa"]:
            xrange = int(input["xrange"])
            self.indBas = 0
            self.indCond = 0
        else:
            lastInds = np.zeros((input["muster_info"]["condTotal"],))
            for i in range(input["muster_info"]["condTotal"]):
                lastInds[i] = input["muster_info"]["tmpCond" + str(i + 1)][-1][1]
            xrange = int(max(lastInds))
            self.indBas = np.array(input["ind_bas"]) - 1
            self.indCond = np.array(input["ind_cond"]) - 1

        self.xrange = xrange

        # main class data initialization block
        self.FD = np.array([])
        self.meanFD = 0
        self.MD = np.array([])
        self.meanMD = 0
        self.blockIter = 1
        self.excFD = [0, 0]
        self.excMD = 0
        self.excFDIndexes_1 = np.array([-1])
        self.excFDIndexes_2 = np.array([-1])
        self.excMDIndexes = np.array([-1])
        self.rsqDispl = np.array([0])
        self.mc_params = np.array([[1e-05,1e-05,1e-05,1e-05,1e-05,1e-05]]).astype(np.float)
        self.radius = config.DEFAULT_FD_RADIUS
        self.threshold = config.DEFAULT_FD_THRESHOLDS
        self.iterBas = 0
        self.iterCond = 0
        self.iteration = 0
        self.blockIter = 0
        self.noRegBlockIter = 0
        self.rMean = np.zeros((sz, xrange))
        self.m2 = np.zeros((sz, xrange))
        self.rVar = np.zeros((sz, xrange))
        self.rSNR = np.zeros((sz, xrange))
        self.rNoRegMean = np.zeros((sz, xrange))
        self.noRegM2 = np.zeros((sz, 1))
        self.rNoRegVar = np.zeros((sz, xrange))
        self.rNoRegSNR = np.zeros((sz, xrange))
        self.meanBas = np.zeros((sz, xrange))
        self.varBas = np.zeros((sz, xrange))
        self.m2Bas = np.zeros((sz, 1))
        self.meanCond = np.zeros((sz, xrange))
        self.varCond = np.zeros((sz, xrange))
        self.m2Cond = np.zeros((sz, 1))
        self.rCNR = np.zeros((sz, xrange))
        self.glmProcTimeSeries = np.zeros((sz, xrange))
        self.posSpikes = dict.fromkeys(['{:d}'.format(x) for x in range(sz)], np.array(0))
        self.negSpikes = dict.fromkeys(['{:d}'.format(x) for x in range(sz)], np.array(0))
        self.rMSE = np.zeros((sz, xrange))
        self.DVARS = np.zeros((1, ))
        self.excDVARS = 0
        self.linTrendCoeff = np.zeros((sz, xrange))
        self.prevVol = np.array([])

        self.volume_data = {"mean_vol": [],
                            "m2_vol": [],
                            "var_vol": [],
                            "iter": 0,
                            "mean_bas_vol": [],
                            "m2_bas_vol": [],
                            "var_bas_vol": [],
                            "iter_bas": 0,
                            "mean_cond_vol": [],
                            "m2_cond_vol": [],
                            "var_cond_vol": [],
                            "iter_cond": 0
                            }

        self.output["rSNR"] = self.rSNR
        self.output["rCNR"] = self.rCNR
        self.output["rMean"] = self.rMean
        self.output["meanBas"] = self.meanBas
        self.output["meanCond"] = self.meanCond
        self.output["rVar"] = self.rVar
        self.output["varBas"] = self.varBas
        self.output["varCond"] = self.varCond
        self.output["glmProcTimeSeries"] = self.glmProcTimeSeries
        self.output["rMSE"] = self.rMSE
        self.output["linTrendCoeff"] = self.linTrendCoeff
        self.output["rNoRegSNR"] = self.rNoRegSNR
        self.output["DVARS"] = self.DVARS
        self.output["excDVARS"] = self.excDVARS
        self.output["mc_params"] = self.mc_params
        self.output["mc_offset"] = np.zeros((6,1))
        self.output["FD"] = self.FD
        self.output["MD"] = self.MD
        self.output["meanFD"] = self.meanFD
        self.output["meanMD"] = self.meanMD
        self.output["excFD"] = self.excFD
        self.output["excMD"] = self.excMD
        self.output["posSpikes"] = self.posSpikes
        self.output["negSpikes"] = self.negSpikes

    # --------------------------------------------------------------------------
    def run(self):

        np.seterr(divide='ignore', invalid='ignore')

        while not self.input["is_stopped"]:

            if self.input["data_ready"]:
                self.calculate_rtqa()

                self.output["rSNR"] = self.rSNR
                self.output["rCNR"] = self.rCNR
                self.output["rMean"] = self.rMean
                self.output["meanBas"] = self.meanBas
                self.output["meanCond"] = self.meanCond
                self.output["rVar"] = self.rVar
                self.output["varBas"] = self.varBas
                self.output["varCond"] = self.varCond
                self.output["glmProcTimeSeries"] = self.glmProcTimeSeries
                self.output["rMSE"] = self.rMSE
                self.output["linTrendCoeff"] = self.linTrendCoeff
                self.output["rNoRegSNR"] = self.rNoRegSNR
                self.output["DVARS"] = self.DVARS
                self.output["excDVARS"] = self.excDVARS
                self.output["mc_params"] = self.mc_params
                self.output["FD"] = self.FD
                self.output["MD"] = self.MD
                self.output["meanFD"] = self.meanFD
                self.output["meanMD"] = self.meanMD
                self.output["excFD"] = self.excFD
                self.output["excMD"] = self.excMD
                self.output["posSpikes"] = self.posSpikes
                self.output["negSpikes"] = self.negSpikes

                self.input["data_ready"] = False
                self.input["calc_ready"] = True

    # --------------------------------------------------------------------------
    def calculate_rtqa(self):

        iteration = self.input["iteration"]
        for i in range(self.nrROIs):
            self.linTrendCoeff[i][iteration] = self.input["beta_coeff"][i][-1]

        volume = np.memmap(self.input["volume"], dtype=np.float64, order="F")

        if self.input["is_new_dcm_block"]:
            self.blockIter = 0
            self.iterBas = 0
            self.iterCond = 0
            self.volume_data["iter"] = 0
            self.volume_data["iter_bas"] = 0
            self.volume_data["iter_cond"] = 0

        if iteration == 0:
            self.volume_data["mean_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["m2_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["var_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["mean_bas_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["m2_bas_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["var_bas_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["mean_cond_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["m2_cond_vol"] = np.zeros(volume.shape, order="F")
            self.volume_data["var_cond_vol"] = np.zeros(volume.shape, order="F")

        if iteration > self.first_snr_vol:
            self.calculate_rtqa_volume(volume, iteration)
        self.calculate_rtqa_ts(iteration)
        self.calculateDVARS(volume[self.input["wb_roi_indexes"]], iteration, self.input["is_new_dcm_block"])
        self.calc_mc()

    # --------------------------------------------------------------------------
    def calculate_rtqa_volume(self, volume, index_volume):

        output_vol, self.volume_data["mean_vol"], \
        self.volume_data["m2_vol"], self.volume_data["var_vol"] = self.snr(self.volume_data["mean_vol"],
                                                                           self.volume_data["m2_vol"],
                                                                           volume, self.volume_data["iter"])
        self.volume_data["iter"] += 1
        output_vol[self.input["wb_mask"]] = 0
        self.output["snr_vol"] = output_vol.reshape(self.input["dim"], order="F")

        if not self.input["is_auto_rtqa"]:
            output_vol, self.volume_data["mean_bas_vol"], self.volume_data["m2_bas_vol"], \
            self.volume_data["var_bas_vol"], self.volume_data["mean_cond_vol"], self.volume_data["m2_cond_vol"], \
            self.volume_data["var_cond_vol"] = self.cnr(self.volume_data["mean_bas_vol"],
                                                        self.volume_data["m2_bas_vol"],
                                                        self.volume_data["var_bas_vol"],
                                                        self.volume_data["mean_cond_vol"],
                                                        self.volume_data["m2_cond_vol"],
                                                        self.volume_data["var_cond_vol"],
                                                        volume, self.volume_data["iter_bas"], self.volume_data["iter_cond"], index_volume)

            output_vol[self.input["wb_mask"]] = 0
            self.output["cnr_vol"] = output_vol.reshape(self.input["dim"], order="F")

            if index_volume in self.indBas:
                self.volume_data["iter_bas"] += 1
            if index_volume in self.indCond:
                self.volume_data["iter_cond"] += 1

        self.input["rtqa_vol_ready"] = True

    # --------------------------------------------------------------------------
    def calculate_rtqa_ts(self, index_volume):

        for roi in range(self.nrROIs):

            data = self.input["raw_ts"][roi]

            # AR(1) was not applied.
            self.rSNR[roi, index_volume], \
            self.rMean[roi, index_volume], \
            self.m2[roi, index_volume], \
            self.rVar[roi, index_volume] = self.snr(self.rMean[roi, index_volume - 1],
                                                              self.m2[roi, index_volume - 1],
                                                              data, self.blockIter)

            # GLM regressors were estimated for time-series with AR(1) applied
            if self.input["no_reg_glm_ts"].any():
                data_noreg = self.input["no_reg_glm_ts"][roi]
                self.rNoRegSNR[roi, index_volume], self.rNoRegMean[roi, index_volume], \
                self.noRegM2[roi], \
                self.rNoRegVar[roi, index_volume] = self.snr(self.rNoRegMean[roi, index_volume - 1],
                                                             self.noRegM2[roi],
                                                             data_noreg, self.blockIter)

            if not self.input["is_auto_rtqa"]:
                self.rCNR[roi, index_volume], self.meanBas[roi, index_volume], \
                self.m2Bas[roi], self.varBas[roi, index_volume], \
                self.meanCond[roi, index_volume], self.m2Cond[roi], \
                self.varCond[roi, index_volume] = self.cnr(self.meanBas[roi, index_volume - 1], self.m2Bas[roi],
                                                           self.varBas[roi, index_volume-1],
                                                           self.meanCond[roi, index_volume - 1], self.m2Cond[roi],
                                                           self.varCond[roi, index_volume-1],
                                                           data, self.iterBas, self.iterCond,
                                                           index_volume)

        self.blockIter += 1
        if not self.input["is_auto_rtqa"]:
            if index_volume in self.indBas:
                self.iterBas += 1
            if index_volume in self.indCond:
                self.iterCond += 1

        data_glm = self.input["glm_ts"]
        data_proc = self.input["proc_ts"]
        data_pos_spikes = self.input["pos_spikes"]
        data_neg_spikes = self.input["neg_spikes"]

        self.calculateSpikes(data_glm, index_volume, data_pos_spikes, data_neg_spikes)
        self.calculateMSE(index_volume, data_glm, data_proc)

    # --------------------------------------------------------------------------
    def snr(self, rMean, m2, data, blockIter):
        """ Recursive SNR calculation

        :param rMean: previous mean value of input data
        :param m2: ptrvious squared mean difference of input data
        :param data: input data
        :param blockIter: iteration number
        :return: calculated rSNR, rMean, rM2 and rVariance
        """

        if blockIter:

            prevMean = rMean
            rMean = prevMean + (data - prevMean) / (blockIter + 1)
            m2 = m2 + (data - prevMean) * (data - rMean)
            rVar = m2 / blockIter
            rSNR = rMean / (rVar ** (.5))
            blockIter += 1

        else:

            rMean = data
            m2 = np.zeros(data.shape, order="F")
            rVar = np.zeros(data.shape, order="F")
            rSNR = np.zeros(data.shape, order="F")
            blockIter = 1

        if not isinstance(data, np.ndarray) and blockIter < 8:
            rSNR = 0

        return rSNR, rMean, m2, rVar,

    # --------------------------------------------------------------------------
    def cnr(self, meanBas, m2Bas, varBas, meanCond, m2Cond, varCond, data, iterBas, iterCond, indexVolume):
        """ Recursive time-series CNR calculation

        :param data: new value of raw time-series
        :param indexVolume: current volume index
        :param isNewDCMBlock: flag of new dcm block
        :return: calculated rCNR, rMeans, rM2s and rVariances
        """

        if indexVolume in self.indBas:
            if not iterBas:
                meanBas = data
                m2Bas = np.zeros(data.shape, order="F")
                varBas = np.zeros(data.shape, order="F")
                iterBas += 1

            else:
                prevMeanBas = meanBas
                meanBas = meanBas + (data - meanBas) / (iterBas + 1)
                m2Bas = m2Bas + (data - prevMeanBas) * (data - meanBas)
                varBas = m2Bas / iterBas
                iterBas += 1

        if indexVolume in self.indCond:
            if not iterCond:
                meanCond = data
                m2Cond = np.zeros(data.shape, order="F")
                varCond = np.zeros(data.shape, order="F")
                iterCond += 1
            else:
                prevMeanCond = meanCond
                meanCond = meanCond + (data - meanCond) / (iterCond + 1)
                m2Cond = m2Cond + (data - prevMeanCond) * (data - meanCond)
                varCond = m2Cond / iterCond
                iterCond += 1

        if iterCond:
            rCNR = (meanCond - meanBas) / (np.sqrt(varCond + varBas))
        else:
            rCNR = np.zeros(data.shape, order="F")

        return rCNR, meanBas, m2Bas, varBas, meanCond, m2Cond, varCond

    # --------------------------------------------------------------------------
    def _di(self, i):
        return np.array(self.mc_params[i][0:3])

    # --------------------------------------------------------------------------
    def _ri(self, i):
        return np.array(self.mc_params[i][3:6])

    # --------------------------------------------------------------------------
    def _ij_FD(self, i, j):  # displacement from i to j
        return sum(np.absolute(self._di(j) - self._di(i))) + \
               sum(np.absolute(self._ri(j) - self._ri(i))) * self.radius

    # --------------------------------------------------------------------------
    def all_fd(self):
        i = len(self.mc_params) - 1

        if not self.input["is_new_dcm_block"]:
            self.FD = np.append(self.FD, self._ij_FD(i - 1, i))
            self.meanFD = self.meanFD + (self.FD[-1] - self.meanFD) / (self.blockIter + 1)
        else:
            self.FD = np.append(self.FD, 0)
            self.meanFD = 0

        if self.FD[-1] >= self.threshold[1]:
            self.excFD[0] += 1

            if self.excFDIndexes_1[-1] == -1:
                self.excFDIndexes_1 = np.array([i - 1])
            else:
                self.excFDIndexes_1 = np.append(self.excFDIndexes_1, i - 1)

            if self.FD[-1] >= self.threshold[2]:
                self.excFD[1] += 1

                if self.excFDIndexes_2[-1] == -1:
                    self.excFDIndexes_2 = np.array([i - 1])
                else:
                    self.excFDIndexes_2 = np.append(self.excFDIndexes_2, i - 1)

    # --------------------------------------------------------------------------
    def micro_displacement(self):

        n = len(self.mc_params) - 1
        sqDispl = 0

        if not self.input["is_new_dcm_block"]:

            for i in range(3):
                sqDispl += self.mc_params[n, i] ** 2

            self.rsqDispl = np.append(self.rsqDispl, np.sqrt(sqDispl))

            self.MD = np.append(self.MD, abs(self.rsqDispl[-2] - self.rsqDispl[-1]))
            self.meanMD = self.meanMD + (self.MD[-1] - self.meanMD) / (self.blockIter + 1)

        else:
            self.MD = np.append(self.MD, 0)
            self.meanMD = 0

        if self.MD[-1] >= self.threshold[0]:
            self.excMD += 1
            if self.excMDIndexes[-1] == -1:
                self.excMDIndexes = np.array([n - 1])
            else:
                self.excMDIndexes = np.append(self.excMDIndexes, n - 1)

    # --------------------------------------------------------------------------
    def calc_mc(self):

        if self.input["iteration"] == 0:
            self.output["mc_offset"] = self.input["offset_mc"]
            self.mc_params = self.output["mc_offset"]
        else:
            self.mc_params = np.vstack((self.mc_params, self.input["mc_ts"]))
        self.micro_displacement()
        self.all_fd()

    # --------------------------------------------------------------------------
    def calculateSpikes(self, data, indexVolume, posSpikes, negSpikes):
        """ Spikes and GLM signal recording

        :param data: signal values after GLM process
        :param indexVolume: current volume index
        :param posSpikes: flags of positive spikes
        :param negSpikes: flags of negative spikes
        """

        sz, l = data.shape
        self.glmProcTimeSeries[:, indexVolume] = data[:, 0]

        for i in range(sz):
            if posSpikes[i] == 1:
                if self.posSpikes[str(i)].any():
                    self.posSpikes[str(i)] = np.append(self.posSpikes[str(i)], indexVolume)
                else:
                    self.posSpikes[str(i)] = np.array([indexVolume])
            if negSpikes[i] == 1 and l > 2:
                if self.negSpikes[str(i)].any():
                    self.negSpikes[str(i)] = np.append(self.negSpikes[str(i)], indexVolume)
                else:
                    self.negSpikes[str(i)] = np.array([indexVolume])

    # --------------------------------------------------------------------------
    def calculateMSE(self, indexVolume, inputSignal, outputSignal):
        """ Low pass filter performance estimated by recursive mean squared error

        :param indexVolume: current volume index
        :param inputSignal: signal value before filtration
        :param outputSignal: signal value after filtration

        """

        sz = inputSignal.size
        n = self.blockIter

        for i in range(sz):
            self.rMSE[i, indexVolume] = (n / (n + 1)) * self.rMSE[i, indexVolume - 1] + (
                        (inputSignal[i] - outputSignal[i]) ** 2) / (n + 1)

    # --------------------------------------------------------------------------
    def calculateDVARS(self, volume, index_volume, isNewDCMBlock):

        if self.prevVol.size == 0:
            dvars_diff = (volume / self.input["dvars_scale"]) ** 2
        else:
            dvars_diff = ((self.prevVol - volume) / self.input["dvars_scale"]) ** 2
        dvars_value = 100 * (np.mean(dvars_diff, axis=None)) ** .5

        self.prevVol = volume

        if index_volume == 0 or isNewDCMBlock:
            self.DVARS = np.append(self.DVARS, 0)
        else:
            self.DVARS = np.append(self.DVARS, dvars_value)

        if self.DVARS[-1] > config.DEFAULT_DVARS_THRESHOLD:
            self.excDVARS = self.excDVARS + 1

    # --------------------------------------------------------------------------
    def dataPacking(self):
        """ Packaging of python RTQA data for following save
        """

        tsRTQA = dict.fromkeys(['rMean', 'rVar', 'rSNR', 'rNoRegSNR',
                                'meanBas', 'varBas', 'meanCond', 'varCond', 'rCNR',
                                'excFDIndexes_1', 'excFDIndexes_2', 'excMDIndexes',
                                'FD', 'MD', 'DVARS', 'rMSE', 'snrVol', 'cnrVol'])

        tsRTQA['rMean'] = matlab.double(self.output["rMean"].tolist())
        tsRTQA['rVar'] = matlab.double(self.output["rVar"].tolist())
        tsRTQA['rSNR'] = matlab.double(self.output["rSNR"].tolist())
        tsRTQA['rNoRegSNR'] = matlab.double(self.output["rNoRegSNR"].tolist())
        tsRTQA['meanBas'] = matlab.double(self.output["meanBas"].tolist())
        tsRTQA['varBas'] = matlab.double(self.output["varBas"].tolist())
        tsRTQA['meanCond'] = matlab.double(self.output["meanCond"].tolist())
        tsRTQA['varCond'] = matlab.double(self.output["varCond"].tolist())
        tsRTQA['rCNR'] = matlab.double(self.output["rCNR"].tolist())
        tsRTQA['excFDIndexes_1'] = matlab.double(self.excFDIndexes_1.tolist())
        tsRTQA['excFDIndexes_2'] = matlab.double(self.excFDIndexes_2.tolist())
        tsRTQA['excMDIndexes'] = matlab.double(self.excMDIndexes.tolist())
        tsRTQA['FD'] = matlab.double(self.output["FD"].tolist())
        tsRTQA['MD'] = matlab.double(self.output["MD"].tolist())
        tsRTQA['DVARS'] = matlab.double(self.output["DVARS"].tolist())
        tsRTQA['rMSE'] = matlab.double(self.output["rMSE"].tolist())
        tsRTQA['snrVol'] = matlab.double(self.output["snr_vol"].tolist())
        tsRTQA['cnrVol'] = matlab.double(self.output["cnr_vol"].tolist())

        return tsRTQA