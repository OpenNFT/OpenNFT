# -*- coding: utf-8 -*-

"""
Processing latency plots from an OpenNFT TimeVectors file

Produces a stacked area chart of per-stage durations plus a latency histogram,
saved as <TimeVectors name>_performance.png in the OpenNFT work folder.

Usage:
    python timevec.py <TimeVectors_01.txt> <TR_ms> [--prot cont|inter] [--skip N]

Examples:
    python timevec.py ...\\NF_DCM\\NF_Data_1\\TimeVectors_01.txt 1100 --prot inter --skip 10
    python timevec.py ...\\NF_SVM\\NF_Data_1\\TimeVectors_01.txt 2020 --prot cont  --skip 5
"""

import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# TimeVectors columns used here: 1:t1, 2:t2, 3:t3, 4:t4, 5:t5, 13:d0 (elapsed)
T1, T2, T3, T4, T5, D0 = 1, 2, 3, 4, 5, 13

# Timestamps below this are unset rather than a real epoch time
VALID_TIME = 1000


def load_and_process_data(file_path, skip_vol=0):
    if not os.path.exists(file_path):
        sys.exit('File not found: {}'.format(file_path))

    try:
        df = pd.read_csv(file_path, sep=r'\s+', header=None)
    except Exception as e:
        sys.exit('Cannot read {}: {}'.format(file_path, e))

    if len(df) > skip_vol:
        df = df.iloc[skip_vol:].reset_index(drop=True)

    data = pd.DataFrame()
    data['Volume'] = df.index + 1 + skip_vol

    # Offline runs stamp every t1 in one burst before processing starts
    # (startInOfflineMode), so t2 - t1 would measure time since Start, not file
    # load. Detect it by how far t1 spreads compared with t2: online both cover
    # the whole run, offline t1 does not spread at all.
    v1 = df[T1][df[T1] > VALID_TIME]
    v2 = df[T2][df[T2] > VALID_TIME]
    t1_span = (v1.max() - v1.min()) if len(v1) else 0.0
    t2_span = (v2.max() - v2.min()) if len(v2) else 0.0
    is_offline = (t2_span <= 0) or ((t1_span / t2_span) < 0.05)

    if is_offline:
        data['FileLoad'] = 0.0
    else:
        data['FileLoad'] = np.clip(
            np.where(df[T1] > VALID_TIME, (df[T2] - df[T1]) * 1000, 0), 0, None)

    data['Preprocessing'] = ((df[T3] - df[T2]) * 1000).clip(lower=0)
    data['SignalExtraction'] = ((df[T4] - df[T3]) * 1000).clip(lower=0)
    data['FeedbackCalc'] = np.clip(
        np.where(df[T5] > VALID_TIME, (df[T5] - df[T4]) * 1000, 0), 0, None)

    # Drop rows holding raw epoch timestamps instead of a duration
    data = data[data['Preprocessing'] < 3600000]

    if D0 in df.columns:
        data['TotalLatency'] = df[D0] * 1000
    else:
        data['TotalLatency'] = data[['Preprocessing', 'SignalExtraction', 'FeedbackCalc']].sum(axis=1)

    # Whatever the elapsed time contains beyond the stages measured above
    measured = data['Preprocessing'] + data['SignalExtraction'] + data['FeedbackCalc']
    data['SystemOverhead'] = (data['TotalLatency'] - measured).clip(lower=0)

    data = data[data['TotalLatency'] > 0]

    return data, is_offline


def plot_performance(file_path, tr_ms, prot='cont', skip_vol=0, out_dir=None):
    data, is_offline = load_and_process_data(file_path, skip_vol)

    load_text = ('n/a (offline run)' if is_offline else
                 '{:.1f} +/- {:.1f} ms'.format(data['FileLoad'].mean(), data['FileLoad'].std()))

    if prot == 'inter':
        # Feedback is computed at block ends only, so volumes in between would
        # pull the mean towards zero. Outliers are clipped out of the histogram.
        active = data[data['FeedbackCalc'] > 3]['FeedbackCalc']
        calc_text = ('{:.1f} +/- {:.1f} ms'.format(active.mean(), active.std())
                     if len(active) else '0.0 ms')
        hist_data = data[data['TotalLatency'] <= tr_ms * 1.5]['TotalLatency']
        ylim = tr_ms * 1.5
    else:
        calc_text = '{:.1f} +/- {:.1f} ms'.format(
            data['FeedbackCalc'].mean(), data['FeedbackCalc'].std())
        hist_data = data['TotalLatency']
        ylim = max(tr_ms * 1.1, data['TotalLatency'].max() * 1.1)

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[2, 1])

    # Stacked stage durations per volume
    ax1 = fig.add_subplot(gs[0])
    ax1.stackplot(data['Volume'],
                  data['FileLoad'],
                  data['Preprocessing'],
                  data['SignalExtraction'],
                  data['FeedbackCalc'],
                  data['SystemOverhead'],
                  labels=['File Load (t2-t1)', 'Preprocessing (t3-t2)', 'Signal Ext. (t4-t3)',
                          'Feedback Calc (t5-t4)', 'Overhead (t3:end)'],
                  colors=['#95a5a6', '#f39c12', '#3498db', '#9b59b6', '#e74c3c'], alpha=0.8)
    ax1.axhline(y=tr_ms, color='r', linestyle='--', linewidth=2, label='TR Limit ({}ms)'.format(tr_ms))
    ax1.set_ylim(0, ylim)

    textstr = '\n'.join((
        r'$\bf{Means:}$',
        'File Load: {}'.format(load_text),
        'Preprocessing: {:.1f} +/- {:.1f} ms'.format(data['Preprocessing'].mean(), data['Preprocessing'].std()),
        'Signal Ext.: {:.1f} +/- {:.1f} ms'.format(data['SignalExtraction'].mean(), data['SignalExtraction'].std()),
        'Feedback Calc: {}'.format(calc_text),
        'Sys. Overhead: {:.1f} +/- {:.1f} ms'.format(data['SystemOverhead'].mean(), data['SystemOverhead'].std()),
        '----------------',
        r'$\bf{Elapsed\ Time\ (d0):}$',
        '{:.1f} +/- {:.1f} ms'.format(data['TotalLatency'].mean(), data['TotalLatency'].std()),
    ))
    ax1.text(0.02, 0.95, textstr, transform=ax1.transAxes, fontsize=11,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    ax1.set_title('Processing Performance' + (' (offline run - no file load)' if is_offline else ''),
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Processing Time (ms)')
    ax1.set_xlim(left=data['Volume'].min(), right=data['Volume'].max())
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    ax2 = fig.add_subplot(gs[1])
    ax2.hist(hist_data, bins=50, color='#2c3e50', alpha=0.7, edgecolor='black')
    ax2.axvline(x=tr_ms, color='r', linestyle='--', linewidth=2, label='TR Limit')
    ax2.set_title('Total Latency Distribution', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Total Processing Time (ms)')
    ax2.set_ylabel('Count')

    plt.tight_layout()

    # OpenNFT writes TimeVectors into <WorkFolder>/NF_Data_<n> (setupProcParams.m),
    # so the work folder is one level up
    if out_dir is None:
        out_dir = os.path.dirname(os.path.dirname(os.path.abspath(file_path)))
    os.makedirs(out_dir, exist_ok=True)
    save_path = os.path.join(
        out_dir, '{}_performance.png'.format(os.path.splitext(os.path.basename(file_path))[0]))
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print('Saved {}'.format(save_path))
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot OpenNFT processing latency')
    parser.add_argument('path', type=str, help='path to a TimeVectors file')
    parser.add_argument('tr', type=int, help='TR in milliseconds')
    parser.add_argument('--prot', choices=['cont', 'inter'], default='cont',
                        help="feedback protocol, matching the setup file's Prot field: "
                             "cont for continuous feedback (Cont, ContTask), "
                             "inter for intermittent (Inter, InterBlock)")
    parser.add_argument('--skip', type=int, default=0,
                        help='initial volumes to skip, i.e. nrSkipVol')
    parser.add_argument('--outdir', type=str, default=None,
                        help='where to write the PNG (default: the OpenNFT work folder)')
    args = parser.parse_args()

    plot_performance(args.path.strip('"').strip("'"), args.tr, args.prot, args.skip, args.outdir)