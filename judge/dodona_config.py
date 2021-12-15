"""Dodona Judge configuration."""

import json
import os
from types import SimpleNamespace
from typing import Any, Union


class DodonaConfig(SimpleNamespace):  # noqa: R0902
    """a class for containing all Dodona Judge configuration.

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
    """

    def __init__(self, **kwargs: Any) -> None:
        """Store all parameters & set correct type for 'known' Dodona judge configuration fields.

        Args:
            kwargs: the named parameters in the form of a dict
        """
        super().__init__(**kwargs)
        self.memory_limit: int = int(self.memory_limit)
        self.time_limit: int = int(self.time_limit)
        self.programming_language: str = str(self.programming_language)
        self.natural_language: str = str(self.natural_language)
        self.resources: str = str(self.resources)
        self.source: str = str(self.source)
        self.judge: str = str(self.judge)
        self.workdir: str = str(self.workdir)

    def __eq__(self, other):
        """Check equality.

        Args:
            other: other object to compare self against
        """
        if isinstance(other, str):
            return super().__eq__(DodonaConfig.from_json(other))

        if isinstance(other, dict):
            return super().__eq__(DodonaConfig(**other))

        return super().__eq__(other)

    @classmethod
    def from_json(cls: type["DodonaConfig"], json_str: Union[str, bytes]) -> "DodonaConfig":
        """Decode json string into a DodonaConfig object.

        Args:
            json_str: input json-encoded string

        Returns:
            decoded Dodona judge config
        """
        simple = json.loads(json_str, object_hook=lambda d: SimpleNamespace(**d))
        return cls(**simple.__dict__)

    def sanity_check(self) -> None:
        """Perform sanity checks.

        This function checks if the Python file is executed correctly.
        The current working dir should be the same directory that is
        passed as the 'workdir' property in the Dodona config. Also,
        this Python file (and all other Python judge files) should be
        located in the 'judge' dir.
        """
        # Make sure that the current working dir is the workdir
        cwd = os.getcwd()
        assert os.path.realpath(cwd) == os.path.realpath(self.workdir)

        # Make sure that this file is located in a subfolder of the judge folder
        script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        assert os.path.realpath(script_path) == os.path.realpath(self.judge)
