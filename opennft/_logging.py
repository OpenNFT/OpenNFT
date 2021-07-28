# -*- coding: utf-8 -*-

import sys
import os
from loguru import logger

from opennft import config
from opennft.utils import get_app_config_dir


def logging_setup():
    if sys.platform == 'win32' and sys.executable.lower().endswith('pythonw.exe'):
        log_file = get_app_config_dir() / f'{config.APP_NAME}.log'
        sys.stdout = open(os.devnull, "w")
        sys.stderr = sys.stdout
    else:
        print(get_app_config_dir() / f'{config.APP_NAME}.log')
        log_file = sys.stdout

    logger.remove()
    logger.add(
        log_file,
        format=(
            '<g>{time:YYYY-MM-DD hh:mm:ss}</g> | '
            '<level>{level:9}</level> | '
            '<c>{module}</c>:<c>{function}</c> - '
            '<b>{message}</b>'
        ),
        level=config.LOG_LEVEL,
    )
