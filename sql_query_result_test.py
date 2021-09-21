# pylint: disable=missing-docstring

import unittest

import pandas as pd

from sql_query_result import SQLQueryResult


class TestSQLQueryResult(unittest.TestCase):
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

        self.assertEqual(
            query_result.csv_out,
            "col1,col3,col2\n" "19,Tom,20\n" "11,nick,21\n" "17,krish,19\n" "18,jack,18",
        )
        self.assertEqual(
            query_result.types_out,
            "col1 [INTEGER]\n" "col3 [TEXT]\n" "col2 [INTEGER]",
        )

        query_result.index_columns(["col3", "col1", "non_existing"])  # should keep all columns & not add non_existing
        query_result.sort_rows(["col3", "col1", "non_existing"])

        self.assertEqual(
            query_result.csv_out,
            "col3,col1,col2\n" "Tom,19,20\n" "jack,18,18\n" "krish,17,19\n" "nick,11,21",
        )
        self.assertEqual(
            query_result.types_out,
            "col3 [TEXT]\n" "col1 [INTEGER]\n" "col2 [INTEGER]",
        )

    def test_init2(self):
        query_result = SQLQueryResult(
            pd.DataFrame(
                [["tom", 2, 10], ["nick", 2, 15], ["juli", 2, 14]],
            ),
            ["Name", "Test", "Name"],
            [str, int, int],
        )

        self.assertEqual(query_result.csv_out, "Name,Test,Name\n" "tom,2,10\n" "nick,2,15\n" "juli,2,14")
        self.assertEqual(query_result.types_out, "Name [TEXT]\n" "Test [INTEGER]\n" "Name [INTEGER]")

        query_result.index_columns(["Name", "Test"])  # should keep both columns & keep ordering (stable)
        query_result.sort_rows(["Name"])

        self.assertEqual(query_result.csv_out, "Name,Test,Name\n" "juli,2,14\n" "nick,2,15\n" "tom,2,10")
        self.assertEqual(query_result.types_out, "Name [TEXT]\n" "Test [INTEGER]\n" "Name [INTEGER]")


if __name__ == "__main__":
    unittest.main()
