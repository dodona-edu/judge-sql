"""Test SQLQueryResult."""

import sqlite3
import textwrap
import unittest

from judge.sql_query_result import SQLQueryResult


def run_query(query: str) -> SQLQueryResult:
    connection = sqlite3.connect(":memory:")
    try:
        return SQLQueryResult.from_cursor(100, connection.execute(query))
    finally:
        connection.close()


class TestSQLQueryResult(unittest.TestCase):
    """SQLQueryResult TestCase."""

    def test_init1(self):
        query_result = SQLQueryResult(
            [(19, "Tom", 20), (11, "nick", 21), (17, "krish", 19), (18, "jack", 18)],
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
            [("tom", 2, 10), ("nick", 2, 15), ("juli", 2, 14)],
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

    def test_integer_column_with_null(self):
        query_result = run_query("SELECT 1 AS a UNION ALL SELECT NULL UNION ALL SELECT 3")
        self.assertEqual(query_result.csv_out, 'A\n1\n""\n3')

    def test_big_integer_column_with_null(self):
        query_result = run_query("SELECT 9007199254740993 AS a, 'x' AS b UNION ALL SELECT NULL, 'y'")
        self.assertEqual(query_result.csv_out, "A,B\n9007199254740993,x\n,y")

    def test_integer_and_real_column(self):
        query_result = run_query("SELECT 1 AS a UNION ALL SELECT 2.5")
        self.assertEqual(query_result.csv_out, "A\n1\n2.5")

    def test_real_values(self):
        self.assertEqual(run_query("SELECT AVG(x) AS a FROM (SELECT 1 AS x UNION ALL SELECT 3)").csv_out, "A\n2.0")
        self.assertEqual(run_query("SELECT 0.1 + 0.2 AS a").csv_out, "A\n0.30000000000000004")
        self.assertEqual(run_query("SELECT 1e-7 AS a UNION ALL SELECT 1e20").csv_out, "A\n1e-07\n1e+20")

    def test_quoting(self):
        query_result = run_query(
            "SELECT 'a,b' AS a UNION ALL SELECT 'say \"hi\"' UNION ALL SELECT 'line1' || char(10) || 'line2'"
        )
        self.assertEqual(query_result.csv_out, 'A\n"a,b"\n"say ""hi"""\n"line1\nline2"')

    def test_blob(self):
        self.assertEqual(run_query("SELECT x'4142' AS a").csv_out, "A\nb'AB'")

    def test_empty_result(self):
        query_result = run_query("SELECT 1 AS a WHERE 0")
        self.assertEqual(query_result.csv_out, "")
        self.assertEqual(query_result.types_out, "")
        self.assertEqual(query_result.column_count, 0)
        self.assertEqual(query_result.row_count, 0)

        query_result.sort_rows(["A"])  # noop
        self.assertEqual(query_result.csv_out, "")

    def test_counts(self):
        query_result = run_query("SELECT 1 AS a, 2 AS a UNION ALL SELECT 3, 4")
        self.assertEqual(query_result.csv_out, "A,A\n1,2\n3,4")
        self.assertEqual(query_result.column_count, 2)
        self.assertEqual(query_result.row_count, 2)

    def test_sort_mixed_types(self):
        query_result = run_query(
            "SELECT 'b' AS a UNION ALL SELECT NULL UNION ALL SELECT x'41' UNION ALL SELECT 2.5 "
            "UNION ALL SELECT 'B' UNION ALL SELECT 1"
        )
        query_result.sort_rows(["A"])
        self.assertEqual(query_result.csv_out, "A\n1\n2.5\nB\nb\nb'A'\n\"\"")

    def test_sort_null_last_and_stable(self):
        query_result = run_query(
            "SELECT NULL AS a, 1 AS b UNION ALL SELECT 2, 2 UNION ALL SELECT 1, 3 UNION ALL SELECT 2, 4"
        )
        query_result.sort_rows(["A"])
        self.assertEqual(query_result.csv_out, "A,B\n1,3\n2,2\n2,4\n,1")
