# -*- coding: utf-8 -*-

import sys
from loguru import logger

from opennft import config


def logging_setup():
    logger.remove()
    logger.add(
        sys.stdout,
        format=(
            '<g>{time:YYYY-MM-DD hh:mm:ss}</g> | '
            '<level>{level:9}</level> | '
            '<c>{module}</c>:<c>{function}</c> - '
            '<b>{message}</b>'
        ),
        level=config.LOG_LEVEL,
    )
