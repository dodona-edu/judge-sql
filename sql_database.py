"""manage sqlite solution and submission database"""

import os
import sqlite3

from sqlite3 import Cursor
from types import TracebackType
from shutil import copyfile
from dodona_config import DodonaConfig
from sql_query_result import SQLQueryResult


class SQLDatabase:
    """wrapper class for the sqlite3 connections & file management

    This class manages a solution and a submission file that are based on the
    exercise's "starting-point"/ init database. The user queries should be applied on the
    submission file and the solution queries should be applied on the solution file.
    This class also provides functions for comparing the two databases. This class is usefull
    when used with non-select sql queries (eg. CREATE & INSERT).
    """

    def __init__(self, db_name: str, sourcefile: str, workdir: str):
        """construct SQLDatabase

        :param sourcefile: exercise's sqlite start databse file
        """
        self.sourcefile = sourcefile
        self.solutionfile = os.path.join(workdir, f"{db_name}.solution")
        self.submissionfile = os.path.join(workdir, f"{db_name}.submission")

        self.connection = None

    def __enter__(self) -> "SQLDatabase":
        """create solutionfile and submissionfile

        If no solutionfile/ submissionfile has been generated before
        (usally because it is the first testcase), the sourcefile is
        copied to these filelocations.

        :return: current SQLDatabase instance
        """
        if not os.path.isfile(self.solutionfile):
            copyfile(self.sourcefile, self.solutionfile)
        if not os.path.isfile(self.submissionfile):
            copyfile(self.sourcefile, self.submissionfile)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        """commit & close current database connection on exit"""
        self.close()

    def close(self) -> None:
        """commit & close current database connection"""
        if self.connection is not None:
            self.connection.commit()
            self.connection.close()
        self.connection = None

    def solution_cursor(self) -> Cursor:
        """:return: a cursor for the solutionfile database"""
        self.close()
        self.connection = sqlite3.connect(self.solutionfile)
        return self.connection.cursor()

    def submission_cursor(self) -> Cursor:
        """:return: a cursor for the submissionfile database"""
        self.close()
        self.connection = sqlite3.connect(self.submissionfile)
        return self.connection.cursor()

    def joined_cursor(self) -> Cursor:
        """:return: a cursor for the a database in which both the solution and submission are attached"""
        self.close()
        self.connection = sqlite3.connect(":memory:")
        cursor = self.connection.cursor()
        cursor.execute(f'ATTACH "{self.solutionfile}" as solution')
        cursor.execute(f'ATTACH "{self.submissionfile}" as submission')
        return cursor

    def get_table_layout(self, config: DodonaConfig, table: str) -> tuple[SQLQueryResult, SQLQueryResult]:
        """retrieve the table layout for both the solution and submission

        :param config: the dodonda judge config
        :param table: name of table to request layout for
        :return: (solution_layout, submission_layout) containing the pragma table info
        """
        cursor = self.joined_cursor()
        cursor.execute(f"PRAGMA solution.table_info('{table}')")
        solution_layout = SQLQueryResult.from_cursor(config.max_rows, cursor)
        cursor.execute(f"PRAGMA submission.table_info('{table}')")
        submission_layout = SQLQueryResult.from_cursor(config.max_rows, cursor)
        return solution_layout, submission_layout

    def get_table_content(self, config: DodonaConfig, table: str) -> tuple[SQLQueryResult, SQLQueryResult]:
        """retrieve the table content for both the solution and submission

        :param config: the dodonda judge config
        :param table: name of table to request content for
        :return: (solution_content, submission_content) containing the table contents
        """
        cursor = self.joined_cursor()
        cursor.execute(f"SELECT * FROM solution.'{table}'")
        solution_content = SQLQueryResult.from_cursor(config.max_rows, cursor)
        cursor.execute(f"SELECT * FROM submission.'{table}'")
        submission_content = SQLQueryResult.from_cursor(config.max_rows, cursor)
        return solution_content, submission_content

    count_identical_columns_sql = """
    --- ONLY IN SOLUTION ---
    SELECT
        sol.name,
        0, 1, 0 -- any number values that trigger a mismatch will do
    FROM solution.sqlite_master AS sol
    WHERE NOT EXISTS (
        SELECT 1
        FROM submission.sqlite_master AS sub
        WHERE sub.name = sol.name
    )
    UNION ALL
    --- ONLY IN SUBMISSION ---
    SELECT
        sub.name,
        0, 0, 1 -- any number values that trigger a mismatch will do
    FROM submission.sqlite_master AS sub
    WHERE NOT EXISTS (
        SELECT 1
        FROM solution.sqlite_master AS sol
        WHERE sol.name = sub.name
    )
    UNION ALL
    --- DIFFERENT SCHEME ---
    SELECT
        s.name,
        count(1) as identical,
        (SELECT count(1) FROM pragma_table_info(s.name, 'solution')) as solution,
        (SELECT count(1) FROM pragma_table_info(s.name, 'submission')) as submission
    FROM
        solution.sqlite_master as s,
        pragma_table_info(s.name, 'solution') solTable,
        pragma_table_info(s.name, 'submission') subTable
    WHERE
        s.type = 'table' AND
        s.name NOT LIKE 'sqlite_%' AND
        solTable.name=subTable.name AND
        solTable.type=subTable.type AND
        solTable.'notnull'=subTable.'notnull' AND
        (
            solTable.dflt_value=subTable.dflt_value OR
            (
                solTable.dflt_value IS NULL AND
                subTable.dflt_value IS NULL
            )
        ) AND
        solTable.pk=subTable.pk
    GROUP BY s.name;
    """

    count_different_rows_sql = """
    SELECT count(1) FROM (
        SELECT * FROM solution.'{table}' A
        EXCEPT
        SELECT * FROM submission.'{table}' B
    )
    """

    def diff(self) -> tuple[list[str], list[str], list[str], list[str]]:
        """determine the difference between the solution and submission sqlite databases

        First all table names are checked, tables with a name that includes the character '
        are returned in 'incorrect_name'. Then, from the correctly named tables, all tables
        that have a different table layout are filtered, these are returned as 'diff_layout'.
        Finally, the remaining table's content is compared and a list of tables with differing
        contents is returned as 'diff_content'.

        :return: (incorrect_name, diff_layout, diff_content, correct) names of tables that have invalid names,
        are non-identical with regards to layout, are non-identical with regards to content and are identical
        """
        cursor = self.joined_cursor()

        cursor.execute(self.count_identical_columns_sql)

        incorrect_name, diff_layout, check_content, correct = [], [], [], []
        temp = cursor.fetchall()
        for row in temp:
            table, identical, solution, submission = row

            if "'" in table:
                incorrect_name += [table]
            elif solution != submission or solution != identical:
                diff_layout += [table]
            else:
                check_content += [table]

        cursor.execute(
            "UNION ALL\n".join([self.count_different_rows_sql.format(table=table) for table in check_content])
        )

        counts = [count for (count,) in cursor.fetchall()]
        diff_content = []
        for i, table in enumerate(check_content):
            if counts[i] != 0:
                diff_content += [table]
            else:
                correct += [table]

        return incorrect_name, diff_layout, diff_content, correct
