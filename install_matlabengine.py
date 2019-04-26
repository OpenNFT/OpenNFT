# -*- coding: utf-8 -*-

import sys
import os
import subprocess

sys.path = sys.argv[3:]

import elevate
import chardet


def main():
    engine_dir = sys.argv[1]
    ferr = sys.argv[2]

    engine_setup = os.path.join(engine_dir, 'setup.py')
    install_command = [sys.executable, engine_setup, 'install']

    p = subprocess.run(install_command,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       cwd=engine_dir)

    if p.returncode != 0:
        if (b"error: could not create 'build'" in p.stderr
                or b"error: You do not have write permission" in p.stderr):
            # Access denied, try to install as Administrator/root
            elevate.elevate(show_console=False, graphical=True)

        try:
            stderr_text = p.stderr.decode()
        except UnicodeDecodeError:
            enc = chardet.detect(p.stderr)['encoding']
            if enc:
                stderr_text = p.stderr.decode(enc)
            else:
                # cannot decode bytes, return as it is
                stderr_text = str(p.stderr)

        with open(ferr, 'w', encoding='utf-8') as fp:
            fp.write(stderr_text)

    return p.returncode


if __name__ == '__main__':
    sys.exit(main())
