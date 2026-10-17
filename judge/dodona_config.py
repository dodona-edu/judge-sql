"""Dodona Judge configuration."""

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import SimpleNamespace
from typing import Self

from .translator import Translator

UNSET = sentinel("UNSET")


@dataclass
class DodonaConfig:
    """a class for containing all Dodona Judge configuration.

    Teacher evaluation options (see the README) follow the Dodona-provided fields.

    Attributes:
        memory_limit:           An integer, the memory limit in bytes. The docker container
                                will be killed when it's internal processes exceed this limit. The judge
                                can use this value to cut of the tests, so he might be able to give more
                                feedback to the student than just the default "Memory limit exceeded."
        time_limit:             An integer, the time limit in seconds. Just like the memory
                                limit, the docker will be killed if the judging takes longer. Can be used
                                to for instance specify the specific test case the limit would be exceeded,
                                instead of just "Time limit exceeded."
        programming_language:   The full name (e.g. "python", "haskell") of the
                                programming language the student submitted his code for.
        natural_language:       The natural language (e.g. "nl", "en") in which the
                                student submitted his code.
        resources:              Full path to a directory containing the resources for the evaluation.
                                This is the "evaluation" directory of an exercise.
        source:                 Full path to a file containing the code the user submitted.
        judge:                  Full path to a directory containing a copy of the judge repository.
        workdir:                Full path to the directory in which all user code should be executed.
        translator:             Translator for `natural_language`.
    """

    memory_limit: int
    time_limit: int
    programming_language: str
    natural_language: str
    resources: str
    source: str
    judge: str
    workdir: str

    max_rows: int = 100
    semicolon_warning: bool = True
    order_unordered_rows: bool = False
    strict_identical_order_by: bool = True
    allow_different_column_order: bool = True
    pragma_startup_queries: str = ""
    pre_execution_forbidden_symbolregex: list[str] = field(
        default_factory=lambda: [".*sqlite_(temp_)?(master|schema).*", "pragma"]
    )
    pre_execution_mandatory_symbolregex: list[str] = field(default_factory=list)
    pre_execution_forbidden_fullregex: list[str] = field(default_factory=list)
    pre_execution_mandatory_fullregex: list[str] = field(default_factory=list)
    post_execution_forbidden_symbolregex: list[str] = field(default_factory=list)
    post_execution_mandatory_symbolregex: list[str] = field(default_factory=list)
    post_execution_forbidden_fullregex: list[str] = field(default_factory=list)
    post_execution_mandatory_fullregex: list[str] = field(default_factory=list)
    database_files: list[str] | UNSET = UNSET
    database_dir: str = "."
    solution_sql: str = "./solution.sql"

    translator: Translator = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Set the correct type for the Dodona-provided fields."""
        self.memory_limit = int(self.memory_limit)
        self.time_limit = int(self.time_limit)
        self.programming_language = str(self.programming_language)
        self.natural_language = str(self.natural_language)
        self.resources = str(self.resources)
        self.source = str(self.source)
        self.judge = str(self.judge)
        self.workdir = str(self.workdir)
        self.translator = Translator.from_str(self.natural_language)

    @classmethod
    def from_json(cls, json_str: str | bytes) -> Self:
        """Decode json string into a DodonaConfig object.

        Args:
            json_str: input json-encoded string

        Returns:
            decoded Dodona judge config
        """
        # Nested objects stay SimpleNamespace: str(), list() and bool() of a dict give different results.
        decoded = json.loads(json_str, object_hook=lambda d: SimpleNamespace(**d))
        known = {f.name for f in fields(cls) if f.init}
        # Dodona and teachers send keys this judge doesn't use: ignore them.
        return cls(**{key: value for key, value in vars(decoded).items() if key in known})

    def coerce_evaluation_options(self) -> None:
        """Set the correct type for the teacher's evaluation options.

        Not part of `__post_init__`: the judge calls this inside its Judgement, so a value that
        can't be coerced still ends the judgement on stdout.
        """
        self.max_rows = int(self.max_rows)
        self.semicolon_warning = bool(self.semicolon_warning)
        self.order_unordered_rows = bool(self.order_unordered_rows)
        self.strict_identical_order_by = bool(self.strict_identical_order_by)
        self.allow_different_column_order = bool(self.allow_different_column_order)
        self.pragma_startup_queries = str(self.pragma_startup_queries)
        self.pre_execution_forbidden_symbolregex = list(self.pre_execution_forbidden_symbolregex)
        self.pre_execution_mandatory_symbolregex = list(self.pre_execution_mandatory_symbolregex)
        self.pre_execution_forbidden_fullregex = list(self.pre_execution_forbidden_fullregex)
        self.pre_execution_mandatory_fullregex = list(self.pre_execution_mandatory_fullregex)
        self.post_execution_forbidden_symbolregex = list(self.post_execution_forbidden_symbolregex)
        self.post_execution_mandatory_symbolregex = list(self.post_execution_mandatory_symbolregex)
        self.post_execution_forbidden_fullregex = list(self.post_execution_forbidden_fullregex)
        self.post_execution_mandatory_fullregex = list(self.post_execution_mandatory_fullregex)
        self.database_dir = str(self.database_dir)
        self.solution_sql = str(self.solution_sql)

    def sanity_check(self) -> None:
        """Perform sanity checks.

        This function checks if the Python file is executed correctly.
        The current working dir should be the same directory that is
        passed as the 'workdir' property in the Dodona config. Also,
        this Python file (and all other Python judge files) should be
        located in the 'judge' dir.
        """
        # Make sure that the current working dir is the workdir
        assert Path.cwd().resolve() == Path(self.workdir).resolve()

        # Make sure that this file is located in a subfolder of the judge folder
        script_path = Path(__file__).resolve().parent.parent
        assert script_path == Path(self.judge).resolve()
