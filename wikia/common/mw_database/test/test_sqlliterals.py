import unittest

from ..sqlliterals import SqlLiteral


class SqlLiteralTest(unittest.TestCase):

    def test_raw_string(self):
        cases = [
            [
                ('asd',[]),
                ('asd',{})
            ],
            [
                ('fk_id = %s', ['a']),
                ('fk_id = %(lsqid_312__index_0)s', {'lsqid_312__index_0': 'a'})
            ],
            [
                ('fk_id = %(xqa)s', {'xqa': 'a'}),
                ('fk_id = %(lsqid_312__key_xqa)s', {'lsqid_312__key_xqa': 'a'})
            ],
            [
                ('fk_id = %(xqa)s OR pq_id > %(id)d', {'xqa': 'a', 'id': 2}),
                ('fk_id = %(lsqid_312__key_xqa)s OR pq_id > %(lsqid_312__key_id)d',
                 {'lsqid_312__key_xqa': 'a', 'lsqid_312__key_id': 2})
            ],
            [
                ('fk_id = %s OR xd_id IN (%d, %d)', ['a', 3, 5]),
                ('fk_id = %(lsqid_312__index_0)s OR xd_id IN (%(lsqid_312__index_1)d, %(lsqid_312__index_2)d)',
                 {'lsqid_312__index_0': 'a', 'lsqid_312__index_1': 3, 'lsqid_312__index_2': 5})
            ]
        ]

        for input, (out_text, out_args) in cases:
            SqlLiteral.LITERAL_SEQ_ID = 312
            literal = SqlLiteral(*input)
            assert literal.text == out_text
            assert tuple(literal.args.items()) == tuple(out_args.items())
