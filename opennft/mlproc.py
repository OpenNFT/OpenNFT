# -*- coding: utf-8 -*-

"""
Wrapper class for Matlab processes


__________________________________________________________________________
Copyright (C) 2016-2019 OpenNFT.org

Written by Evgeny Prilepin

"""

import time
import multiprocessing as mp

from loguru import logger

try:
    import matlab.engine as me
except ImportError as err:
    raise ImportError(
        '"MATLAB Engine for Python" is not installed.\n'
        'Please see how to install Matlab engine:\n'
        'https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html\n'
        'https://github.com/OpenNFT/opennft.github.io/blob/master/OpenNFT_Manual_v1.0.pdf'
    ) from err

from opennft import config


class MatlabSharedEngineHelper:
    """A helper class for using shared matlab engine sessions
    """

    def __init__(self, alive_check_period=60, startup_options=None, shared_name=None):
        self._engine = None

        self._alive_check_period = alive_check_period  # second
        self._startup_options = startup_options
        self._shared_name = shared_name
        self._name = ''
        self._pid = mp.Value('i', 0)
        self._proc = None  # type: mp.Process

    @property
    def engine(self):
        return self._engine

    @property
    def name(self):
        return self._name

    def connect(self, start=True, name_prefix=None):
        """Connects to a shared matlab session
        """
        if self.engine is not None:
            return True

        if not self._connect(name_prefix):
            if start:
                self._start()
                return self._connect(name_prefix)
            else:
                return False
        else:
            return True

    def prepare(self):
        """Prepares Matlab session for needs of NFB
        """
        if not self.engine:
            return

        self.engine.cd(config.MATLAB_FUNCTIONS_PATH)
        self.engine.addMatlabDirs(nargout=0)
        self.engine.clear('all', nargout=0)

    def destroy_engine(self):
        if not self._engine:
            return

        logger.info('Destroy Matlab engine "{}"...', self.name)

        if self._pid.value != -1:
            # send termination signal
            self._pid.value = -1

        self._engine = None

    def detach_engine(self):
        if self._engine and '_matlab' in self._engine.__dict__:
            self._engine.__dict__.pop("_matlab")
            self._engine = None

    def wait(self, timeout=None):
        """Waits for closing matlab
        """
        if self._proc:
            try:
                self._proc.join(timeout=timeout)
            except KeyboardInterrupt:
                self.destroy_engine()

    def _connect(self, name_prefix=None):
        sessions = me.find_matlab()

        if not sessions:
            return

        if not name_prefix:
            name = sessions[0]
        else:
            name = ''
            for s in sessions:
                if s.startswith(name_prefix):
                    name = s
                    break
            if not name:
                return False

        try:
            self._engine = me.connect_matlab(name)
            logger.info('Connected to Matlab engine "{}"', name)
        except me.EngineError:
            logger.exception('Cannot connect to Matlab engine "{}"', name)
            return False

        self._name = name
        return True

    def _start(self):
        e = mp.Event()

        p = mp.Process(
            target=self._start_matlab,
            args=(e, self._alive_check_period,
                  self._startup_options, self._shared_name))

        p.daemon = False
        p.start()
        e.wait()

        self._proc = p

    def _start_matlab(self, event: mp.Event,
                      alive_check_period=60,
                      startup_options=None,
                      shared_name=None):

        pid = mp.current_process().pid
        self._pid.value = pid

        logger.info('Starting Matlab engine "{}" helper process {}...', shared_name, pid)

        event.clear()

        try:
            if startup_options is None:
                eng = me.start_matlab()
            else:
                eng = me.start_matlab(startup_options)

            if shared_name:
                eng.matlab.engine.shareEngine(shared_name, nargout=0)
            else:
                eng.matlab.engine.shareEngine(nargout=0)
                shared_name = eng.matlab.engine.engineName(nargout=1)

            logger.info('Matlab engine "{}" is started', shared_name)
        except (me.EngineError, me.MatlabExecutionError):
            logger.exception('Cannot start Matlab engine "{}"', shared_name)
            raise
        finally:
            event.set()

        while self._pid.value != -1:
            # Is matlab alive?
            try:
                eng.version(nargout=0)
            except (me.EngineError, me.CancelledError):
                break
            try:
                time.sleep(alive_check_period)
            except KeyboardInterrupt:
                break

        try:
            eng.exit()
        except SystemError:
            logger.exception('Cannot terminate Matlab process correctly')
        else:
            logger.info('Terminate Matlab engine "{}" helper process {}', shared_name, pid)
