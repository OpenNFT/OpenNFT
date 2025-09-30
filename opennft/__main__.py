# -*- coding: utf-8 -*-

"""

__________________________________________________________________________
Copyright (C) 2016-2021 OpenNFT.org

"""

import sys
import multiprocessing as mp

from PyQt6.QtWidgets import QApplication

from opennft import excepthook, utils
from opennft import config
from opennft import opennft
from opennft import __version__
from opennft._logging import logging_setup


def main():
    mp.set_start_method('spawn')

    # Override default exception hook to show any exceptions on PyQt5 slots
    excepthook.set_hook()

    app = QApplication(sys.argv)

    app.setApplicationName(config.APP_NAME)
    app.setOrganizationName(config.APP_NAME)
    app.setApplicationVersion(__version__)

    config.MATLAB_NAME_SUFFIX = '_{}'.format(utils.generate_random_number_string())

    logging_setup()

    nft = opennft.OpenNFT()
    nft.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
