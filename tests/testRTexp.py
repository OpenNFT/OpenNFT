# -*- coding: utf-8 -*-

"""
Real time export simulation

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

Written by Artem Nikonorov, Yury Koush
"""


import os
import shutil
from time import sleep
import glob

delete_files = True

mask = "001_000008_000"
#fns = [1, 2, 3, 4, 6, 5, 7, 8]
fns = None

testCase = 'PSC'

if testCase == 'PSC':
    srcpath = 'C:/_RT/rtData/NF_PSC/NF_Run_1_src'
    dstpath = 'C:/_RT/rtData/NF_PSC/NF_Run_1'
    pause_in_sec = 1

elif testCase == 'SVM':
    srcpath = 'C:/_RT/rtData/NF_SVM/NF_Run_1_src'
    dstpath = 'C:/_RT/rtData/NF_SVM/NF_Run_1'
    pause_in_sec = 1

elif testCase == 'DCM': 
    srcpath = 'C:/_RT/rtData/NF_DCM/NF_Run_1_src'
    dstpath = 'C:/_RT/rtData/NF_DCM/NF_Run_1'
    pause_in_sec = 1

elif testCase == 'REST': 
    srcpath = 'C:/_RT/rtData/rtQA_REST/RS_Run_1_src'
    dstpath = 'C:/_RT/rtData/rtQA_REST/RS_Run_1'
    pause_in_sec = 1.97

elif testCase == 'TASK': 
    srcpath = 'C:/_RT/rtData/rtQA_TASK/TASK_Run_1_src'
    dstpath = 'C:/_RT/rtData/rtQA_TASK/TASK_Run_1'
    pause_in_sec = 1.97

if delete_files:
    files = glob.glob(dstpath+'/*')
    for f in files:
        os.remove(f)

if fns is None:
    filelist = os.listdir(srcpath)
else:
    filelist = []
    for fn in fns:
        fname = "{0}{1:03d}.dcm".format(mask, fn)
        filelist.append(fname)

for filename in filelist:
    src = os.path.join(srcpath, filename)
    if os.path.isfile(src):
        dst = os.path.join(dstpath, filename)
        shutil.copy(src, dst)
        print(filename)
        sleep(pause_in_sec) # seconds
