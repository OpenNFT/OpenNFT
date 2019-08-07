# Generic framewise displacement computation and plotting

import matlab
import numpy as np

import opennft.config as c


class FD:
    def __init__(self, xmax, module = None):
        self.module = module
        
        # names of the dofs
        self.names = ['X','Y','Z','pitch','roll','yaw', 'FD']

        self.mode = {'tr': ['tr', 'translational','tr_sa'], 'rot' : ['rot', 'rotational','rot_sa'], 'fd':['FD', 'fd','FD_sa']}
        
        self.plotBgColor = c.PLOT_BACKGROUND_COLOR
        
        k = np.array(list(matlab.double([[1e-05,1e-05,1e-05,1e-05,1e-05,1e-05]])))
        self.data = np.array(k).astype(np.float)
        
        self.radius = c.DEFAULT_FD_RADIUS
        self.threshold = c.DEFAULT_FD_THRESHOLDS

        self.xmax = xmax
        self.fd = 0
        self.vdCriteria = [0]

                
    # FD computation 
    def _di(self, i):
        return np.array(self.data[i][0:3])
    
    def _ri(self, i):
        return np.array(self.data[i][3:6])
    
    def _ij_FD(self,i,j): # displacement from i to j
        return sum(np.absolute(self._di(j)-self._di(i))) + \
              sum(np.absolute(self._ri(j)-self._ri(i))) * self.radius
              
    def all_fd(self):
       i = len(self.data)-1
       self.fd = np.append(self.fd, self._ij_FD(i-1,i))

    def Van_Dijk_criteria(self):

        n = len(self.vdCriteria) - 1
        rmsDisp = 0;

        for i in range(3):
            rmsDisp += self.data[n, i]**2

        rmsDisp = np.sqrt(rmsDisp)

        self.vdCriteria = np.append(self.vdCriteria, abs(self.vdCriteria[n]-rmsDisp))


    def draw_mc_plots(self, data, vdFlag, trPlotitem, rotPlotitem, fdPlotitem):

        self.data = np.vstack((self.data,data))
        x = np.arange(1, self.data.shape[0] + 1, dtype=np.float64)

        trPlotitem.clear()
        rotPlotitem.clear()
        fdPlotitem.clear()
        self.Van_Dijk_criteria()
        self.all_fd()

        for i in range(0, 3):
            trPlotitem.plot(x=x, y=self.data[:, i], pen=c.PLOT_PEN_COLORS[i], name=self.names[i])

        for i in range(3, 6):
            rotPlotitem.plot(x=x, y=self.data[:, i], pen=c.PLOT_PEN_COLORS[i], name=self.names[i])

        if vdFlag:
            fdPlotitem.plot(x=x, y=self.vdCriteria, pen=c.PLOT_PEN_COLORS[0], name='Micro displacement')
            fdPlotitem.plot(x=np.arange(0, self.xmax, dtype=np.float64), y=self.threshold[0] * np.ones(self.xmax),
                            pen=c.PLOT_PEN_COLORS[2], name='thr')
        else:
            fdPlotitem.plot(x=x, y=self.fd, pen=c.PLOT_PEN_COLORS[0], name='FD')
            thresholds = self.threshold[1:3]
            for i, t in enumerate(thresholds):
                fdPlotitem.plot(x=np.arange(0, self.xmax, dtype=np.float64), y=float(t) * np.ones(self.xmax),
                                pen=c.PLOT_PEN_COLORS[i + 1], name='thr' + str(i))

