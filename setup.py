# -*- coding: utf-8 -*-

import sys
import pathlib
import subprocess

from distutils.core import DistutilsOptionError

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install


NAME = 'OpenNFT'
URL = 'http://www.OpenNFT.org'
LICENSE = 'GPL-3.0'
AUTHOR = 'OpenNFT Team'
AUTHOR_EMAIL = 'opennft@gmail.com'
DESCRIPTION = 'An open-source Python/Matlab framework for real-time fMRI neurofeedback training'

PYTHON_REQUIRES = '>=3.5'


def root_dir():
    return pathlib.Path(__file__).parent


def version():
    about = {}
    ver_mod = root_dir() / 'opennft' / '__version__.py'
    with ver_mod.open() as f:
        exec(f.read(), about)
    return about['__version__']


def long_description():
    readme = root_dir() / 'README.md'
    with readme.open(encoding='utf-8') as f:
        return '\n' + f.read()


def find_matlab_package_files():
    matlab_files_root = root_dir() / 'opennft' / 'matlab'
    matlab_files = list(str(p) for p in matlab_files_root.rglob('*.m'))
    return matlab_files


def package_data():
    data = [
        'configs/*'
    ] + find_matlab_package_files()
    return {'opennft': data}


def find_requires():
    requires = [
        'PyQt5 >= 5.12.0',
        'numpy >= 1.15.0, >= 1.15.0+mkl',
        'pyqtgraph  @  https://github.com/pyqtgraph/pyqtgraph/tarball/master',
        'pyniexp @ https://github.com/tiborauer/pyniexp/tarball/master',
        'watchdog >= 0.9.0',
    ]

    if sys.platform == 'win32':
        pyhook_whl = {
            (3, 5): 'https://github.com/OpenNFT/OpenNFT/releases/download/v1.0rc0/pyHook-1.5.1-cp35-cp35m-win_amd64.whl',
            (3, 6): 'https://github.com/OpenNFT/OpenNFT/releases/download/v1.0rc0/pyHook-1.5.1-cp36-cp36m-win_amd64.whl',
            (3, 7): 'https://github.com/OpenNFT/OpenNFT/releases/download/v1.0rc0/pyHook-1.5.1-cp37-cp37m-win_amd64.whl',
        }[sys.version_info[:2]]

        requires += [
            'pywin32 >= 224',
            'pyHook @ {}'.format(pyhook_whl),
        ]

    return requires


class InstallMatlabEngineMixin:
    cmd_options = [
        ('matlab-root=', None, "MATLAB installation directory")
    ]

    def _initialize(self):
        self.matlab_root = None

    def _finalize(self):
        if self.matlab_root is not None:
            self.matlab_root = pathlib.Path(self.matlab_root)
            if not self.matlab_root.is_dir():
                raise DistutilsOptionError(
                    'MATLAB installation directory "{}" does not exist'.format(self.matlab_root))

    def _install_matlab_engine(self):
        if not self.matlab_root:
            return

        engine_dir = self.matlab_root / 'extern' / 'engines' / 'python'

        if not engine_dir.is_dir():
            raise EnvironmentError(
                'Cannot find "MATLAB engine for Python" in MATLAB root "{}"'.format(
                    self.matlab_root))

        print('Installing "MATLAB engine for Python" from "{}"...'.format(engine_dir))

        engine_setup_path = str(engine_dir / 'setup.py')
        install_command = [sys.executable, engine_setup_path, 'install']

        p = subprocess.run(install_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if p.returncode != 0:
            raise EnvironmentError(
                'An error occurred while installing "MATLAB engine for Python"\n'
                + '{}\n'.format(p.stderr.decode('utf-8'))
            )
        else:
            print('{}\n\n"Matlab Engine for Python" is successfully installed'.format(
                p.stdout.decode('utf-8')))


class InstallCommand(install, InstallMatlabEngineMixin):
    user_options = install.user_options + InstallMatlabEngineMixin.cmd_options

    def initialize_options(self):
        install.initialize_options(self)
        self._initialize()

    def finalize_options(self):
        install.finalize_options(self)
        self._finalize()

    def run(self):
        self._install_matlab_engine()
        install.run(self)


class DevelopCommand(develop, InstallMatlabEngineMixin):
    user_options = develop.user_options + InstallMatlabEngineMixin.cmd_options

    def initialize_options(self):
        develop.initialize_options(self)
        self._initialize()

    def finalize_options(self):
        develop.finalize_options(self)
        self._finalize()

    def run(self):
        self._install_matlab_engine()
        develop.run(self)


setup(
    name=NAME,
    version=version(),

    python_requires=PYTHON_REQUIRES,
    install_requires=find_requires(),

    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_data=package_data(),
    include_package_data=True,

    entry_points={
        'gui_scripts': [
            'opennft = opennft.opennft:main'
        ],
        'console_scripts': [
            'opennft_console = opennft.opennft:main'
        ]
    },

    cmdclass={
        'install': InstallCommand,
        'develop': DevelopCommand,
    },

    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],

    url=URL,
    license=LICENSE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=long_description(),
    long_description_content_type='text/markdown',
)
