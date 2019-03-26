# -*- coding: utf-8 -*-
"""Module for json-format logger that output messages compatible with Wikia k8s/elk stack."""

__author__ = "mech"

from datetime import datetime
import logging.config
import time

import pythonjsonlogger.jsonlogger


class WikiaJsonLogsFormatter(pythonjsonlogger.jsonlogger.JsonFormatter):
    """
    Formats json log entries

    This sets the following fields:
        * '@timestamp' log entry timestamp
        * 'level' log entry severity
        * 'appname' application name
        * '@version' application version
        * 'instance_id' string identifier generated once for the application run, allows to group logs from a single run
        * '@message' main log entry message field
    """

    def __init__(self, appname, version, *args, **kwargs):
        self.appname = appname
        self.version = version
        self.instance_id = int(time.time())
        super(WikiaJsonLogsFormatter, self).__init__(*args, **kwargs)

    def add_fields(self, log_record, record, message_dict):
        super(WikiaJsonLogsFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('@timestamp'):
            log_record['@timestamp'] = datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        if log_record.get('level'):
            log_record['level'] = log_record['level']
        else:
            log_record['level'] = record.levelname.lower()

        if not log_record.get('@message') and 'message' in log_record:
            log_record['@message'] = log_record['message']
            del log_record['message']

        log_record['appname'] = self.appname
        log_record['@version'] = self.version
        log_record['instance_id'] = self.instance_id


def configure(app_name, version, level, formatter_config=None):
    """
    configures Python logging module to output json messages

    :param app_name: name of the application that will be put into logs
    :param version: application version
    :param level: logging level
    :param formatter_config: customized formatter parametes, can override the formatter
        class and alter constructor parameters
    """
    cfg = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'default': {
                'level': level,
                'class': 'logging.StreamHandler',
                'formatter': 'wikiaLogsFormatter',
                'stream': 'ext://sys.stdout'
            },
        },
        'formatters': {
            'wikiaLogsFormatter': {
                '()': WikiaJsonLogsFormatter,
                'appname': app_name,
                'version': version,
                'fmt': '(@timestamp) (level) (name) (@message) (message)'
            }
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': level,
                'propagate': True
            }
        }
    }
    if formatter_config is not None:
        cfg['formatters']['wikiaLogsFormatter'].update(formatter_config)
    logging.config.dictConfig(cfg)
