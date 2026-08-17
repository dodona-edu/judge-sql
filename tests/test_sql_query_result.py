"""Test SQLQueryResult."""

import textwrap
import unittest

import pandas as pd

from judge.sql_query_result import SQLQueryResult


class TestSQLQueryResult(unittest.TestCase):
    """SQLQueryResult TestCase."""

    def test_init1(self):
        query_result = SQLQueryResult(
            pd.DataFrame(
                {
                    "col1": [19, 11, 17, 18],
                    "col3": ["Tom", "nick", "krish", "jack"],
                    "col2": [20, 21, 19, 18],
                }
            ),
            ["col1", "col3", "col2"],
            [int, str, int],
        )

        self.assertMultiLineEqual(
            query_result.csv_out,
            textwrap.dedent("""\
                col1,col3,col2
                19,Tom,20
                11,nick,21
                17,krish,19
                18,jack,18"""),
        )
        self.assertMultiLineEqual(
            query_result.types_out,
            textwrap.dedent("""\
                col1 [INTEGER]
                col3 [TEXT]
                col2 [INTEGER]"""),
        )

        self.assertSequenceEqual(query_result.columns, ["col1", "col3", "col2"])
        query_result.index_columns(["col3", "col1", "non_existing"])  # should keep all columns & not add non_existing
        query_result.sort_rows(["col3", "col1", "non_existing"])

        self.assertMultiLineEqual(
            query_result.csv_out,
            textwrap.dedent("""\
                col3,col1,col2
                Tom,19,20
                jack,18,18
                krish,17,19
                nick,11,21"""),
        )
        self.assertMultiLineEqual(
            query_result.types_out,
            textwrap.dedent("""\
                col3 [TEXT]
                col1 [INTEGER]
                col2 [INTEGER]"""),
        )

    def test_init2(self):
        query_result = SQLQueryResult(
            pd.DataFrame(
                [["tom", 2, 10], ["nick", 2, 15], ["juli", 2, 14]],
            ),
            ["Name", "Test", "Name"],
            [str, int, int],
        )

        self.assertMultiLineEqual(
            query_result.csv_out,
            textwrap.dedent("""\
                Name,Test,Name
                tom,2,10
                nick,2,15
                juli,2,14"""),
        )
        self.assertMultiLineEqual(
            query_result.types_out,
            textwrap.dedent("""\
                Name [TEXT]
                Test [INTEGER]
                Name [INTEGER]"""),
        )

        query_result.index_columns(["Name", "Test"])  # should keep both columns & keep ordering (stable)
        query_result.sort_rows(["Name"])

        self.assertMultiLineEqual(
            query_result.csv_out,
            textwrap.dedent("""\
                Name,Test,Name
                juli,2,14
                nick,2,15
                tom,2,10"""),
        )
        self.assertMultiLineEqual(
            query_result.types_out,
            textwrap.dedent("""\
                Name [TEXT]
                Test [INTEGER]
                Name [INTEGER]"""),
        )

        query_result.sort_rows([])  # noop

        self.assertMultiLineEqual(
            query_result.csv_out,
            textwrap.dedent("""\
                Name,Test,Name
                juli,2,14
                nick,2,15
                tom,2,10"""),
        )
        self.assertMultiLineEqual(
            query_result.types_out,
            textwrap.dedent("""\
                Name [TEXT]
                Test [INTEGER]
                Name [INTEGER]"""),
        )
