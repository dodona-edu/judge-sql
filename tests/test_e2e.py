"""Test E2E."""

import json
import os
import runpy
import shutil
from io import StringIO
from pathlib import Path

import pytest

from .fake_in_out import fake_in_out

ROOT_PATH = Path(__file__).resolve().parent.parent
E2E_REPO_NAME = "test-sql-judge"
EXERCISES_PATH = ROOT_PATH / "tests" / "e2e_repos" / E2E_REPO_NAME
STDOUT_PATH = ROOT_PATH / "tests" / "e2e_stdout" / E2E_REPO_NAME

LEARN_OUTPUT = os.environ.get("LEARN_OUTPUT", "NO") == "YES"


def _discover_cases() -> list:
    """Discover (exercise, submission) pairs from the e2e fixture repo.

    Returns:
        One `pytest.param` per exercise/submission combination, carrying the
        exercise directory and submission file as values and a readable
        `<exercise>-<submission>` id.
    """
    if not EXERCISES_PATH.is_dir():
        return []

    cases = []

    for exercise_path in sorted(EXERCISES_PATH.iterdir()):
        if exercise_path.name.startswith("_") or not exercise_path.is_dir():
            continue

        for submission_path in sorted((exercise_path / "solution").iterdir()):
            if submission_path.suffix != ".sql":
                continue

            case_id = f"{exercise_path.name}-{submission_path.stem}"
            cases.append(pytest.param(exercise_path, submission_path, id=case_id))

    return cases


E2E_CASES = _discover_cases()

if not E2E_CASES:
    raise RuntimeError(
        f"No e2e exercise/submission pairs found in {EXERCISES_PATH}. "
        "Run `git submodule update --init` to fetch the e2e fixture submodule."
    )


@pytest.fixture(scope="session", autouse=True)
def _reset_stdout_goldens() -> None:
    """Reset the golden stdout directory once per session when learning.

    In learning mode (`LEARN_OUTPUT=YES`, see `devel/learn-e2e.sh`) the
    golden `.stdout` files are regenerated from the observed judge output
    instead of being compared against. The directory is wiped and recreated
    exactly once here rather than per test case.

    Learning mode is meant to be run single-process: `devel/learn-e2e.sh`
    does not pass `-n`, since the wipe above would otherwise race across
    xdist workers.
    """
    if LEARN_OUTPUT:
        print("\n------------------------------------------")
        print("WARNING: LEARN_OUTPUT is enabled")
        print("> 'stdout' and 'stderr' files will get updated to match the execution output")
        print("------------------------------------------")

        shutil.rmtree(STDOUT_PATH, ignore_errors=True)

    STDOUT_PATH.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize("exercise_path, submission_path", E2E_CASES)
def test_e2e(exercise_path: Path, submission_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the SQL judge on one exercise/submission pair and check its output.

    Args:
        exercise_path: Directory of the exercise, e.g. `.../create_table`.
        submission_path: Submission file to judge, e.g. `.../wrong_name.sql`.
        tmp_path: Pytest-provided scratch directory, used as the judge workdir.
        monkeypatch: Used to change into `tmp_path` for the duration of the run.
    """
    config_path = exercise_path / "config.json"

    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file).get("evaluation", {})

    config.update(
        {
            "memory_limit": "99999999",
            "time_limit": "99999999",
            "programming_language": "sql",
            "natural_language": "nl",
            "resources": str(exercise_path / "evaluation"),
            "source": str(submission_path),
            "judge": str(ROOT_PATH),
            "workdir": str(tmp_path),
        }
    )

    monkeypatch.chdir(tmp_path)
    with fake_in_out(StringIO(json.dumps(config))) as (out, err):
        runpy.run_path(str(ROOT_PATH / "sql_judge.py"))

    assert err.getvalue().strip() == ""

    observed = out.getvalue().strip().replace(str(exercise_path), "<exercise_path>")
    stdout_path = STDOUT_PATH / f"{exercise_path.name}_{submission_path.stem}.stdout"

    if LEARN_OUTPUT:
        stdout_path.write_text(observed, encoding="utf-8")
        return

    if not stdout_path.exists():
        raise FileNotFoundError(f"Missing stdout file: {stdout_path}")

    assert observed == stdout_path.read_text(encoding="utf-8")
