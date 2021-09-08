"""report judge's results to Dodona using Dodona commands (partial JSON output)"""

import json
import sys
from abc import ABC
from enum import Enum
from types import SimpleNamespace, TracebackType
from typing import Union


class ErrorType(str, Enum):
    """Dodona error type"""

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
    """Dodona permission for a message"""

    STUDENT = "student"
    STAFF = "staff"
    ZEUS = "zeus"

    def __str__(self):
        return str(self)


class MessageFormat(str, Enum):
    """Dodona format for a message"""

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
    """Dodona serverity of an annotation"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def __str__(self):
        return str(self)


class DodonaException(Exception):
    """exception that will automatically create a message and set the correct status when thrown

    When thrown inside a Dodona 'with' block, an error message will be created on the current
    Dodona object (eg. Test, Context ...). Blocks that extend the DodonaCommandWithAccepted class
    will have their accepted field set to True (if CORRECT or CORRECT_ANSWER) and to False otherwise.
    If the block also extends DodonaCommandWithStatus, its status is updated with this exception's
    status. The outer Judgement block will silently catch the exception and the process will exit
    with a 0 exitcode.
    """

    def __init__(
        self,
        status: dict[str, str],
        *args,
        **kwargs,
    ):
        super().__init__()
        self.status = status
        self.message = Message(*args, **kwargs) if len(args) > 0 or len(kwargs) > 0 else None


class DodonaCommand(ABC):
    """abstract class, parent of all Dodona commands

    This class provides all shared functionality for the Dodona commands. These commands
    should be used in a Python 'with' block.

    Example:
    >>> with Judgement() as judgement:
    ...     with Tab():
    ...         pass

    A JSON message will be printed to stdout when entering the 'with' block. The contents of
    the message are the parameters passed to the constructor to the class.
    When exiting the 'with' block, a close JSON message will be printed to stdout. The contents
    of that message are set dynamically on the object that was returned when entering.

    Example:
    >>> with Tab(
    ...     title="example tab",
    ... ) as tab:
    ...     tab.badgeCount = 43
    When entering the 'with' block, prints:
    {
        "command": "start-tab",
        "title": "example tab"
    }

    When exiting the 'with' block, prints:
    {
        "command": "close-tab",
        "badgeCount": 43
    }
    """

    def __init__(self, **kwargs):
        self.start_args = SimpleNamespace(**kwargs)
        self.close_args = SimpleNamespace()

    def name(self) -> str:
        """name used in start and close messages, defaults to the lowercase version of the classname"""
        return self.__class__.__name__.lower()

    def start_msg(self) -> dict:
        """start message that is printed as JSON to stdout when entering the 'with' block"""
        return {"command": f"start-{self.name()}", **self.start_args.__dict__}

    def close_msg(self) -> dict:
        """close message that is printed as JSON to stdout when exiting the 'with' block"""
        return {"command": f"close-{self.name()}", **self.close_args.__dict__}

    @staticmethod
    def __print_command(result: Union[None, dict]) -> None:
        """print the provided to stdout as JSON

        :param result: dict that will be JSON encoded and printed to stdout
        """
        if result is None:
            return
        json.dump(result, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")  # Next JSON fragment should be on new line

    def __enter__(self) -> SimpleNamespace:
        """print the start message when entering the 'with' block"""
        self.__print_command(self.start_msg())
        return self.close_args

    # pylint: disable=no-self-use
    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """handle a DodonaException

        This function returns a boolean that is True if the exeption should
        not get propagated to parent codeblocks. This should only be True
        for the most outer block (Judgement), so that all levels of Dodona
        objects can update their status and success parameters.

        This function can be overwritten by child classes, these overwrites
        should still call this function.

        This function prints a Dodona message and removes the message from
        the exception, so it is not also printed by the parent 'with' blocks.

        :param exception: exception thrown in the enclosed 'with' block
        :return: if True, the exception is not propagated
        """

        # Add an error message
        if exception.message is not None:
            with exception.message:
                pass

            exception.message = None

        return False

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> bool:
        """print the close message when exiting the 'with' block & handle enclosed exceptions

        If a DodonaException was thrown in the enclosed 'with' block, the 'handle_dodona_exception'
        function is called. This function can be overwritten by child classes. If 'handle_dodona_exception'
        returns True, this function also returns True and the error is not propagated.

        :return: if True, the exception is not propagated
        """
        if isinstance(exc_val, DodonaException):
            handled = self.handle_dodona_exception(exc_val)
        else:
            handled = False

        self.__print_command(self.close_msg())
        return handled


class DodonaCommandWithAccepted(DodonaCommand):
    """abstract class, parent of all Dodona commands that have an accepted field"""

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """update the accepted parameter based on the exception status"""
        accepted = exception.status["enum"] == ErrorType.CORRECT or exception.status["enum"] == ErrorType.CORRECT_ANSWER
        self.close_args.accepted = accepted

        return super().handle_dodona_exception(exception)


class DodonaCommandWithStatus(DodonaCommandWithAccepted):
    """abstract class, parent of all Dodona commands that have a status field"""

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """update the status of the object"""
        self.close_args.status = exception.status

        return super().handle_dodona_exception(exception)


class Judgement(DodonaCommandWithStatus):
    """Dodona Judgement"""

    def handle_dodona_exception(self, exception: DodonaException) -> bool:
        """return True to prevent the exception from crashing Python and causing a non-zero exit code"""
        super().handle_dodona_exception(exception)
        return True


class Tab(DodonaCommand):
    """Dodona Tab"""

    def __init__(self, title: str, **kwargs):
        super().__init__(title=title, **kwargs)


class Context(DodonaCommandWithAccepted):
    """Dodona Context"""


class TestCase(DodonaCommandWithAccepted):
    """Dodona TestCase"""

    def __init__(self, *args, **kwargs):
        """create TestCase

        If a single positional argument is passed, this is assumed to be the message.
        Example:
        >>> with TestCase("This is the message"):
        ...     pass
        >>> with TestCase({
        ...     "format": MessageFormat.SQL,
        ...     "description": "This is the message"
        ... }):
        ...     pass
        If keyword arguments are passed, these are assumed to be the message's content.
        Example:
        >>> with TestCase(
        ...     format=MessageFormat.SQL,
        ...     description="This is the message"
        ... ):
        ...     pass
        """
        if len(args) == 1:
            super().__init__(description=args[0])
        else:
            super().__init__(description=kwargs)


class Test(DodonaCommandWithStatus):
    """Dodona Test"""

    def __init__(self, description: str, expected: str, **kwargs):
        super().__init__(description=description, expected=expected, **kwargs)


class Message(DodonaCommand):
    """Dodona Message"""

    def __init__(self, *args, **kwargs):
        """create Message

        If a single positional argument is passed, this is assumed to be the message.
        Example:
        >>> with Message("This is the message"):
        ...     pass
        >>> with Message({
        ...     "format": MessageFormat.SQL,
        ...     "description": "This is the message"
        ... }):
        ...     pass
        If keyword arguments are passed, these are assumed to be the message's content.
        Example:
        >>> with Message(
        ...     format=MessageFormat.SQL,
        ...     description="This is the message"
        ... ):
        ...     pass
        """
        if len(args) == 1:
            super().__init__(message=args[0])
        else:
            super().__init__(message=kwargs)

    def start_msg(self) -> dict:
        """print the "append-message" command and parameters when entering the 'with' block"""
        return {"command": "append-message", **self.start_args.__dict__}

    def close_msg(self) -> None:
        """don't print anything when exiting the 'with' block"""


class Annotation(DodonaCommand):
    """Dodona Annotation"""

    def __init__(self, row: int, text: str, **kwargs):
        super().__init__(row=row, text=text, **kwargs)

    def start_msg(self) -> dict:
        """print the "annotate-code" command and parameters when entering the 'with' block"""
        return {"command": "annotate-code", **self.start_args.__dict__}

    def close_msg(self) -> None:
        """don't print anything when exiting the 'with' block"""
