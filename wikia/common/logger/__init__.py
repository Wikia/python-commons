"""
wikia.common.logger
===================

Common logging classes for centralized logging at Wikia
"""

import json
import pkg_resources

from .logger import Logger, LogFormatter, LogRecord


__version__ = json.loads(pkg_resources.resource_string(__name__, 'build.json'))['version']
