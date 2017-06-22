"""
Special setup file for wikia.common packages

DO NOT run this setup file directly. Use the build.py script instead.
"""

import json
import os
from setuptools import setup, find_packages


# This gets set by the build.py script which calls this script
pkg_name = os.environ.get('WIKIA_PYTHON_COMMONS_PACKAGE')

# Get the directory that contains the requested package
here = os.path.abspath(os.path.dirname(__file__))

if not pkg_name:
    # If the package name is not specified, try to figure it out.
    # We don't want to use find_packages() here, because we only want
    # the top level packages in wikia/common/ instead of all packages.
    pkgs = os.listdir(os.path.join(here, 'wikia', 'common'))
    pkgs = [p for p in pkgs if os.path.isdir(os.path.join(here, 'wikia', 'common', p))]
    if len(pkgs) != 1:
        raise Exception('Package to build/install is ambiguous.')
    pkg_name = pkgs[0]

pkg_subdir = os.path.join('wikia', 'common', pkg_name)
if not os.path.isdir(os.path.join(here, pkg_subdir)):
    raise Exception('Package directory "{pkg_subdir}" does not exist'.format(pkg_subdir=pkg_subdir))

# Check for required files
for filename in ['__init__.py', 'build.json', 'README.rst']:
    if not os.path.isfile(os.path.join(here, pkg_subdir, filename)):
        raise Exception('Package must contain a "{filename}" file'.format(filename=filename))

# Define initial params
setup_params = {
    'name': 'wikia-common-' + pkg_name,
    'author': 'Wikia Engineering',
    'author_email': 'techteam-l@wikia-inc.com',
    'url': 'https://github.com/Wikia/python-commons/tree/master/wikia/common/' + pkg_name,
    'namespace_packages': ['wikia', 'wikia.common'],
    'packages': ['wikia.common.' + pkg_name] +
                ['wikia.common.{0}.{1}'.format(pkg_name, p) for p in find_packages(pkg_subdir)],
    'include_package_data': True,
}

# Read the long_description from the README.rst file
with open(os.path.join(here, pkg_subdir, 'README.rst')) as fp:
    setup_params['long_description'] = fp.read()

# Load extra params from the build.json file
with open(os.path.join(here, pkg_subdir, 'build.json')) as fp:
    pkg_meta = json.load(fp)
    for key in ['version', 'description']:
        if key not in pkg_meta:
            raise Exception('File "{build_file}" must contain the "{key}" key'.format(
                build_file=os.path.join(pkg_subdir, 'build.json'),
                key=key
            ))
    setup_params.update(pkg_meta)

# Write a temprorary MANIFEST.in file to include package data
with open(os.path.join(here, 'MANIFEST.in'), 'w') as fp:
    fp.write('recursive-include {pkg_subdir} *\n'.format(pkg_subdir=pkg_subdir))

# Run it
setup(**setup_params)

# Removed temporary MANIFEST.in file
os.remove(os.path.join(here, 'MANIFEST.in'))
