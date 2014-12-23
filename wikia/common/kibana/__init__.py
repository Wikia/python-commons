"""
wikia.common.kibana
===================

Run queries against Kibana's Elasticsearch
"""

import json
import pkg_resources

from .kibana import Kibana

__version__ = json.loads(pkg_resources.resource_string(__name__, 'build.json'))['version']
