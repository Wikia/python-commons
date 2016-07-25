import unittest

from ..connection import SqlBuilderMixin
from ..sqlliterals import SqlLiteral, SqlCondition


def dict_eq(d1, d2):
    ds = [
        tuple(sorted(d.items(), key=lambda kv: kv[0]))
        for d in [d1,d2]
        ]
    return ds[0] == ds[1]

def create_sql_literal(lsqid, *args, **kwargs):
    SqlLiteral.LITERAL_SEQ_ID = lsqid
    return SqlLiteral(*args, **kwargs)

def create_sql_condition(lsqid, *args, **kwargs):
    SqlLiteral.LITERAL_SEQ_ID = lsqid
    return SqlCondition(*args, **kwargs)


class QueryBuilderRecorder(SqlBuilderMixin):
    def query(self, *args, **kwargs):
        self.q_args = args
        self.q_kwargs = kwargs

class SqlLiteralTest(unittest.TestCase):
    def test_select(self):
        cases = [
            [
                ['ab_config', '*', None],
                ["SELECT * FROM ab_config WHERE 1 = 1;", {}]
            ],
            [
                ['ab_config', '*', {'ab_id': 3}],
                ["SELECT * FROM ab_config WHERE ab_id = %(ab_id)s;", {'ab_id': 3}]
            ],
            [
                ['ab_config', 'asd, zxc as qa', {'ab_id': 3, 's_id': 'qas'}],
                ["SELECT asd, zxc as qa FROM ab_config WHERE s_id = %(s_id)s AND ab_id = %(ab_id)s;", {'ab_id': 3, 's_id': 'qas'}]
            ],
            [
                ['ab_config', 'asd, zxc as qa', {'ab_id': create_sql_condition(312, 'ab_id > %d', [12]), 's_id': create_sql_literal(313, 's2_id')}],
                ["SELECT asd, zxc as qa FROM ab_config WHERE s_id = s2_id AND ab_id > %(lsqid_312__index_0)d;",
                 {'lsqid_312__index_0': 12}]
            ],
        ]

        for input, (out_text, out_args) in cases:
            print input
            SqlLiteral.LITERAL_SEQ_ID = 312
            recorder = QueryBuilderRecorder()
            recorder.select(*input)

            assert len(recorder.q_args) == 1
            assert recorder.q_args[0] == out_text
            assert len(recorder.q_kwargs) == 1
            assert recorder.q_kwargs.keys()[0] == 'args'
            assert dict_eq(recorder.q_kwargs.values()[0], out_args)

    def test_update(self):
        cases = [
            [
                ['ab_config', {'text': 'asd'}, {}],
                ["UPDATE ab_config SET text = %(data_text)s WHERE 1 = 1;", {'data_text': 'asd'}]
            ],
            [
                ['ab_config', {'fk_id': 3}, {'ab_id': 4}],
                ["UPDATE ab_config SET fk_id = %(data_fk_id)s WHERE ab_id = %(conds_ab_id)s;", {'data_fk_id': 3, 'conds_ab_id': 4}]
            ],
            [
                ['ab_config', {'fk_id': create_sql_literal(312, 'current_time()')}, {'ab_id': 4}],
                ["UPDATE ab_config SET fk_id = current_time() WHERE ab_id = %(conds_ab_id)s;", {'conds_ab_id': 4}]
            ]
        ]

        for input, (out_text, out_args) in cases:
            print input
            recorder = QueryBuilderRecorder()
            recorder.update(*input)

            assert len(recorder.q_args) == 1
            assert recorder.q_args[0] == out_text
            assert len(recorder.q_kwargs) == 1
            assert recorder.q_kwargs.keys()[0] == 'args'
            assert dict_eq(recorder.q_kwargs.values()[0], out_args)

    def test_delete(self):
        cases = [
            [
                ['ab_config', {}],
                ["DELETE FROM ab_config WHERE 1 = 1;", {}]
            ],
            [
                ['ab_config', {'text': 'asd'}],
                ["DELETE FROM ab_config WHERE text = %(text)s;", {'text': 'asd'}]
            ],
            [
                ['ab_config', {'fk_id': create_sql_condition(312, 'last_updated > current_time() - interval %d day', [3])}],
                ["DELETE FROM ab_config WHERE last_updated > current_time() - interval %(lsqid_312__index_0)d day;", {'lsqid_312__index_0': 3}]
            ],
            [
                ['ab_config', {'fk_id': create_sql_condition(312, 'last_updated > current_time() - interval %(days)d day', {'days': 3})}],
                ["DELETE FROM ab_config WHERE last_updated > current_time() - interval %(lsqid_312__key_days)d day;", {'lsqid_312__key_days': 3}]
            ]
        ]

        for input, (out_text, out_args) in cases:
            print input
            recorder = QueryBuilderRecorder()
            recorder.delete(*input)

            assert len(recorder.q_args) == 1
            assert recorder.q_args[0] == out_text
            assert len(recorder.q_kwargs) == 1
            assert recorder.q_kwargs.keys()[0] == 'args'
            assert dict_eq(recorder.q_kwargs.values()[0], out_args)

    def test_insert(self):
        cases = [
            [
                ['ab_config', {'a': create_sql_literal(300, 'current_time()'), 'text': 'asd', 'c': create_sql_literal(312, '%d', [33])}],
                ["INSERT INTO ab_config(a, text, c) VALUES (current_time(), %(text)s, %(lsqid_312__index_0)d);", {'text': 'asd', 'lsqid_312__index_0': 33}]
            ]
        ]

        for input, (out_text, out_args) in cases:
            print input
            recorder = QueryBuilderRecorder()
            recorder.insert(*input)

            assert len(recorder.q_args) == 1
            assert recorder.q_args[0] == out_text
            assert len(recorder.q_kwargs) == 1
            assert recorder.q_kwargs.keys()[0] == 'args'
            assert dict_eq(recorder.q_kwargs.values()[0], out_args)
