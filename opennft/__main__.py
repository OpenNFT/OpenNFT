# -*- coding: utf-8 -*-

"""

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

"""

import sys
import multiprocessing as mp

from PyQt5.QtWidgets import QApplication

from opennft import excepthook, utils
from opennft import config
from opennft import opennft


def main():
    mp.set_start_method('spawn')

    # Override default exception hook to show any exceptions on PyQt5 slots
    excepthook.set_hook()

    app = QApplication(sys.argv)

    app.setApplicationName('OpenNFT')
    app.setOrganizationName('OpenNFT')
    app.setApplicationVersion('1.0')

    config.MATLAB_NAME_SUFFIX = '_{}'.format(utils.generate_random_number_string())

    nft = opennft.OpenNFT()
    nft.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
