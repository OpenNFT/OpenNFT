# -*- coding: utf-8 -*-
"""

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Evgeny Prilepin
"""

import sys


def set_hook():
    def _exception_hook(exctype, value, traceback):
        sys.__excepthook__(exctype, value, traceback)

    sys.excepthook = _exception_hook
