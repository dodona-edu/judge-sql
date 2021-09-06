import unittest

import pandas as pd

from sql_query_result import SQLQueryResult


class TestSQLQueryResult(unittest.TestCase):
    def test_init1(self):
        qr = SQLQueryResult(
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
            qr.csv_out,
            "col1,col3,col2\n" "19,Tom,20\n" "11,nick,21\n" "17,krish,19\n" "18,jack,18",
        )
        self.assertEqual(
            qr.types_out,
            "col1 [INTEGER]\n" "col3 [TEXT]\n" "col2 [INTEGER]",
        )

        qr.index_columns(["col3", "col1", "non_existing"])  # should keep all columns & not add non_existing
        qr.sort_rows(["col3", "col1", "non_existing"])

        self.assertEqual(
            qr.csv_out,
            "col3,col1,col2\n" "Tom,19,20\n" "jack,18,18\n" "krish,17,19\n" "nick,11,21",
        )
        self.assertEqual(
            qr.types_out,
            "col3 [TEXT]\n" "col1 [INTEGER]\n" "col2 [INTEGER]",
        )

    def test_init2(self):
        qr = SQLQueryResult(
            pd.DataFrame(
                [["tom", 10], ["nick", 15], ["juli", 14]],
            ),
            ["Name", "Name"],
            [str, int],
        )

        self.assertEqual(qr.csv_out, "Name,Name\n" "tom,10\n" "nick,15\n" "juli,14")
        self.assertEqual(qr.types_out, "Name [TEXT]\n" "Name [INTEGER]")

        qr.index_columns(["Name"])  # should keep both columns & keep ordering (stable)
        qr.sort_rows(["Name"])

        self.assertEqual(qr.csv_out, "Name,Name\n" "juli,14\n" "nick,15\n" "tom,10")
        self.assertEqual(qr.types_out, "Name [TEXT]\n" "Name [INTEGER]")


if __name__ == "__main__":
    unittest.main()
