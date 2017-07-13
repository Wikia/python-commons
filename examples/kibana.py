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

# customize index to query Apache access log
rows = Kibana(period=86400, index_prefix='logstash-apache-access-log').query_by_string(
    query='tags: ("apache_access_log") AND @source_host: /s.*/ AND request: "Special:WikiFactory"', limit=2000)

print json.dumps(rows, indent=True)

# aggregations
stats = Kibana(period=3600, index_prefix='logstash-mediawiki').get_aggregations(
    query='"Http request" AND severity: "debug" AND @fields.datacenter: "SJC" and @field.environment: "prod"',
    group_by='@context.caller.keyword',
    stats_field='@context.requestTimeMS'
)

print json.dumps(stats, indent=True)
