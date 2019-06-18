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

                
    # FD computation 
    def _di(self, i):
        return np.array(self.data[i][0:3])
    
    def _ri(self, i):
        return np.array(self.data[i][3:6])
    
    def _ij_FD(self,i,j): # displacement from i to j
        return sum(np.absolute(self._di(j)-self._di(i))) + \
              sum(np.absolute(self._ri(j)-self._ri(i))) * self.radius
              
    def all_fd(self):
       fd = np.zeros(self.data.shape[0])
       for i in range(1, self.data.shape[0]):
           fd[i] = self._ij_FD(i-1,i)
       return fd

    def draw_mc_plots(self, init, outputSamples, plotitem, md):
        if not outputSamples:
            return
    
        # get data, compute X from data length
        k = np.array(outputSamples['motCorrParam'])
        self.data = np.array(k).astype(np.float)
        x = np.arange(1, self.data.shape[0] + 1, dtype=np.float64)
                    
        # retrieve plot information from openNFT
        mctrrot = plotitem
    
        # initialise plot
        if init:
            mctrrot.clear()
                        
            if md in self.mode['tr']:
                for i in range(0, 3):
                    mctrrot.plot(x=x, y=self.data[:, i], pen=c.PLOT_PEN_COLORS[i], name=self.names[i])
                        
            elif md in self.mode['rot']:
                for i in range(3, 6):
                    mctrrot.plot(x=x, y=self.data[:, i], pen=c.PLOT_PEN_COLORS[i], name=self.names[i])
                        
            elif md in self.mode['fd']:
                mctrrot.plot(x=x, y=self.all_fd(), pen=c.PLOT_PEN_COLORS[0], name='FD')
                for i,t in enumerate(self.threshold):
                    mctrrot.plot(x=np.arange(0,self.xmax, dtype=np.float64), y=float(t)*np.ones(self.xmax), pen=c.PLOT_PEN_COLORS[i+1], name='thr' + str(i))
                
            else:
                for i in range(0, 6):
                    mctrrot.plot(x=x, y=self.data[:, i],pen=c.PLOT_PEN_COLORS[i], name=self.names[i])

        if md in self.mode['tr']:
            for i,plt in enumerate(mctrrot.listDataItems()):
                plt.setData(x=x, y=self.data[:, i])
        
        elif md in self.mode['rot']:
            for i,plt in enumerate(mctrrot.listDataItems()):
                plt.setData(x=x, y=self.data[:, i+3])
        
        elif md in self.mode['fd']:
            for i,plt in enumerate(mctrrot.listDataItems()):
                if i == 0:
                    plt.setData(x=x, y=self.all_fd())
                else:
                    t = self.threshold[i-1]
                    plt.setData(x=np.arange(0,self.xmax, dtype=np.float64), y=float(t)*np.ones(self.xmax))

        else: # legacy
            for i,plt in enumerate(mctrrot.listDataItems()):
                plt.setData(x=x, y=self.data[:, i])