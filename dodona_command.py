import json
import sys
from abc import ABC
from enum import Enum
from types import SimpleNamespace, TracebackType
from typing import Union


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


class MessagePermission(str, Enum):
    STUDENT = "student"
    STAFF = "staff"
    ZEUS = "zeus"

    def __str__(self):
        return str(self)


class MessageFormat(str, Enum):
    PLAIN = "plain"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    CALLOUT = "callout"
    CALLOUT_INFO = "callout-info"
    CALLOUT_WARNING = "callout-warning"
    CALLOUT_DANGER = "callout-danger"
    CODE = "code"
    SQL = "sql"

    def __str__(self):
        return str(self)


class AnnotationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self):
        return str(self)


class DodonaException(Exception):
    def __init__(
        self,
        status: dict[str, str],
        *args,
        **kwargs,
    ):
        self.status = status
        self.message = Message(*args, **kwargs) if len(args) > 0 or len(kwargs) > 0 else None


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
    def __print_command(result: Union[None, dict]) -> None:
        if result is None:
            return
        json.dump(result, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")  # Next JSON fragment should be on new line

    def __enter__(self) -> SimpleNamespace:
        self.__print_command(self.start_msg())
        return self.close_args

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        False

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> bool:
        if isinstance(exc_val, DodonaException):
            handled = self.handle_dodona_exception(exc_val)
        else:
            handled = False

        self.__print_command(self.close_msg())
        return handled


class DodonaCommandWithAccepted(DodonaCommand):
    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        accepted = exception.status["enum"] == ErrorType.CORRECT or exception.status["enum"] == ErrorType.CORRECT_ANSWER
        self.close_args.accepted = accepted

        # Add an error message
        if exception.message is not None:
            with exception.message:
                pass

            exception.message = None

        return super().handle_dodona_exception(exception)


class DodonaCommandWithStatus(DodonaCommandWithAccepted):
    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        self.close_args.status = exception.status

        return super().handle_dodona_exception(exception)


class Judgement(DodonaCommandWithStatus):
    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        super().handle_dodona_exception(exception)
        return True


class Tab(DodonaCommand):
    def __init__(self, title: str, **kwargs):
        super().__init__(title=title, **kwargs)


class Context(DodonaCommandWithAccepted):
    pass


class TestCase(DodonaCommandWithAccepted):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            super().__init__(description=args[0])
        else:
            super().__init__(description=kwargs)


class Test(DodonaCommandWithStatus):
    def __init__(self, description: str, expected: str, **kwargs):
        super().__init__(description=description, expected=expected, **kwargs)


class Message(DodonaCommand):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            super().__init__(message=args[0])
        else:
            super().__init__(message=kwargs)

    def start_msg(self) -> dict:
        return {"command": "append-message", **self.start_args.__dict__}

    def close_msg(self) -> None:
        pass


class Annotation(DodonaCommand):
    def __init__(self, row: int, text: str, **kwargs):
        super().__init__(row=row, text=text, **kwargs)

    def start_msg(self) -> dict:
        return {"command": "annotate-code", **self.start_args.__dict__}

    def close_msg(self) -> None:
        pass
