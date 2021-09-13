"""sql feedback for non-select queries"""

from types import SimpleNamespace
from translator import Translator
from dodona_config import DodonaConfig
from dodona_command import (
    Test,
    DodonaException,
    ErrorType,
    MessagePermission,
    MessageFormat,
)
from sql_database import SQLDatabase


def non_select_feedback(config: DodonaConfig, testcase: SimpleNamespace, db_name: str, db_file: str):
    """run tests based on execution results of a select query"""
    with SQLDatabase(db_name, db_file, config.workdir) as database:
        incorrect_name, diff_layout, diff_content = database.diff()

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
                    description="Could not retrieve solution layout " f"({type(err).__name__}):\n    {err}",
                    format=MessageFormat.CODE,
                ) from err

            with Test(
                config.translator.translate(Translator.Text.COMPARING_TABLE_LAYOUT, table=table),
                solution_layout.csv_out,
                # format="csv",
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
                    description="Could not retrieve solution content " f"({type(err).__name__}):\n    {err}",
                    format=MessageFormat.CODE,
                ) from err

            with Test(
                config.translator.translate(Translator.Text.COMPARING_TABLE_CONTENT, table=table),
                solution_content.csv_out,
                # format="csv",
            ) as test:
                test.generated = submission_content.csv_out
                test.status = config.translator.error_status(ErrorType.WRONG)
                testcase.accepted = False  # Signal that following on-success tests should not run
