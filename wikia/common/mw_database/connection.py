from contextlib import closing
import logging
import random
import MySQLdb
import time
import six
import sys

from .query_builder import SqlBuilderMixin
import wikia.common.logger


logger = logging.getLogger(__name__)


class Connection(SqlBuilderMixin):
    def __init__(self, raw_connection, connection_info=None):
        self.raw_connection = raw_connection
        self.connection_info = connection_info
        self.__logger = None

    @property
    def logger(self):
        if self.__logger is None:
            self.__logger = wikia.common.logger.Logger.get(__name__, level=logging.INFO)
        return self.__logger

    def close(self):
        self.raw_connection.close()

    def escape_string(self, s):
        return self.raw_connection.escape_string(s)

    def cursor(self):
        return self.raw_connection.cursor()

    def query(self, query, *args, **kwargs):
        log_text = 'SQL Query: {}'.format(query)
        if 'args' in kwargs and len(kwargs['args']) > 0:
            if "\n" in query:
                log_text += "\n"
            log_text += ' (with args: {})'.format(kwargs['args'])
        logger.debug(log_text)
        def do_exec_query(cursor):
            time_started = time.time()

            returned = cursor.execute(query, *args, **kwargs)
            affected = cursor.rowcount
            all_rows = cursor.fetchall()

            # log SQL - sampled at 1%
            if random.random() < 0.01:
                extra = {}
                try:
                    extra.update(self.connection_info.__dict__)
                except Exception:
                    pass
                extra.pop('password', None)
                extra['num_rows'] = affected
                extra['elapsed'] = time.time() - time_started

                try:
                    extra['script'] = sys.modules['__main__'].__file__
                except Exception:
                    extra['script'] = 'interactive?'

                self.logger.info('SQL {}'.format(query), extra=extra)

            return QueryResult(query, args, kwargs, affected, cursor.description, all_rows)

        if 'cursor' in kwargs:
            return do_exec_query(kwargs.pop('cursor'))
        else:
            with closing(self.cursor()) as cursor:
                return do_exec_query(cursor)

    def exec_sql_script_at_once(self, sql_script):
        with closing(self.cursor()) as cursor:
            with open(sql_script, 'r') as fp:
                cursor.execute(fp.read())
            self.commit()

    def exec_sql_script(self, sql_script, ignore_duplicates=None):
        with closing(self.cursor()) as cursor:
            statement = ''
            for line in open(sql_script):
                stripped = line.strip()
                if stripped == '' or stripped[:2] == '--':  # ignore sql comment lines
                    continue
                statement += line
                if stripped[-1] == ';':  # keep appending lines that don't end with ';'
                    logger.debug('SQL Script: {}'.format(sql_script))
                    logger.debug('SQL Statement: {}'.format(statement))
                    try:
                        cursor.execute(statement)
                    except MySQLdb.OperationalError as e:
                        # 1050 - Table X already exists
                        # 1060 - Duplicate column name X
                        # 1061 - Duplicate key name X
                        if ignore_duplicates:
                            if e.args[0] not in (1050, 1060, 1061):
                                raise
                    statement = ''
            if statement.strip() != '':
                logger.debug('SQL Script: {}'.format(sql_script))
                logger.debug('SQL Statement: {}'.format(statement))
                cursor.execute(statement)
            self.commit()

    def last_insert_id(self):
        return self.raw_connection.insert_id()

    def commit(self):
        self.raw_connection.commit()


class QueryResult(object):
    def __init__(self, query, query_args, query_kwargs, affected, description, all_rows):
        self.query = query
        self.query_args = query_args
        self.query_kwargs = query_kwargs
        self.affected = affected
        self.description = description
        self.all_rows = all_rows
        self.num_rows = len(all_rows)

    @property
    def to_dicts(self):
        column_names = [column[0] for column in self.description]
        column_range = range(len(column_names))
        res = []
        for row in self.all_rows:
            res.append({column_names[i]: row[i] if not isinstance(row[i], (str, six.text_type)) else str(row[i])
                        for i in column_range
                        })
        return res

    def __iter__(self):
        return iter(self.all_rows)
