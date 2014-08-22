wikia.common.perfmonitoring
=========================

Send performance metrics to InfluxDB via JSON+UDP

Basic Usage
-----------

::


	import logging
	logging.basicConfig(level=logging.DEBUG)

	from wikia.common.perfmonitoring import PerfMonitoring

	# series_name can be skipped, defaults to "metrics"
	metrics = PerfMonitoring(app_name='MyAwesomeService', series_name='metrics')

	# add metrics
	metrics.set('type', 'get_index')
	metrics.inc('queries')
	metrics.set('response_time', 231)

	# finally push them
	metrics.push()

Data stored in InfluxDB (``time`` "metric" is generated automatically if not provided):

::


	test> select * from myawesomeservice_metrics
	┌──────────────────┬─────────────────┬─────────┬───────────────┬───────────┐
	│       time       │ sequence_number │ queries │ response_time │ type      │
	├──────────────────┼─────────────────┼─────────┼───────────────┼───────────┤
	│ 20/8/14 16:06:07 │ 10497200001     │ 1       │ 231           │ get_index │
	└──────────────────┴─────────────────┴─────────┴───────────────┴───────────┘
	Query took  437 ms


Environments
------------

THe package will detect the environment using ``WIKIA_ENVIRONMENT`` variable.

Metrics will be pushed (using JSON over UDP) to either:

* ``site`` database in production
* ``test`` database in dev
