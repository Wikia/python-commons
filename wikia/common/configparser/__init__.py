"""
wikia.common.configparser
=========================

Wrapper around the configparser backport from Python 3.2+:
https://pypi.python.org/pypi/configparser
"""

import json
import pkg_resources

from .configparser import ConfigParser, ExtendedInterpolation


__version__ = json.loads(pkg_resources.resource_string(__name__, 'build.json'))['version']
