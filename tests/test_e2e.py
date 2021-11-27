import json
import os
import runpy
import tempfile
import unittest
import shutil
from io import StringIO

from .fake_in_out import fake_in_out


class TestEndToEnd(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        self.maxDiff = None
        self.root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    def run_sql_judge(self, exercise_path: str, stdout_path: str, learning_mode: bool = False):
        evaluation_path = os.path.join(exercise_path, "evaluation")
        config_path = os.path.join(exercise_path, "config.json")

        config = {}

        with open(config_path, "r") as config_file:
            config.update(json.load(config_file).get("evaluation", {}))

        submission_path = os.path.join(evaluation_path, str(config.get("solution_sql", "./solution.sql")))

        with tempfile.TemporaryDirectory() as cwd_path:
            config.update(
                {
                    "memory_limit": "99999999",
                    "time_limit": "99999999",
                    "programming_language": "sql",
                    "natural_language": "nl",
                    "resources": evaluation_path,
                    "source": submission_path,
                    "judge": self.root_path,
                    "workdir": cwd_path,
                }
            )

            os.chdir(cwd_path)
            with fake_in_out(StringIO(json.dumps(config))) as (out, err):
                runpy.run_path(os.path.join(self.root_path, "sql_judge.py"))

        self.assertEqual(err.getvalue().strip(), "")

        if learning_mode:
            with open(stdout_path, "w") as stdout:
                stdout.write(out.getvalue().strip().replace(exercise_path, "<exercise_path>"))
        else:
            if not os.path.exists(stdout_path):
                raise FileNotFoundError(f"Missing stdout file: {stdout_path}")

            with open(stdout_path, "r") as stdout:
                self.assertEqual(
                    out.getvalue().strip().replace(exercise_path, "<exercise_path>"),
                    stdout.read(),
                )

    def run_all_repo_tests(self, repo_path: str):
        test_exercises_path = os.path.join(self.root_path, "tests", "e2e_repos", repo_path)
        test_stdout_path = os.path.join(self.root_path, "tests", "e2e_stdout", repo_path)

        LEARN_OUTPUT = os.environ.get("LEARN_OUTPUT", "NO") == "YES"
        if LEARN_OUTPUT:
            print("\n------------------------------------------")
            print("WARNING: LEARN_OUTPUT is enabled")
            print("> 'stdout' and 'stderr' files will get updated to match the execution output")
            print("------------------------------------------")

            shutil.rmtree(test_stdout_path)

        os.makedirs(test_stdout_path, exist_ok=True)

        for folder in os.listdir(test_exercises_path):
            exercise_path = os.path.join(test_exercises_path, folder)
            stdout_path = os.path.join(test_stdout_path, f"{folder}.stdout")

            if not os.path.isdir(exercise_path):
                continue

            with self.subTest(folder):
                self.run_sql_judge(
                    exercise_path,
                    stdout_path,
                    LEARN_OUTPUT,
                )

    def test_e2e(self):
        self.run_all_repo_tests(os.path.join("test-sql-judge"))
