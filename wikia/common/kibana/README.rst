wikia.common.kibana
===================

Run queries against Kibana's Elasticsearch.

Basic Usage
-----------

::
	from wikia.common.kibana import Kibana
	source = Kibana(since=12345, period=900)

since: UNIX timestamp data should be fetched since (if None, then period specifies the last n seconds).
period: period (in seconds) before now() to be used when since is empty (defaults to last 15 minutes).

::
	source.get_rows(match={"tags": 'edge-cache-requestmessage'}, limit=2000)

Returns data matching the given query.

match: query to be run against Kibana log messages (ex. {"@message": "Foo Bar DB queries"}).
limit: the number of results (defaults to 10).

::
	source.query_by_string(query='@message:"^PHP Fatal"', limit=2000)

Returns data matching the given query string.

query: query string to be run against Kibana log messages (ex. @message:"^PHP Fatal").
limit: the number of results (defaults to 10).

::
	source.get_to_timestamp()

Returns the upper time boundary for the requested data.
