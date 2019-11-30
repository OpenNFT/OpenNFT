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
        self.meanFD = 0
        self.md = [0]
        self.meanMD = 0

        self.excFD = [0, 0]
        self.excVD = 0

        self.excFDIndexes_1 = np.array([-1])
        self.excFDIndexes_2 = np.array([-1])
        self.excMDIndexes = np.array([-1])

                
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
        self.fd = np.append(self.fd, self._ij_FD(i-1, i))
        self.meanFD = self.meanFD + (self.fd[i] - self.meanFD) / i

        if self.fd[i] >= self.threshold[1]:
           self.excFD[0] += 1

           if self.excFDIndexes_1[-1] == -1:
               self.excFDIndexes_1 = [i - 1]
           else:
               self.excFDIndexes_1 = np.append(self.excFDIndexes_1, i - 1)

           if self.fd[i] >= self.threshold[2]:
              self.excFD[1] += 1

              if self.excFDIndexes_2[-1] == -1:
                  self.excFDIndexes_2 = [i - 1]
              else:
                  self.excFDIndexes_2 = np.append(self.excFDIndexes_2, i - 1)

    def micro_displacement(self):

        n = len(self.data) - 1
        rmsDisp = 0;

        for i in range(3):
            rmsDisp += self.data[n, i]**2

        rmsDisp = np.sqrt(rmsDisp)

        self.md = np.append(self.md, abs(self.md[-1]-rmsDisp))
        self.meanMD = self.meanMD + (self.md[-1] - self.meanMD) / n

        if self.md[n] >= self.threshold[0]:
            self.excVD += 1
            if self.excMDIndexes[-1] == -1:
                self.excMDIndexes = [ n-1 ]
            else:
                self.excMDIndexes = np.append(self.excMDIndexes, n-1)


    def calc_mc_plots(self, data):

        self.data = np.vstack((self.data,data))
        self.micro_displacement()
        self.all_fd()

    def draw_mc_plots(self, mdFlag, trPlotitem, rotPlotitem, fdPlotitem):

        x = np.arange(1, self.data.shape[0] + 1, dtype=np.float64)

        trPlotitem.clear()
        rotPlotitem.clear()
        fdPlotitem.clear()

        for i in range(0, 3):
            trPlotitem.plot(x=x, y=self.data[:, i], pen=c.PLOT_PEN_COLORS[i], name=self.names[i])

        for i in range(3, 6):
            rotPlotitem.plot(x=x, y=self.data[:, i], pen=c.PLOT_PEN_COLORS[i], name=self.names[i])

        if mdFlag:
            fdPlotitem.plot(x=x, y=self.md, pen=c.PLOT_PEN_COLORS[0], name='MD')
            fdPlotitem.plot(x=np.arange(0, self.xmax, dtype=np.float64), y=self.threshold[0] * np.ones(self.xmax),
                            pen=c.PLOT_PEN_COLORS[2], name='thr')
        else:
            fdPlotitem.plot(x=x, y=self.fd, pen=c.PLOT_PEN_COLORS[0], name='FD')
            thresholds = self.threshold[1:3]
            for i, t in enumerate(thresholds):
                fdPlotitem.plot(x=np.arange(0, self.xmax, dtype=np.float64), y=float(t) * np.ones(self.xmax),
                                pen=c.PLOT_PEN_COLORS[i + 1], name='thr' + str(i))

