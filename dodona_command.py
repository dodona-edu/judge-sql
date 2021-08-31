import json
import sys
from abc import ABC
from types import SimpleNamespace, TracebackType
from typing import Union
from enum import Enum


class Permission(str, Enum):
    STUDENT = "student"
    STAFF = "staff"
    ZEUS = "zeus"

    def __str__(self):
        return str(self)


class ErrorType(str, Enum):
    INTERNAL_ERROR = "internal error"
    COMPILATION_ERROR = "compilation error"
    MEMORY_LIMIT_EXCEEDED = "memory limit exceeded"
    TIME_LIMIT_EXCEEDED = "time limit exceeded"
    OUTPUT_LIMIT_EXCEEDED = "output limit exceeded"
    RUNTIME_ERROR = "runtime error"
    WRONG = "wrong"
    WRONG_ANSWER = "wrong answer"
    CORRECT = "correct"
    CORRECT_ANSWER = "correct answer"

    def __str__(self):
        return str(self)


class Format(str, Enum):
    PLAIN = "plain"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    CALLOUT = "callout"
    CODE = "code"
    SQL = "sql"

    def __str__(self):
        return str(self)


class DodonaException(Exception):
    def __init__(
        self,
        error_type: ErrorType,
        message_permission: Permission,
        message_description: str,
        message_format: Union[None, Format] = None,
    ):
        self.type = error_type
        self.permission = message_permission
        self.description = message_description
        self.format = message_format if message_format is not None else Format.PLAIN


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

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        return False

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> bool:
        if exc_type == DodonaException:
            assert isinstance(exc_val, DodonaException)
            handled = self.handle_dodona_exception(exc_val)
        else:
            handled = False

        self.__print_command(self.close_msg())

        return handled


class Judgement(DodonaCommand):
    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        self.close_args.accepted = False
        self.close_args.status = {"enum": exception.type}
        with Message(
            {
                "permission": exception.permission,
                "format": exception.format,
                "description": exception.description,
            }
        ):
            pass

        return True


class Tab(DodonaCommand):
    def __init__(self, title: str, **kwargs):
        super().__init__(title=title, **kwargs)


class Context(DodonaCommand):
    pass


class TestCase(DodonaCommand):
    def __init__(self, description: Union[str, dict], **kwargs):
        super().__init__(description=description, **kwargs)


class Test(DodonaCommand):
    def __init__(self, description: str, expected: str, **kwargs):
        super().__init__(description=description, expected=expected, **kwargs)


class Message(DodonaCommand):
    def __init__(self, message: Union[str, dict], **kwargs):
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
    def __init__(self, row: int, text: str, **kwargs):
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
