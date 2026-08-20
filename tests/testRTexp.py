# -*- coding: utf-8 -*-

"""
Real time export simulation

Usage:
    python testRTexp.py DCM
    python testRTexp.py GE_PSC -r
    python testRTexp.py TASK --nrvol 50 --pause 0.05

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

Written by Artem Nikonorov, Yury Koush
"""


import argparse
import random
import re
import shutil
from pathlib import Path
from time import sleep

# Root folder holding demo datasets
DATA_ROOT = Path('path/to/root_with_demo')

# Per-protocol replay settings, taken from each dataset's setup file.
#   slnr  - files making up one volume: 1 for Siemens-style data (one DICOM per
#           volume), NrOfSlices for GE Signa (one DICOM per slice)
#   nrvol - volumes to send
#   pause - seconds between volumes, i.e. the TR
TEST_CASES = {
    'PSC':    dict(src='data/NF_PSC/NF_Run_1_src',       dst='data/NF_PSC/NF_Run_1',
                   slnr=1,  nrvol=155,  pause=1.97, mask='*.dcm'),
    'SVM':    dict(src='data/NF_SVM/NF_Run_1_src',       dst='data/NF_SVM/NF_Run_1',
                   slnr=1,  nrvol=215,  pause=2.02, mask='*.dcm'),
    'DCM':    dict(src='data/NF_DCM/NF_Run_1_src',       dst='data/NF_DCM/NF_Run_1',
                   slnr=1,  nrvol=1060, pause=1.10, mask='*.dcm'),
    'REST':   dict(src='data/rtQA_REST/RS_Run_1_src',    dst='data/rtQA_REST/RS_Run_1',
                   slnr=1,  nrvol=336,  pause=1.97, mask='*.dcm'),
    'TASK':   dict(src='data/rtQA_TASK/TASK_Run_1_src',  dst='data/rtQA_TASK/TASK_Run_1',
                   slnr=1,  nrvol=100,  pause=1.97, mask='*.dcm'),
    'GE_PH1': dict(src='data/PH1_DATA_080925/s11100000', dst='data/PH1_DATA_080925/NF_Data_1',
                   slnr=48, nrvol=203,  pause=2.50, mask='i*.MRDC.*'),
    'GE_PSC': dict(src='data/PS2_DATA_160325/s_run3',    dst='data/PS2_DATA_160325/NF_Data_1',
                   slnr=60, nrvol=100,  pause=2.00, mask='i*.MRDC.*'),
}

parser = argparse.ArgumentParser(description='Real time export simulation')
parser.add_argument('testCase', choices=sorted(TEST_CASES), help='protocol to replay')
parser.add_argument('-r', action='store_true', help='Send slices in random order within the volume')
parser.add_argument('--nrvol', type=int, help='override the number of volumes to send')
parser.add_argument('--pause', type=float, help='override the seconds between volumes')
parser.add_argument('--keep', action='store_true', help='do not clear the destination folder first')
args = parser.parse_args()

cfg = TEST_CASES[args.testCase]
srcpath = DATA_ROOT / cfg['src']
dstpath = DATA_ROOT / cfg['dst']
mask = cfg['mask']
slnr = cfg['slnr']
slnr_2 = slnr // 2
nrvol = cfg['nrvol'] if args.nrvol is None else args.nrvol
pause_in_sec = cfg['pause'] if args.pause is None else args.pause

if not srcpath.is_dir():
    raise SystemExit('Source folder not found: {}\n'
                     'Check DATA_ROOT at the top of this file.'.format(srcpath))
dstpath.mkdir(parents=True, exist_ok=True)

if not args.keep:
    for f in dstpath.glob('*'):
        if f.is_file():
            f.unlink()


def file_index(f):
    numbers = re.findall(r'\d+', f.name)
    return int(numbers[-1]) if numbers else 0


filelist = sorted((f for f in srcpath.glob(mask) if f.is_file()), key=file_index)

available = len(filelist) // slnr
if nrvol > available:
    print('Only {} volumes available ({} files / {} per volume), sending those'.format(
        available, len(filelist), slnr))
    nrvol = available

print('{}: {} volumes x {} file(s), every {} s -> {}'.format(
    args.testCase, nrvol, slnr, pause_in_sec, dstpath))

for n in range(0, slnr * nrvol, slnr):
    print(n)
    if args.r:
        files_to_copy = list(filelist[n: n + slnr])
        random.shuffle(files_to_copy)
    else:
        part1 = filelist[n + slnr_2: n + slnr]
        part2 = filelist[n: n + slnr_2]
        files_to_copy = part1 + part2

    for f in files_to_copy:
        if f.is_file() and not f.name.startswith('.'):
            shutil.copy(f, Path(dstpath, f.name))
            print(f)
    sleep(pause_in_sec)
