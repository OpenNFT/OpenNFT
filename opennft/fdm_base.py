# Generic framewise displacement computation and plotting

import matlab
import numpy as np
import pyqtgraph as pg

import opennft.fdm_settings as s


class FD:
    def __init__(self, module = None):
        self.module = module
        
        # names of the dofs
        self.names = ['X','Y','Z','pitch','roll','yaw', 'FD']

        self.mode = {'tr': ['tr', 'translational','tr_sa'], 'rot' : ['rot', 'rotational','rot_sa'], 'fd':['FD', 'fd','FD_sa']}
        
        self.plotBgColor = s.PLOT_BACKGROUND_COLOR
        
        k = np.array(list(matlab.double([[1e-05,1e-05,1e-05,1e-05,1e-05,1e-05]])))
        self.data = np.array(k).astype(np.float)
        
        self.radius = s.DEFAULT_FD_RADIUS
        self.threshold = s.DEFAULT_FD_THRESHOLDS
        
        self.xmax = s.PLOT_INITIAL_XMAX
        self.smooth_fwhm = s.REGRESSION_SMOOTH_FWHM
                
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

    # create Plot
    def create_mc_plot(self, parent, eventfilter = None, nme="MC"):
        mctrotplot = pg.PlotWidget(parent, name=nme)
        mctrotplot.setBackground(self.plotBgColor)

        p = mctrotplot.getPlotItem()
        p.setTitle('MC', size='')
        p.setLabel('left', "Amplitude [a.u.]")
        p.setMenuEnabled(enableMenu=True)
        p.setMouseEnabled(x=False, y=False)
        if eventfilter is not None:
            p.installEventFilter(eventfilter)
        
        return mctrotplot
    
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
                    mctrrot.plot(x=x, y=self.data[:, i], pen=s.PLOT_PEN_COLORS[i], name=self.names[i])
                        
            elif md in self.mode['rot']:
                for i in range(3, 6):
                    mctrrot.plot(x=x, y=self.data[:, i], pen=s.PLOT_PEN_COLORS[i], name=self.names[i])
                        
            elif md in self.mode['fd']:
                mctrrot.plot(x=x, y=self.all_fd(), pen=s.PLOT_PEN_COLORS[0], name='FD')
                for i,t in enumerate(self.threshold):
                    mctrrot.plot(x=np.arange(0,self.xmax, dtype=np.float64), y=float(t)*np.ones(self.xmax), pen=s.PLOT_PEN_COLORS[i+1], name='thr' + str(i))
                
            else:
                for i in range(0, 6):
                    mctrrot.plot(x=x, y=self.data[:, i],pen=s.PLOT_PEN_COLORS[i], name=self.names[i])
                
            # mctrrot.disableAutoRange(axis=pg.ViewBox.XAxis)
            # # adapt xmax
            # if len(x) > self.xmax-5:
            #     self.xmax+=30
            # mctrrot.setXRange(1, self.xmax)
                    
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