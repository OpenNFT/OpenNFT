# -*- coding: utf-8 -*-

import sys
import collections
import typing

from loguru import logger

from opennft import mlproc
from opennft import utils
from opennft import config


_SHARED_SUFFIX = '_SHARED'


def create_matlab_helper(engine_name: str, startup_options=None):
    """Creates helper object for Matlab shared engine
    """
    shared_name = engine_name + config.MATLAB_NAME_SUFFIX

    return mlproc.MatlabSharedEngineHelper(
        startup_options=startup_options,
        shared_name=shared_name
    )


def get_matlab_helpers() -> typing.Dict[str, mlproc.MatlabSharedEngineHelper]:
    """Returns dictionary with all matlab helper objects
    """
    if not getattr(get_matlab_helpers, 'helpers', None):
        helpers = [
            # Main matlab engine
            (config.MAIN_MATLAB_NAME, create_matlab_helper(
                engine_name=config.MAIN_MATLAB_NAME,
                startup_options=config.MAIN_MATLAB_STARTUP_OPTIONS,
            )),

            # Matlab helper processs for display using Psychtoolbox (aka Ptb)
            # with possible reusing for first model computation
            (config.PTB_MATLAB_NAME, create_matlab_helper(
                engine_name=config.PTB_MATLAB_NAME,
                startup_options=config.PTB_MATLAB_STARTUP_OPTIONS,
            )),

            # Matlab helper processs for GUI data estimation
            (config.SPM_MATLAB_NAME, create_matlab_helper(
                engine_name=config.SPM_MATLAB_NAME,
                startup_options=config.SPM_MATLAB_STARTUP_OPTIONS,
            )),
        ]

        if config.USE_MATLAB_MODEL_HELPER:
            # Matlab helper processs for second model computation
            helpers.append((config.MODEL_HELPER_MATLAB_NAME, create_matlab_helper(
                engine_name=config.MODEL_HELPER_MATLAB_NAME,
                startup_options=config.MODEL_HELPER_MATLAB_STARTUP_OPTIONS,
            )))

        get_matlab_helpers.helpers = collections.OrderedDict(helpers)

    return get_matlab_helpers.helpers


def connect_to_matlab(start=True) -> bool:
    """Connects to all matlab shared engines
    """
    helpers = get_matlab_helpers()

    for name, helper in helpers.items():
        if not helper.connect(start=start, name_prefix=name):
            logger.error('Cannot connect to Matlab "{}"'.format(name))
            return False

    return True


def destroy_matlab():
    """Destroys all matlab engines
    """
    helpers = get_matlab_helpers()

    for name, helper in helpers.items():
        helper.destroy_engine()

    wait_for_closing_matlab()


def detach_matlab():
    """Detach from all matlab engines
    """
    helpers = get_matlab_helpers()

    for name, helper in helpers.items():
        helper.detach_engine()


def wait_for_closing_matlab():
    """Waits for closing all matlab engines
    """
    for helper in get_matlab_helpers().values():
        helper.wait()


def is_shared_matlab() -> bool:
    """Returns true if matlab sessions are shared
    """
    helpers = get_matlab_helpers()
    return helpers[config.MAIN_MATLAB_NAME].name.endswith(_SHARED_SUFFIX)


def main():
    config.MATLAB_NAME_SUFFIX = _SHARED_SUFFIX

    with utils.timeit('Running Matlab shared engines: '):
        if not connect_to_matlab(start=True):
            destroy_matlab()
            sys.exit(1)

    print('Press Ctrl+C for quit and destroy all Matlab shared engines')
    wait_for_closing_matlab()


if __name__ == '__main__':
    main()
