"""Test SQLDatabase."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from judge.sql_database import SQLDatabase


class TestSQLDatabase(unittest.TestCase):
    """SQLDatabase TestCase."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workdir = Path(self.tmp.name)
        source = self.workdir / "source.sqlite"
        sqlite3.connect(source).close()
        self.database = self.enterContext(SQLDatabase(str(source), str(self.workdir), "test"))

    def run_statement(self, cursor: sqlite3.Cursor, statement: str, parameters: tuple = ()):
        cursor.execute(statement, parameters)
        cursor.connection.commit()

    # SQLite upper-cases standard type names itself, so these tests use varchar, which keeps its declared case.
    def test_diff_ignores_column_type_case(self):
        self.run_statement(self.database.solution_cursor(), "CREATE TABLE t (id INTEGER, name VARCHAR(20))")
        self.run_statement(self.database.submission_cursor(), "CREATE TABLE t (id integer, name varchar(20))")

        incorrect_name, diff_layout, diff_content, correct = self.database.diff()

        self.assertEqual(incorrect_name, [])
        self.assertEqual(diff_layout, [])
        self.assertEqual(diff_content, [])
        self.assertEqual(correct, ["t"])

    def test_diff_detects_different_column_type(self):
        self.run_statement(self.database.solution_cursor(), "CREATE TABLE t (id VARCHAR(20))")
        self.run_statement(self.database.submission_cursor(), "CREATE TABLE t (id VARCHAR(30))")

        self.assertEqual(self.database.diff()[1], ["t"])

    def test_diff_compares_tables_starting_with_sqlite(self):
        for make_cursor, value in ((self.database.solution_cursor, "1"), (self.database.submission_cursor, "2")):
            cursor = make_cursor()
            self.run_statement(cursor, "CREATE TABLE sqlitedata (id INTEGER)")
            self.run_statement(cursor, "INSERT INTO sqlitedata VALUES (?)", (value,))
            self.run_statement(cursor, "CREATE TABLE same (id INTEGER)")
            self.run_statement(cursor, "INSERT INTO same VALUES (1)")

        incorrect_name, diff_layout, diff_content, correct = self.database.diff()

        self.assertEqual(incorrect_name, [])
        self.assertEqual(diff_layout, [])
        self.assertEqual(diff_content, ["sqlitedata"])
        self.assertEqual(correct, ["same"])

    def test_table_layout_ignores_column_type_case(self):
        self.run_statement(self.database.solution_cursor(), "CREATE TABLE t (id VARCHAR(20))")
        self.run_statement(self.database.submission_cursor(), "CREATE TABLE t (id varchar(20))")

        solution_layout, submission_layout = self.database.get_table_layout(100, "t")

        self.assertMultiLineEqual(solution_layout.csv_out, submission_layout.csv_out)
        self.assertIn("VARCHAR(20)", submission_layout.csv_out)
