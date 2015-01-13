#!/usr/bin/env python2
"""
Example script for wikia.common.kibana
"""

import json
import logging

from wikia.common.kibana import Kibana


logging.basicConfig(level=logging.INFO)
source = Kibana(period=3600)

rows = source.get_rows(match={"tags": 'edge-cache-requestmessage'})
print json.dumps(rows, indent=True)

rows = source.query_by_string(query='@message:"^PHP Fatal Error"', limit=2000)
print json.dumps(rows, indent=True)
