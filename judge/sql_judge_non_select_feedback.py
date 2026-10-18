"""sql feedback for non-select queries."""

from contextlib import contextmanager
lazy from collections.abc import Iterator
lazy from types import SimpleNamespace

from .dodona_command import (
    DodonaException,
    ErrorType,
    MessageFormat,
    MessagePermission,
    Test,
)
from .sql_database import SQLDatabase
from .translator import Translator
lazy from .dodona_config import DodonaConfig
lazy from .sql_query import SQLQuery
lazy from .sql_query_result import SQLQueryResult


@contextmanager
def _retrieving(config: DodonaConfig, what: str) -> Iterator[None]:
    """Turn an error while retrieving table data into an internal error.

    Args:
        config: parsed config received from Dodona
        what: the data being retrieved, as named in the error message

    Raises:
        DodonaException: the enclosed block raised an error
    """
    try:
        yield
    except Exception as err:
        raise DodonaException(
            config.translator.error_status(ErrorType.INTERNAL_ERROR),
            permission=MessagePermission.EDUCATOR,
            description=f"Could not retrieve solution {what} ({type(err).__name__}):\n    {err}",
            format=MessageFormat.CODE,
        ) from err


def _table_test(
    config: DodonaConfig, description: str, solution: SQLQueryResult, submission: SQLQueryResult, status: ErrorType
) -> None:
    """Show the solution and submission versions of a table in a test.

    Args:
        config: parsed config received from Dodona
        description: the test's description
        solution: the table in the solution database
        submission: the table in the submission database
        status: the test's status
    """
    with Test(
        {
            "description": description,
            "format": MessageFormat.MARKDOWN,
        },
        solution.csv_out,
        format="csv",
    ) as test:
        test.generated = submission.csv_out
        test.status = config.translator.error_status(status)


def non_select_feedback(
    config: DodonaConfig, testcase: SimpleNamespace, db_name: str, db_file: str, solution_query: SQLQuery
) -> None:
    """Run tests based on database status after running a non-select query.

    Args:
        config: parsed config received from Dodona
        testcase: testcase object used to return values to Dodona
        db_name: the name of the database
        db_file: the location of the database file
        solution_query: the parsed solution query

    Raises:
        DodonaException: custom exception that is automatically handled by the 'with' blocks
    """
    with SQLDatabase(db_file, config.workdir, db_name) as database:
        incorrect_name, diff_layout, diff_content, correct = database.diff()

        if len(incorrect_name) > 0:
            raise DodonaException(
                config.translator.error_status(ErrorType.COMPILATION_ERROR),
                permission=MessagePermission.STUDENT,
                description=config.translator.translate(
                    Translator.Text.INVALID_SINGLE_QUOTE_TABLE_NAME,
                    table=incorrect_name[0],
                ),
                format=MessageFormat.CALLOUT_DANGER,
            )

        for table in diff_layout:
            with _retrieving(config, "layout"):
                solution_layout, submission_layout = database.get_table_layout(config, table)

            description = config.translator.translate(Translator.Text.COMPARING_TABLE_LAYOUT, table=table)
            _table_test(config, description, solution_layout, submission_layout, ErrorType.WRONG)
            testcase.accepted = False  # Signal that following on-success tests should not run

        for table in diff_content:
            with _retrieving(config, "content"):
                solution_content, submission_content = database.get_table_content(config, table)

            description = config.translator.translate(Translator.Text.COMPARING_TABLE_CONTENT, table=table)
            _table_test(config, description, solution_content, submission_content, ErrorType.WRONG)
            testcase.accepted = False  # Signal that following on-success tests should not run

        if diff_layout or diff_content:
            return

        affected_table = solution_query.first_match_array(correct)

        if affected_table is None:
            return

        with _retrieving(config, "layout & content"):
            solution_layout, submission_layout = database.get_table_layout(config, affected_table)
            solution_content, submission_content = database.get_table_content(config, affected_table)

        description = config.translator.translate(Translator.Text.COMPARING_TABLE_LAYOUT, table=affected_table)
        _table_test(config, description, solution_layout, submission_layout, ErrorType.CORRECT)
        description = config.translator.translate(Translator.Text.COMPARING_TABLE_CONTENT, table=affected_table)
        _table_test(config, description, solution_content, submission_content, ErrorType.CORRECT)
