#!/usr/bin/env python
"""
This is a convenience script for building, installing, and uploading
individual packages from the wikia.common namespace. This should be run
from inside a virtual environment.

Usage: build.py (install|develop|upload) <package>

Commands:

    install     Install the package into your virtual environment.
    develop     Install the package using pip's "editable" mode.
    upload      Build a source distribution and upload it to Wikia's
                private PyPI server (requires a working ~/.pypirc file).

Arguments:

    <package>   The name of a package directory in wikia/common/

"""

import os
import subprocess
import sys


def is_venv():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def main(args=sys.argv[1:]):
    """Wrapper around setup.py and pip for individual packages."""
    if not is_venv():
        return 'ERROR: Must be run from within a virtual environment'

    if (len(args) != 2 or
            '-h' in args or '--help' in args or
            args[0] not in ('install', 'develop', 'upload')):
        return __doc__
    command, pkg_name = args

    here = os.path.abspath(os.path.dirname(__file__))

    if not os.path.isdir(os.path.join(here, 'wikia', 'common', pkg_name)):
        return 'ERROR: No such package wikia.common.' + pkg_name

    environ = {'WIKIA_PYTHON_COMMONS_PACKAGE': pkg_name}

    if command in ('install', 'develop'):
        command_args = [sys.executable, '-m', 'pip', 'install']
        if command == 'develop':
            command_args.append('-e')
        command_args.append('.')
        proc = subprocess.Popen(command_args, shell=False, cwd=here, env=environ)
        proc.communicate()
    elif command == 'upload':
        command_args = [sys.executable, 'setup.py', 'sdist', 'upload', '-r', 'artifactory']
        proc = subprocess.Popen(command_args, shell=False, cwd=here, env=environ)
        proc.communicate()

    return 0


if __name__ == '__main__':
    sys.exit(main())
