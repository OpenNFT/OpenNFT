# -*- coding: utf-8 -*-

import os
import sys
import pathlib
import tempfile
import subprocess

from distutils.spawn import find_executable
from distutils.core import DistutilsOptionError

from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


NAME = 'OpenNFT'
URL = 'http://www.OpenNFT.org'
LICENSE = 'GPL-3.0'
AUTHOR = 'OpenNFT Team'
AUTHOR_EMAIL = 'opennft@gmail.com'
DESCRIPTION = 'An open-source Python/Matlab framework for real-time fMRI neurofeedback training'

PYTHON_REQUIRES = '>=3.6, <4.0'

ROOT_DIR = pathlib.Path(__file__).parent


def get_version():
    about = {}
    ver_mod = ROOT_DIR / 'opennft' / '__version__.py'
    with ver_mod.open() as f:
        exec(f.read(), about)
    return about['__version__']


def long_description():
    readme = ROOT_DIR / 'README.md'
    with readme.open(encoding='utf-8') as f:
        return '\n' + f.read()


def find_matlab_package_files():
    matlab_files_root = ROOT_DIR / 'opennft' / 'matlab'
    matlab_files = list(str(p) for p in matlab_files_root.rglob('*.m'))
    return matlab_files


def package_data():
    data = [
        'configs/*',
        'ui/*.ui',
        'ui/images/*',
        'plugins/*',
    ] + find_matlab_package_files()
    return {'opennft': data}


def specify_requirements():
    req_file = ROOT_DIR / 'requirements.txt'

    with req_file.open('r') as fp:
        requirements = [line.strip() for line in fp.readlines() if line.strip()]

    return requirements


class InstallMatlabEngineMixin:
    cmd_options = [
        ('matlab-root=', None, "MATLAB installation directory (MATLABROOT)")
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
        if self.matlab_root:
            matlab_root = self.matlab_root
            install_failed_error = True
        else:
            matlab_exe = find_executable('matlab')
            if not matlab_exe:
                print('Cannot find MATLAB. "Matlab engine for Python" will not be installed', file=sys.stderr)
                return

            matlab_exe_parent = pathlib.Path(matlab_exe).parent
            install_failed_error = False

            if matlab_exe_parent.name == 'bin':
                matlab_root = matlab_exe_parent.parent
            else:
                # /matlabroot/bin/win64
                matlab_root = matlab_exe_parent.parent.parent

            print('MATLAB was found. MATLABROOT: "{}"'.format(matlab_root))

        engine_dir = matlab_root / 'extern' / 'engines' / 'python'

        if not engine_dir.is_dir():
            raise EnvironmentError(
                'Cannot find "MATLAB engine for Python" in MATLAB root "{}"'.format(matlab_root))

        print('Installing "MATLAB engine for Python" from "{}"...'.format(engine_dir))

        # A temporary file for writing stderr
        fd, ferr_name = tempfile.mkstemp()
        os.close(fd)

        install_script = str(ROOT_DIR / 'install_matlabengine.py')
        install_command = [sys.executable, install_script, str(engine_dir), ferr_name] + sys.path

        p = subprocess.run(install_command)

        with open(ferr_name, 'r', encoding='utf-8') as ferr:
            stderr_text = ferr.read()
        os.unlink(ferr_name)

        if p.returncode != 0:
            try:
                raise EnvironmentError(
                    'An error occurred while installing "MATLAB engine for Python"\n{}\n'.format(
                        stderr_text))
            except EnvironmentError as err:
                if install_failed_error:
                    raise
                else:
                    print(err, file=sys.stderr)
        else:
            print('"Matlab Engine for Python" is successfully installed')


class InstallGitSubmodulesMixin:
    def _install_git_submodules(self):
        if pathlib.Path('.git').exists():
            subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'])


class InstallCommand(install, InstallMatlabEngineMixin, InstallGitSubmodulesMixin):
    user_options = install.user_options + InstallMatlabEngineMixin.cmd_options

    def initialize_options(self):
        install.initialize_options(self)
        self._initialize()

    def finalize_options(self):
        install.finalize_options(self)
        self._finalize()

    def run(self):
        self._install_matlab_engine()
        self._install_git_submodules()
        install.run(self)


class DevelopCommand(develop, InstallMatlabEngineMixin, InstallGitSubmodulesMixin):
    user_options = develop.user_options + InstallMatlabEngineMixin.cmd_options

    def initialize_options(self):
        develop.initialize_options(self)
        self._initialize()

    def finalize_options(self):
        develop.finalize_options(self)
        self._finalize()

    def run(self):
        self._install_matlab_engine()
        self._install_git_submodules()
        develop.run(self)


setup(
    name=NAME,
    version=get_version(),

    python_requires=PYTHON_REQUIRES,
    install_requires=specify_requirements(),

    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_data=package_data(),
    include_package_data=True,

    entry_points={
        'gui_scripts': [
            'opennft = opennft.__main__:main',
        ],
        'console_scripts': [
            'opennft_console = opennft.__main__:main',
            'run_matlab = opennft.runmatlab:main',
        ],
    },

    cmdclass={
        'install': InstallCommand,
        'develop': DevelopCommand,
    },

    classifiers=[
        'License :: OSI Approved :: GPL-3.0 License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
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
