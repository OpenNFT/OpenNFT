# -*- coding: utf-8 -*-

import sys
from loguru import logger


def logging_setup():
    logger.remove()
    logger.add(
        sys.stdout,
        format='<g>{time:YYYY-MM-DD hh:mm:ss}</g> | <level>{level:9}</level> | <c>{module}</c>:<c>{function}</c>:<le>{line}</le> - <b>{message}</b>'
    )
