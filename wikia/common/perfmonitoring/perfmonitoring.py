"""
perfmonitoring.py
===============

This module allows you to send performance metrics to InfluxDB
"""

from __future__ import absolute_import

import logging
import os

from influxdb import InfluxDBClient


class InfluxDBSettings(object):
    """
    Wraps InfluxDB connection settings

    Returns settings matching the environment
    """
    def __init__(self, environ=os.environ):
        self._is_dev = environ.get('WIKIA_ENVIRONMENT', 'dev') == 'dev'

        # TODO: store settings in a better place
        self._settings = {
            'prod': {
                "host": 'graph-s3',
                "port": 8086,
                "username": 'root',
                "password": 'root',
                "database": "site",
                #"use_udp": True,  # TODO
            },
            'dev': {
                "host": 'graph-s3',
                "port": 8086,
                "username": 'root',
                "password": 'root',
                "database": "test",
                #"use_udp": True,  # TODO
            }
        }

    def is_dev(self):
        return self._is_dev

    def get_settings(self):
        if self.is_dev():
            return self._settings['dev']
        else:
            return self._settings['prod']


class PerfMonitoring(object):
    """
    Wraps metrics and pushes them to InfluxDB
    """
    def __init__(self, app, series_name='metrics'):
        self._logger = logging.getLogger('PerfMonitoring')

        self._series_name = "%s_%s" % (app.lower(), series_name.lower())
        self._metrics = {}

        params = InfluxDBSettings().get_settings()
        self._logger.debug("Connecting to %s", params)

        self._influx_db = InfluxDBClient(**params)

        self._logger.debug("Metrics will be pushed to '%s'", self.get_series_name())

    def get_series_name(self):
        """
        Gets formatted series name that will be pushed to InfluxDB

        <app name>.<series name>
        """
        return self._series_name

    def set(self, name, value):
        """
        Sets the value of a givem metric
        """
        self._metrics[name] = value

    def inc(self, name, inc=1):
        """
        Increments the value of a givem metric
        """
        if name not in self._metrics:
            self._metrics[name] = 0

        self._metrics[name] += inc

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
