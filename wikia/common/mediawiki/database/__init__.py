"""
wikia.common.mediawiki.database
===============================

MediaWiki database connection management
"""

import json
import pkg_resources

from .connection import LoadBalancer
from .config import Config

MASTER = Config.MASTER
SLAVE = Config.SLAVE

__version__ = json.loads(pkg_resources.resource_string(__name__, 'build.json'))['version']
