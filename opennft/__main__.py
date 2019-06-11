# -*- coding: utf-8 -*-

"""

__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

"""

import sys
from PyQt5.QtWidgets import QApplication

from opennft.opennft import OpenNFT


def main():
    app = QApplication(sys.argv)

    app.setApplicationName('OpenNFT')
    app.setOrganizationName('OpenNFT')
    app.setApplicationVersion('1.0')

    nft = OpenNFT()
    nft.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
