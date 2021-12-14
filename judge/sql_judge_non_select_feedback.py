"""sql feedback for non-select queries."""

from types import SimpleNamespace

from .dodona_command import (
    DodonaException,
    ErrorType,
    MessageFormat,
    MessagePermission,
    Test,
)
from .dodona_config import DodonaConfig
from .sql_database import SQLDatabase
from .sql_query import SQLQuery
from .translator import Translator


def non_select_feedback(  # noqa: C901
    config: DodonaConfig, testcase: SimpleNamespace, db_name: str, db_file: str, solution_query: SQLQuery
) -> None:
    """Run tests based on execution results of a select query.

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
            try:
                solution_layout, submission_layout = database.get_table_layout(config, table)
            except Exception as err:
                raise DodonaException(
                    config.translator.error_status(ErrorType.INTERNAL_ERROR),
                    permission=MessagePermission.STAFF,
                    description=f"Could not retrieve solution layout ({type(err).__name__}):\n    {err}",
                    format=MessageFormat.CODE,
                ) from err

            with Test(
                {
                    "description": config.translator.translate(Translator.Text.COMPARING_TABLE_LAYOUT, table=table),
                    "format": MessageFormat.MARKDOWN,
                },
                solution_layout.csv_out,
                format="csv",
            ) as test:
                test.generated = submission_layout.csv_out
                test.status = config.translator.error_status(ErrorType.WRONG)
                testcase.accepted = False  # Signal that following on-success tests should not run

        for table in diff_content:
            try:
                solution_content, submission_content = database.get_table_content(config, table)
            except Exception as err:
                raise DodonaException(
                    config.translator.error_status(ErrorType.INTERNAL_ERROR),
                    permission=MessagePermission.STAFF,
                    description=f"Could not retrieve solution content ({type(err).__name__}):\n    {err}",
                    format=MessageFormat.CODE,
                ) from err

            with Test(
                {
                    "description": config.translator.translate(Translator.Text.COMPARING_TABLE_CONTENT, table=table),
                    "format": MessageFormat.MARKDOWN,
                },
                solution_content.csv_out,
                format="csv",
            ) as test:
                test.generated = submission_content.csv_out
                test.status = config.translator.error_status(ErrorType.WRONG)
                testcase.accepted = False  # Signal that following on-success tests should not run

        if len(incorrect_name) + len(diff_layout) + len(diff_content) > 0:
            return

        affected_table = solution_query.first_match_array(correct)

        if affected_table is None:
            return

        try:
            solution_layout, submission_layout = database.get_table_layout(config, affected_table)
            solution_content, submission_content = database.get_table_content(config, affected_table)
        except Exception as err:
            raise DodonaException(
                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                permission=MessagePermission.STAFF,
                description=f"Could not retrieve solution layout & content ({type(err).__name__}):\n    {err}",
                format=MessageFormat.CODE,
            ) from err

        with Test(
            {
                "description": config.translator.translate(
                    Translator.Text.COMPARING_TABLE_LAYOUT, table=affected_table
                ),
                "format": MessageFormat.MARKDOWN,
            },
            solution_layout.csv_out,
            format="csv",
        ) as test:
            test.generated = submission_layout.csv_out
            test.status = config.translator.error_status(ErrorType.CORRECT)

        with Test(
            {
                "description": config.translator.translate(
                    Translator.Text.COMPARING_TABLE_CONTENT, table=affected_table
                ),
                "format": MessageFormat.MARKDOWN,
            },
            solution_content.csv_out,
            format="csv",
        ) as test:
            test.generated = submission_content.csv_out
            test.status = config.translator.error_status(ErrorType.CORRECT)
