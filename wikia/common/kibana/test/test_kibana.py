"""
Set of unit tests for kibana.py
"""
import time
import unittest

from ..kibana import Kibana


class KibanaTestClass(unittest.TestCase):
    """
    Unit tests for Kibana class
    """
    @staticmethod
    def test_indexes():
        instance = Kibana()
        assert instance._index.startswith('logstash-')

    @staticmethod
    def test_format_index():
        assert Kibana.format_index(1) == 'logstash-1970.01.01'
        assert Kibana.format_index(1408450795) == 'logstash-2014.08.19'

    def test_time(self):
        now = int(time.time())

        cases = [
            # till now
            {
                "since": None,
                "expected_since": now - 60,
                "expected_to": now - 5,
                "period": 60
            },
            # strictly defined time period
            {
                "since": 12345,
                "expected_since": 12346,
                "expected_to": now - 5,
                "period": 600
            }
        ]

        for case in cases:
            self.check_time(**case)

    @staticmethod
    def check_time(since, expected_since, expected_to, period):
        instance = Kibana(since, period)

        assert instance._since == expected_since
        assert instance.get_to_timestamp() == expected_to

    @staticmethod
    def test_get_timestamp_filer():
        instance = Kibana(123456, 60)
        res = instance._get_timestamp_filer()

        assert res['range']['@timestamp'] is not None
        assert res['range']['@timestamp']['from'] == '1970-01-02T10:17:37.000Z'
        assert res['range']['@timestamp']['to'] is not None

    @staticmethod
    def test_get_search_body():
        instance = Kibana(123456, 60)

        match = 'foo-match'
        facet_field = 'facets'
        aggregations = 'aggregations'

        body = instance._get_search_body(match, facet_field, aggregations)

        assert body['size'] == 0
        assert body['query']['match'] == match
        assert body['aggregations']['field']['aggregations'] is not None
