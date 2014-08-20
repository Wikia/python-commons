wikia.common.perfmonitoring
=========================

Send performance metrics to InfluxDB

Basic Usage
-----------

```
from wikia.common.perfmonitoring import PerfMonitoring

# series_name can be skipped, defaults to "metrics"
metrics = PerfMonitoring(app='MyAwesomeService', series_name='metrics')

# add metrics
metrics.set('type', 'get_index')
metrics.inc('queries')
metrics.set('response_time', 231)

# finally push them
metrics.push()
```

Data stored in InfluxDB:

```
test> select * from myawesomeservice_metrics
┌──────────────────┬─────────────────┬─────────┬───────────────┬───────────┐
│       time       │ sequence_number │ queries │ response_time │ type      │
├──────────────────┼─────────────────┼─────────┼───────────────┼───────────┤
│ 20/8/14 16:06:07 │ 10497200001     │ 1       │ 231           │ get_index │
└──────────────────┴─────────────────┴─────────┴───────────────┴───────────┘
Query took  437 ms
```
