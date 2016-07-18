from contextlib import closing
import logging
import random
import MySQLdb
import time
import six
import sys

import wikia.common.logger


logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, raw_connection, connection_info=None):
        self.raw_connection = raw_connection
        self.connection_info = connection_info
        self.query = ConnectionQueryBuilder(self)
        self.__logger = None

    @property
    def logger(self):
        if self.__logger is None:
            self.__logger = wikia.common.logger.Logger.get(__name__)
        return self.__logger

    def close(self):
        self.raw_connection.close()

    def escape_string(self, s):
        return self.raw_connection.escape_string(s)

    def cursor(self):
        return self.raw_connection.cursor()

    def _query(self, query, *args, **kwargs):
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
                extra.update(self.connection_info.__dict__ or {})
                extra.pop('password', None)
                extra['affected'] = affected
                extra['elapsed'] = time.time() - time_started

                try:
                    extra['script'] = sys.modules['__main__'].__file__
                except Exception:
                    extra['script'] = 'interactive?'

                self.logger.info('SQL - {}'.format(query), extra=extra)

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



class SqlBuilderMixin(object):
    def query(self, *args, **kwargs):
        raise NotImplementedError('Inheritors must overrie SqlBuilderMixin.query')

    def select_as_dicts(self, table, what, where):
        return self.select(table, what, where).to_dicts

    def select(self, table, what, where):
        """
        Execute SELECT statement
        :param table:
        :param what:
        :param where:
        :return:
        :rtype: QueryResult
        """
        sql_data = {}
        where_clause = self.where(where, sql_data)
        sql = 'SELECT {} FROM {} WHERE {};'.format(what, table, where_clause)

        return self.query(sql, args=sql_data)

    def insert(self, table, data, ignore_errors=False):
        """
        Execute INSERT statement

        :param table: Table name
        :param data: Dictionary with data
        :param ignore_errors: Option flag to ignore duplicated-class errors durign query execution
        :return:
        :rtype: QueryResult
        """
        columns = []
        values = []
        sql_data = {}
        for column, value in data.items():
            columns.append(column)
            sql_value, is_value = self.add_value(value, sql_data, column)
            if not is_value:
                raise ValueError('insert accepts only value literals')
            values.append(sql_value)
        ignore = ''
        if ignore_errors:
            ignore = 'IGNORE '

        sql = 'INSERT {}INTO {}({}) VALUES ({});'.format(ignore, table, ', '.join(columns), ', '.join(values))

        return self.query(sql, args=sql_data)

    def update(self, table, data, conds):
        """
        Execute UPDATE statement

        :param table: Table name
        :param data: Dictionary with data to be updated
        :param conds: Conditions
        :return:
        :rtype: QueryResult
        """
        sql_data = {}
        set_clause = []
        where_clause = []
        for k, v in data.items():
            self.add_condition(k, v, set_clause, sql_data, 'data_')
        where_clause = self.where(conds, sql_data, 'conds_')

        sql = 'UPDATE {} SET {} WHERE {};'.format(table, ', '.join(set_clause), where_clause)

        return self.query(sql, args=sql_data)

    def delete(self, table, where):
        """
        Execute DELETE statement

        :param table: Table name
        :param where: Conditions
        :return:
        :rtype: QueryResult
        """
        sql_data = {}
        sql = 'DELETE FROM {} WHERE {};'.format(table, self.where(where, sql_data))

        return self.query(sql, args=sql_data)

    def where(self, conds, sql_data, prefix=''):
        clause = []
        if conds is not None:
            for k, v in conds.items():
                self.add_condition(k, v, clause, sql_data, prefix)

        if len(clause) == 0:
            clause = ['1 = 1']

        return ' AND '.join(clause)

    def add_condition(self, key, value, clause, sql_data, prefix=''):
        sql_value, is_value = self.add_value(value, sql_data, prefix + key)
        if is_value:
            clause.append('{} = {}'.format(key, sql_value))
        else:
            clause.append(sql_value)

    def add_value(self, value, sql_data, value_name):
        is_sql_literal = hasattr(value, 'IS_SQL_LITERAL')

        if not is_sql_literal:
            sql_data[value_name] = value
            return '%({})s'.format(value_name), True
        else:
            sql_data.update(value.args)
            return value.text, value.is_value


class ConnectionQueryBuilder(SqlBuilderMixin):
    def __init__(self, connection):
        self.connection = connection

    def __call__(self, *args, **kwargs):
        return self.query(*args, **kwargs)

    def query(self, *args, **kwargs):
        """
        Execute query

        :param sql_text: SQL query text
        :param args: SQL query values
        :return:
        :rtype: QueryResult
        """
        return self.connection._query(*args, **kwargs)

    def select_field(self, table, what, where):
        return self.select(table, what, where).all_rows[0][0]


class QueryResult(object):
    def __init__(self, query, query_args, query_kwargs, affected, description, all_rows):
        self.query = query
        self.query_args = query_args
        self.query_kwargs = query_kwargs
        self.affected = affected
        self.description = description
        self.all_rows = all_rows

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
