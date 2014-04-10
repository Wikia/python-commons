import logging
import logging.handlers
import json


class Logger(logging.getLoggerClass()):
    def __init__(self, name):
        super(Logger, self).__init__(name)
        Logger.__use(self, overwrite_make_record=False)

    def makeRecord(self, name, lvl, fn, lno, msg, args, exc_info, func=None, extra=None):
        return Logger.__make_record(name, lvl, fn, lno, msg, args, exc_info, func, extra)

    @staticmethod
    def __make_record(name, lvl, fn, lno, msg, args, exc_info, func=None, extra=None):
        record = LogRecord(name, lvl, fn, lno, msg, args, exc_info, func)
        record.set_extra(extra)
        return record

    @staticmethod
    def use(logger, level=None):
        return Logger.__use(logger, level)

    @staticmethod
    def __use(logger, level=None, overwrite_make_record=True):
        handler = logging.handlers.SysLogHandler(address='/dev/log')
        handler.setFormatter(LogFormatter())

        if level is not None:
            handler.setLevel(level)

        logger.addHandler(handler)

        if overwrite_make_record:
            logger.makeRecord = Logger.__make_record

        return logger

    @staticmethod
    def get(name='WikiaLogger', app_name='python', level=None):
        current = logging.getLoggerClass()
        logging.setLoggerClass(Logger)
        logger = logging.getLogger(name)
        LogRecord.app_name = app_name

        if level is not None:
            logger.setLevel(level)

        logging.setLoggerClass(current)
        return logger


class LogFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {'@message': record.msg}

        if record.extra is not None:
            log_obj['@fields'] = record.extra

        result = ''.join([LogRecord.app_name, ': ', json.dumps(log_obj)])
        return result


class LogRecord(logging.LogRecord):
    app_name = 'python'

    def __init__(self, *args, **kwargs):
        logging.LogRecord.__init__(self, *args, **kwargs)
        self.extra = None

    def set_extra(self, extra):
        self.extra = extra
