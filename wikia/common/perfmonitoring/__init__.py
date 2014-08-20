"""
wikia.common.perfmonitoring
=========================

Send performance metrics to InfluxDB
"""

import json
import pkg_resources

from .perfmonitoring import PerfMonitoring


__version__ = json.loads(pkg_resources.resource_string(__name__, 'build.json'))['version']
