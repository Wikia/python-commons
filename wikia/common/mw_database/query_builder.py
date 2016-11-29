class SqlBuilderMixin(object):
    def query(self, *args, **kwargs):
        """
        Execute query

        :param sql_text: SQL query text
        :param args: SQL query values
        :return:
        :rtype: QueryResult
        """
        raise NotImplementedError('Inheritors must overrie SqlBuilderMixin.query')

    def select_as_dicts(self, table, what, where):
        return self.select(table, what, where).rows_as_dicts

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
            columns.append('`{}`'.format(column))
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

    def delete(self, table, conds):
        """
        Execute DELETE statement

        :param table: Table name
        :param conds: Conditions
        :return:
        :rtype: QueryResult
        """
        sql_data = {}
        sql = 'DELETE FROM {} WHERE {};'.format(table, self.where(conds, sql_data))

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

    def select_field(self, table, what, where):
        res = self.select(table, what, where)
        if res.num_rows != 1:
            raise ValueError("Query in select_field() returned {} rows instead of 1".format(res.num_rows))
        return res.rows[0][0]
