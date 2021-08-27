import json
import sys
from abc import ABC
from types import SimpleNamespace, TracebackType


class DodonaCommand(ABC):
    def __init__(self, **kwargs):
        self.start_args = SimpleNamespace(**kwargs)
        self.close_args = SimpleNamespace()

    def name(self) -> str:
        return self.__class__.__name__.lower()

    def start_msg(self) -> dict:
        return {"command": f"start-{self.name()}", **self.start_args.__dict__}

    def close_msg(self) -> dict:
        return {"command": f"close-{self.name()}", **self.close_args.__dict__}

    @staticmethod
    def __print_command(result: dict) -> None:
        json.dump(result, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")  # Next JSON fragment should be on new line

    def __enter__(self) -> SimpleNamespace:
        self.__print_command(self.start_msg())
        return self.close_args

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        self.__print_command(self.close_msg())


class Judgement(DodonaCommand):
    pass


class Tab(DodonaCommand):
    def __init__(self, title: str, **kwargs):
        super().__init__(title=title, **kwargs)


class Context(DodonaCommand):
    pass


class TestCase(DodonaCommand):
    def __init__(self, description: str, **kwargs):
        super().__init__(description=description, **kwargs)


class Test(DodonaCommand):
    def __init__(self, description: str, expected: str, **kwargs):
        super().__init__(description=description, expected=expected, **kwargs)


class Message(DodonaCommand):
    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, **kwargs)

    def start_msg(self) -> dict:
        return {"command": "append-message", **self.start_args.__dict__}

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        pass


class Annotation(DodonaCommand):
    def __init__(self, row: str, text: str, **kwargs):
        super().__init__(row=row, text=text, **kwargs)

    def start_msg(self) -> dict:
        return {"command": "annotate-code", **self.start_args.__dict__}

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        pass
