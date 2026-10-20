"""Builders for the exceptions that end (part of) a judgement with an error."""

from .dodona_command import DodonaException, ErrorType, MessageFormat, MessagePermission
lazy from .dodona_config import DodonaConfig


def internal_error(
    config: DodonaConfig, description: str, *, message_format: MessageFormat = MessageFormat.TEXT
) -> DodonaException:
    """Create an internal error that only educators can read.

    Args:
        config: parsed config received from Dodona
        description: message for educators
        message_format: format of the message

    Returns:
        exception that ends the judgement with an internal error
    """
    return DodonaException(
        config.translator.error_status(ErrorType.INTERNAL_ERROR),
        permission=MessagePermission.EDUCATOR,
        description=description,
        format=message_format,
    )


def student_error(
    config: DodonaConfig,
    error_type: ErrorType,
    description: str,
    *,
    message_format: MessageFormat = MessageFormat.CALLOUT_DANGER,
    recover_at: type | None = None,
) -> DodonaException:
    """Create an error with a message the student reads.

    Args:
        config: parsed config received from Dodona
        error_type: status of the error
        description: message for the student
        message_format: format of the message
        recover_at: the type of the 'with' block to recover at, or None to end the judgement

    Returns:
        exception with the given status
    """
    return DodonaException(
        config.translator.error_status(error_type),
        recover_at=recover_at,
        permission=MessagePermission.STUDENT,
        description=description,
        format=message_format,
    )
