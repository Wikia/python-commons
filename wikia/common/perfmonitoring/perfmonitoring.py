"""
perfmonitoring.py
===============

This module allows you to send performance metrics to InfluxDB
"""

import logging
import os

from influxdb import InfluxDBClient


class InfluxDBSettings(object):
    """
    Wraps InfluxDB connection settings

    Returns settings matching the environment
    """
    def __init__(self, environ=None):
        if environ is None:
            self._environ = os.environ
        else:
            self._environ = environ

    @property
    def is_dev(self):
        """
        Is the current environment a development one?
        """
        return self._environ.get('WIKIA_ENVIRONMENT', 'dev') == 'dev'

    @property
    def settings(self):
        """
        Return InfluxDB settings for a current environment
        """
        settings = {
            'prod': {
                "host": 'graph-s3',
                "udp_port": 4444,
                "use_udp": True,
            },
            'dev': {
                "host": 'graph-s3',
                "udp_port": 5551,
                "use_udp": True,
            }
        }

        if self.is_dev:
            return settings['dev']
        else:
            return settings['prod']


class PerfMonitoring(object):
    """
    Wraps metrics and pushes them to InfluxDB
    """
    def __init__(self, app_name, series_name='metrics', influx_db=None):
        self._logger = logging.getLogger('PerfMonitoring')

        self._series_name = "%s_%s" % (app_name.lower(), series_name.lower())
        self._metrics = {}

        if influx_db is None:
            settings = InfluxDBSettings().settings
            self._logger.debug("Connecting to %s", settings)

            self._influx_db = InfluxDBClient(**settings)
        else:
            # handle dependency injection
            self._influx_db = influx_db

        self._logger.debug("Metrics will be pushed to '%s'", self.get_series_name())

    def get_series_name(self):
        """
        Gets formatted series name that will be pushed to InfluxDB

        <app name>.<series name>
        """
        return self._series_name

    def set(self, name, value):
        """
        Sets the value of a given metric
        """
        self._metrics[name] = value

    def inc(self, name, inc=1):
        """
        Increments the value of a given metric
        """
        if name not in self._metrics:
            self._metrics[name] = 0

        self._metrics[name] += inc

    def get(self, name, default=None):
        """
        Return the value of a given metric (or default if not set)
        """
        return self._metrics.get(name, default)

    def push(self):
        """
        Pushes collected metrics to InfluxDB
        """
        self._logger.debug("Pushing metrics to '%s': %s", self.get_series_name(), self._metrics)

        points = [{
            'columns': self._metrics.keys(),
            'name': self.get_series_name(),
            'points': [self._metrics.values()]
        }]

        self._influx_db.write_points(points)
