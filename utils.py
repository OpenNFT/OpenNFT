# -*- coding: utf-8 -*-
"""
__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Evgeny Prilepin

"""

import time
import contextlib

import numpy as np


# ==============================================================================
@contextlib.contextmanager
def timeit(message):
    t = time.time()
    yield
    to = time.time() - t

    units = 's'

    if 0.001 <= to < 0.1:
        to *= 1e3
        units = 'ms'
    elif to < 0.001:
        to *= 1e6
        units = 'mcs'

    print(message + ' {:.2f} {}'.format(to, units))


# ==============================================================================
def generate_random_number_string(num=5):
    """Generates a sequence of numbers and returns it as string
    """
    num = np.random.randint(0, 9, size=(num,)).tolist()
    s_num = ''.join(map(str, num))

    return s_num
