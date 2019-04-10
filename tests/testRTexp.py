# -*- coding: utf-8 -*-

"""
Real time export simulation

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Artem Nikonorov, Yury Koush
"""


import os
import shutil
from time import sleep
import glob

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

delete_files = True

if delete_files:
    files = glob.glob(dstpath+'/*')
    for f in files:
        os.remove(f)

for filename in os.listdir(srcpath):
    src = os.path.join(srcpath, filename)
    if os.path.isfile(src):
    	dst = os.path.join(dstpath, filename)
    	shutil.copy(src, dst)
    	print(filename)
    	sleep(pause_in_seconds) # seconds