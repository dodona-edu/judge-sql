"""Test exercise databases that hold TEXT which is not valid UTF-8."""

import json
import os
import runpy
import sqlite3
import unittest
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from .fake_in_out import fake_in_out

ROOT_PATH = Path(__file__).resolve().parent.parent
QUERY = "SELECT id, voornaam FROM ruimtevaarders ORDER BY id;"


def run_judge(tmp: Path, submission: str, solution: str = QUERY) -> tuple[str, str]:
    """Run sql_judge.py on an exercise whose database holds the Latin-1 bytes of 'André' as TEXT.

    Args:
        tmp: scratch directory for the exercise and the judge workdir
        submission: the submitted query
        solution: the solution query

    Returns:
        (stdout, stderr) of the judge run
    """
    resources, workdir = tmp / "evaluation", tmp / "workdir"
    resources.mkdir()
    workdir.mkdir()

    connection = sqlite3.connect(resources / "ruimtevaart.sqlite")
    connection.execute("CREATE TABLE ruimtevaarders (id INTEGER PRIMARY KEY, voornaam TEXT)")
    connection.execute("INSERT INTO ruimtevaarders VALUES (1, CAST(x'416e6472e9' AS TEXT))")
    connection.commit()
    connection.close()

    (resources / "solution.sql").write_text(solution, encoding="utf-8")
    (tmp / "submission.sql").write_text(submission, encoding="utf-8")

    config = {
        "memory_limit": "99999999",
        "time_limit": "99999999",
        "programming_language": "sql",
        "natural_language": "nl",
        "resources": str(resources),
        "source": str(tmp / "submission.sql"),
        "judge": str(ROOT_PATH),
        "workdir": str(workdir),
    }
    old_cwd = Path.cwd()
    os.chdir(workdir)
    try:
        with fake_in_out(StringIO(json.dumps(config))) as (out, err):
            runpy.run_path(str(ROOT_PATH / "sql_judge.py"))
    finally:
        os.chdir(old_cwd)
    return out.getvalue(), err.getvalue()


class TestInvalidUtf8(unittest.TestCase):
    """Judge runs against a database with invalid UTF-8 TEXT."""

    def test_select_correct_submission(self):
        with TemporaryDirectory() as tmp:
            out, err = run_judge(Path(tmp), QUERY)

        self.assertEqual(err, "")
        self.assertIn("Andr\\ufffd", out)
        self.assertIn('"enum": "correct"', out)
        self.assertNotIn('"enum": "wrong"', out)

    def test_select_wrong_submission(self):
        with TemporaryDirectory() as tmp:
            out, err = run_judge(Path(tmp), "SELECT id, voornaam FROM ruimtevaarders WHERE id > 1;")

        self.assertEqual(err, "")
        self.assertIn('"enum": "wrong"', out)

    def test_non_select_correct_submission(self):
        insert = "INSERT INTO ruimtevaarders VALUES (2, 'x');"
        with TemporaryDirectory() as tmp:
            out, err = run_judge(Path(tmp), insert, insert)

        self.assertEqual(err, "")
        self.assertIn("Andr\\ufffd", out)
        self.assertIn('"enum": "correct"', out)
        self.assertNotIn('"enum": "wrong"', out)
        self.assertNotIn("internal error", out)
