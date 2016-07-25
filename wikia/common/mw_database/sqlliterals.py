import re


class SqlLiteral(object):
    LITERAL_SEQ_ID = 1

    def __init__(self, text, args=None, is_value=True):
        args = args or {}
        arg_prefix = 'lsqid_{}_'.format(self.LITERAL_SEQ_ID)
        self.LITERAL_SEQ_ID += 1
        builder = SqlLiteralBuilder(text, args, arg_prefix)

        self.is_value = is_value
        self.text = builder.text
        self.args = builder.args
        self.IS_SQL_LITERAL = True


class SqlCondition(SqlLiteral):
    def __init__(self, *args, **kwargs):
        kwargs['is_value'] = False
        super(SqlCondition, self).__init__(*args, **kwargs)


class SqlLiteralBuilder(object):
    def __init__(self, text, args, arg_prefix):
        self.input_text = text
        self.input_args = args
        self.arg_prefix = arg_prefix
        self.build()

    def build(self):
        self.arg_index = 0
        self.args_list = []

        self.text = re.sub(r'%(?:\(([^)]+)\))?([sd])', self.register_arg, self.input_text)
        self.args = dict(self.args_list)

        if len(self.input_args) != len(self.args):
            raise ValueError('SQL literal parsing error: arguments counts do not match (got {}, found {})'.format(
                len(self.input_args), len(self.args)))

    def register_arg(self, m):
        if m.group(1):
            value = self.input_args[m.group(1)]
            arg_name = '{}_key_{}'.format(self.arg_prefix, m.group(1))
            self.args_list.append([arg_name, value])
        else:
            value = self.input_args[self.arg_index]
            arg_name = '{}_index_{}'.format(self.arg_prefix, self.arg_index)
            self.args_list.append([arg_name, value])
            self.arg_index += 1

        new_text = '%({}){}'.format(arg_name, m.group(2))

        return new_text
