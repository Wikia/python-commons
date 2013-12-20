import logging
import logging.handlers
import json

class Logger(logging.getLoggerClass()):
	def __init__(self, name):
		super(Logger, self).__init__(name)
		Logger.__use(self, overwriteMakeRecord=False)

	def makeRecord(self, name, lvl, fn, lno, msg, args, exc_info, func=None, extra=None):
		return Logger.__makeRecord(name, lvl, fn, lno, msg, args, exc_info, func, extra)

	@staticmethod
	def __makeRecord(name, lvl, fn, lno, msg, args, exc_info, func=None, extra=None):
		record = LogRecord(name, lvl, fn, lno, msg, args, exc_info, func)
		record.setExtra(extra)
		return record

	@staticmethod
	def use(logger, level=None):
		return Logger.__use(logger, level)
	
	@staticmethod
	def __use(logger, level=None, overwriteMakeRecord=True):
		handler = logging.handlers.SysLogHandler(address='/dev/log')
		handler.setFormatter(LogFormatter())

		if level is not None:
			handler.setLevel(level)

		logger.addHandler(handler)

		if overwriteMakeRecord:
			logger.makeRecord = Logger.__makeRecord
		
		return logger

	@staticmethod
	def get(name='WikiaLogger', appName='python', level=None):
		current = logging.getLoggerClass()
		logging.setLoggerClass(Logger)
		logger = logging.getLogger(name);
		LogRecord.APP_NAME = appName
		
		if level is not None:
			logger.setLevel(level)

		logging.setLoggerClass(current)
		return logger

class LogFormatter(logging.Formatter):
	def format(self, record):
		logObj = { "@message": record.msg }

		if record.extra is not None:
			logObj["@fields"] = record.extra
			
		result = ''.join([LogRecord.APP_NAME, ': ', json.dumps(logObj)])
		return result

class LogRecord(logging.LogRecord):
	APP_NAME = 'python'

	def __init__(self, *args, **kwargs):
		logging.LogRecord.__init__(self, *args, **kwargs)

	def setExtra(self, extra):
		self.extra = extra
