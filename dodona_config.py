import json
import os
from types import SimpleNamespace
from typing import TextIO


class DodonaConfig(SimpleNamespace):
    """A class for containing all Dodona Judge configuration

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

    @classmethod
    def from_json(cls, json_file: TextIO) -> "DodonaConfig":
        simple = json.load(json_file, object_hook=lambda d: SimpleNamespace(**d))
        return cls(**simple.__dict__)

    def sanity_check(self) -> None:
        # Make sure that the current working dir is the workdir
        cwd = os.getcwd()
        assert os.path.realpath(cwd) == os.path.realpath(self.workdir)

        # Make sure that this file is located in the judge folder
        script_path = os.path.dirname(os.path.realpath(__file__))
        assert os.path.realpath(script_path) == os.path.realpath(self.judge)
