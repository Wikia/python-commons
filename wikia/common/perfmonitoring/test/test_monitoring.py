"""
Unit tests for PerfMonitoring class
"""

import unittest
from mock import MagicMock

from ..perfmonitoring import PerfMonitoring


class PerfMonitoringTest(unittest.TestCase):
    """
    Test PerfMonitoring
    """
    def test_get_series_name(self):
        """
        Test get_series_name() method
        """
        cases = [
            {
                "app_name": 'Foo',
                "expected_series_name": 'foo_metrics'
            },
            {
                "app_name": 'foo',
                "expected_series_name": 'foo_metrics'
            },
            {
                "app_name": 'app',
                "series_name": 'Perf_Data',
                "expected_series_name": 'app_perf_data'
            }
        ]

        for case in cases:
            self.check_get_series_name(**case)

    @staticmethod
    def check_get_series_name(expected_series_name=None, **kwargs):
        assert PerfMonitoring(**kwargs).get_series_name() == expected_series_name

    @staticmethod
    def test_set_inc():
        """
        Test set() and inc() methods
        """
        metrics = PerfMonitoring(app_name='MyApp')

        assert metrics.get('foo') is None

        # inc
        metrics.inc('foo')
        assert metrics.get('foo') == 1
        metrics.inc('foo', 3)
        assert metrics.get('foo') == 4

        metrics.set('foo', 42)
        assert metrics.get('foo') == 42

        # set to number
        metrics.set('bar', 2)
        assert metrics.get('bar') == 2

        # set to string
        metrics.set('action', 'test')
        assert metrics.get('action') == 'test'

    @staticmethod
    def test_push():
        """
        Test push() method
        """
        influx_db = MagicMock()
        metrics = PerfMonitoring(app_name='MyApp', influx_db=influx_db)

        metrics.set('foo', 'bar')
        metrics.set('name', 42)

        metrics.push()
        influx_db.write_points.assert_called_with([
            {
                'points': [['bar', 42]],
                'name': 'myapp_metrics',
                'columns': ['foo', 'name']
            }
        ])
