"""
Run queries against Kibana's elasticsearch
@see http://elasticsearch-py.readthedocs.org/en/master/
"""
import json
import logging
import time

from datetime import datetime
from dateutil import tz
from itertools import islice

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan


class KibanaError(Exception):
    pass


class Kibana(object):
    # give 5 seconds for all log messages to reach logstash and be stored in elasticsearch
    SHORT_DELAY = 5

    # seconds in 24h used to get the es index for yesterday
    DAY = 86400

    ELASTICSEARCH_HOST = 'logs-prod.es.service.sjc.consul'  # ES5

    """ Interface for querying Kibana's storage """
    def __init__(self, since=None, period=900, es_host=None, read_timeout=10, index_prefix='logstash-other',
                 batch_size=1000):
        """
        :type since int
        :type period int
        :type es_host str
        :type read_timeout int
        :type index_prefix str
        :type batch_size int

        :arg since: UNIX timestamp data should be fetched since
        :arg period: period (in seconds) before now() to be used when since is empty (defaults to last 15 minutes)
        :arg es_host: customize Elasticsearch host(s) that should be used for querying
        :arg read_timeout: customize Elasticsearch read timeout (defaults to 10 s)
        :arg index_prefix name of the Elasticsearch index (defaults to 'logstash-other')
        :arg batch_size size of the batch sent in every requests of the ELK scroll API (defaults to 1000)
        """
        self._es = Elasticsearch(hosts=es_host if es_host else self.ELASTICSEARCH_HOST, timeout=read_timeout)
        self._batch_size = batch_size

        self._logger = logging.getLogger('kibana')

        # if no timestamp provided, fallback to now() in UTC
        now = int(time.time())

        if since is None:
            since = now - period
        else:
            since += 1
            self._logger.info("Using provided {0} timestamp as since ({1} seconds ago)".format(since, now - since))

        self._since = since
        self._to = now - self.SHORT_DELAY  # give logs some time to reach Logstash

        # Elasticsearch index to query
        # from today and yesterday
        self._index = ','.join([
            self.format_index(index_prefix, now-self.DAY),
            self.format_index(index_prefix, now),
        ])

        self._logger.info("Using {} indices".format(self._index))
        self._logger.info("Querying for messages from between {} and {}".
                          format(self.format_timestamp(self._since), self.format_timestamp(self._to)))

    @staticmethod
    def format_index(prefix, ts):
        """
        :type prefix str
        :type ts int
        :rtype: str
        """
        tz_info = tz.tzutc()

        # ex. logstash-other-2017.05.09
        return "{prefix}-{date}".format(prefix=prefix, date=datetime.fromtimestamp(ts, tz=tz_info).strftime('%Y.%m.%d'))

    @staticmethod
    def format_timestamp(ts):
        """
        Format the UTC timestamp for Elasticsearch
        eg. 2014-07-09T08:37:18.000Z

        @see https://docs.python.org/2/library/time.html#time.strftime
        """
        tz_info = tz.tzutc()
        return datetime.fromtimestamp(ts, tz=tz_info).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def _get_timestamp_filer(self):
        return {
            "range": {
                "@timestamp": {
                    "gte": self.format_timestamp(self._since),
                    "lte": self.format_timestamp(self._to)
                }
            }
        }

    def _search(self, query, limit=50000, sampling=None):
        """
        Perform the search and return raw rows

        :type query object
        :type limit int
        :type sampling int or None

        :arg sampling: Percentage of results to be returned (0,100)

        :rtype: list
        """
        body = {
            "query": {
                "bool": {
                    "must": [
                        query
                    ]
                }
            }
        }

        # add @timestamp range
        # @see http://stackoverflow.com/questions/40996266/elasticsearch-5-1-unknown-key-for-a-start-object-in-filters
        # @see https://discuss.elastic.co/t/elasticsearch-watcher-error-for-range-query/70347/2
        body['query']['bool']['must'].append(self._get_timestamp_filer())

        # sample the results if needed
        if sampling is not None:
            body['query']['bool']['must'].append({
                'script': {
                    'script': {
                        'lang': 'painless',
                        'source': "Math.abs(doc['_id'].value.hashCode()) % 100 < params.sampling",
                        'params': {
                            'sampling': sampling
                        }
                    }
                }
            })

        self._logger.debug("Running {} query (limit set to {:d})".format(json.dumps(body), body.get('size', 0)))

        # use Scroll API to be able to fetch more than 10k results and prevent "search_phase_execution_exception":
        # "Result window is too large, from + size must be less than or equal to: [10000] but was [500000].
        # See the scroll api for a more efficient way to request large data sets."
        #
        # @see http://elasticsearch-py.readthedocs.io/en/master/helpers.html#scan
        rows = scan(
            client=self._es,
            clear_scroll=False,  # True causes "403 Forbidden: You don't have access to this resource"
            index=self._index,
            query=body,
            sort=["_doc"],  # return the next batch of results from every shard that still has results to return.
            size=self._batch_size,  # batch size
        )

        # get only requested amount of entries and cast them to a list
        rows = islice(rows, 0, limit)
        rows = [entry['_source'] for entry in rows]  # get data

        self._logger.info("{:d} rows returned".format(len(rows)))
        return rows

    def get_rows(self, match, limit=10, sampling=None):
        """
        Returns raw rows that matches given query

        :arg match: query to be run against Kibana log messages (ex. {"@message": "Foo Bar DB queries"})
        :arg limit: the number of results (defaults to 10)
        :type sampling int or None
        :arg sampling: Percentage of results to be returned (0,100)
        """
        query = {
            "match": match,
        }

        return self._search(query, limit, sampling)

    def query_by_string(self, query, limit=10, sampling=None):
        """
        Returns raw rows that matches the given query string

        :arg query: query string to be run against Kibana log messages (ex. @message:"^PHP Fatal").
        :arg limit: the number of results (defaults to 10)
        :type sampling int or None
        :arg sampling: Percentage of results to be returned (0,100)
        """
        query = {
            "query_string": {
                "query": query,
            }
        }

        return self._search(query, limit, sampling)

    def get_to_timestamp(self):
        """ Return the upper time boundary to returned data """
        return self._to

    def get_aggregations(self, query, group_by, stats_field, percents=(50, 95, 99, 99.9), size=100):
        """
        Returns aggregations (rows count + percentile stats) for a given query

        This is basically the same as the following pseudo-SQL query:
        SELECT PERCENTILE(stats_field, 75) FROM query GROUP BY group_by LIMIT size

        https://www.elastic.co/guide/en/elasticsearch/reference/5.5/search-aggregations-bucket-terms-aggregation.html
        https://www.elastic.co/guide/en/elasticsearch/reference/5.5/search-aggregations-metrics-percentile-aggregation.html

        Please note that group_by should be provided by a "keyword" field:

        Fielddata is disabled on text fields by default. Set fielddata=true on [@context.caller] in order to load
        fielddata in memory by uninverting the inverted index. Note that this can however use significant memory.\
        Alternatively use a keyword field instead.

        :type query str
        :type group_by str
        :type stats_field str
        :type percents set
        :type size int
        :rtype: dict
        """
        body = {
            "query": {
                "bool": {
                    "must": [{
                        "query_string": {
                            "query": query,
                        },
                    }]
                },
            },
            "aggregations": {
                "group_by_agg": {
                    "terms": {
                        "field": group_by,
                        "size": size,  # how many term buckets should be returned out of the overall terms list
                    },
                    "aggregations": {
                        "field_stats": {
                            "percentiles": {
                                "field": stats_field,
                                "percents": percents
                            }
                        }
                    }
                }
            }
        }

        # add @timestamp range
        body['query']['bool']['must'].append(self._get_timestamp_filer())

        self._logger.info("Getting aggregations for {} field when grouped by {}".format(group_by, stats_field))

        res = self._es.search(
            body=body,
            index=self._index,
            size=0,  # we don need any rows from the index, stats is all we need here
        )

        # print(json.dumps(res, indent=True))

        aggs = {}

        """
        bucket = {
            "field_stats": {
                "values": {
                    "95.0": 20.99858477419025,
                    "99.0": 67.0506954238478,
                    "50.0": 1.0,
                    "99.9": 146.3865495436944
                }
            },
            "key": "Wikia\\Service\\Gateway\\ConsulUrlProvider:getUrl",
            "doc_count": 8912859
        }
        """
        for bucket in res['aggregations']['group_by_agg']['buckets']:
            entry = {
                "count": bucket['doc_count']
            }
            entry.update(bucket['field_stats']['values'])

            aggs[bucket['key']] = entry

        return aggs
