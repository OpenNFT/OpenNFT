from pynf.dicomexport import TcpDicom 
import pickle

rtd = TcpDicom() 
data = { 
    'watch':r'C:\RT\rt', 
    'LastName':'Test', 
    'ID': 'RHUL' 
} 
rtd.set_header_from_Dicom(data) 
rtd.open_as_server(); rtd.receive_initial() 
dat = [] 
for n in range(0,10):
    dat.append(rtd.receive_scan())
    rtd.log('Scan #{:2d} received'.format(n+1))

with open('rtdicom.dat','wb') as f:
    pickle.dump([rtd.header,dat],f)

## To check
# import numpy as np
# from PIL import Image
# with open('rtdicom.dat','rb') as f:
#    dat = pickle.load(f)
# npdat = np.asarray(dat[1])
# im = Image.fromarray(npdat[0,:,:,15])
# im.show()
