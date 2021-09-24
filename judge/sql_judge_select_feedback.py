"""sql feedback for select queries."""

from types import SimpleNamespace

import numpy as np

from .dodona_command import (
    Context,
    DodonaException,
    ErrorType,
    Message,
    MessageFormat,
    MessagePermission,
    Test,
)
from .dodona_config import DodonaConfig
from .sql_query import SQLQuery
from .sql_query_result import SQLQueryResult
from .translator import Translator


def select_feedback(
    config: DodonaConfig,
    testcase: SimpleNamespace,
    expected_output: SQLQueryResult,
    generated_output: SQLQueryResult,
    solution_query: SQLQuery,
    submission_query: SQLQuery,
) -> None:
    """Run tests based on database status after running a non-select query.

    Args:
        config: parsed config received from Dodona
        testcase: testcase object used to return values to Dodona
        expected_output: select query expected output
        generated_output: select query generated output
        solution_query: the parsed solution query
        submission_query: the parsed submission query

    Raises:
        DodonaException: custom exception that is automatically handled by the 'with' blocks
    """
    if config.allow_different_column_order:
        expected_output.index_columns(generated_output.columns)

    # if SELECT is not ordered -> fix ordering by sorting all rows
    if not solution_query.is_ordered:
        sort_on = np.intersect1d(expected_output.columns, generated_output.columns)
        expected_output.sort_rows(sort_on)
        generated_output.sort_rows(sort_on)

    with Test(
        config.translator.translate(Translator.Text.COMPARING_QUERY_OUTPUT_CSV_CONTENT),
        expected_output.csv_out,
        format="csv",
    ) as test:
        test.generated = generated_output.csv_out

        if len(expected_output.dataframe.columns) != len(generated_output.dataframe.columns):
            with Message(
                format=MessageFormat.CALLOUT_DANGER,
                description=config.translator.translate(
                    Translator.Text.DIFFERENT_COLUMN_COUNT,
                    expected=len(expected_output.dataframe.columns),
                    submitted=len(generated_output.dataframe.columns),
                ),
            ):
                pass

        if len(expected_output.dataframe.index) != len(generated_output.dataframe.index):
            with Message(
                format=MessageFormat.CALLOUT_DANGER,
                description=config.translator.translate(
                    Translator.Text.DIFFERENT_ROW_COUNT,
                    expected=len(expected_output.dataframe.index),
                    submitted=len(generated_output.dataframe.index),
                ),
            ):
                pass

        if expected_output.csv_out == generated_output.csv_out:
            test.status = config.translator.error_status(ErrorType.CORRECT)
        else:
            test.status = config.translator.error_status(ErrorType.WRONG)
            testcase.accepted = False  # Signal that following on-success tests should not run

            # if SELECT is ordered -> check if rows are correct but order is wrong
            if solution_query.is_ordered:
                sort_on = np.intersect1d(expected_output.columns, generated_output.columns)
                expected_output.sort_rows(sort_on)
                generated_output.sort_rows(sort_on)

                if expected_output.csv_out == generated_output.csv_out:
                    with Message(
                        format=MessageFormat.CALLOUT_INFO,
                        description=config.translator.translate(Translator.Text.CORRECT_ROWS_WRONG_ORDER),
                    ):
                        pass

    with Test(
        config.translator.translate(Translator.Text.COMPARING_QUERY_OUTPUT_TYPES),
        expected_output.types_out,
    ) as test:
        test.generated = generated_output.types_out

        if expected_output.types_out == generated_output.types_out:
            test.status = config.translator.error_status(ErrorType.CORRECT)
        else:
            test.status = config.translator.error_status(ErrorType.WRONG)
            testcase.accepted = False  # Signal that following on-success tests should not run

    if (
        config.strict_identical_order_by
        and getattr(testcase, "accepted", True)  # Only run if all other tests are OK
        and submission_query.is_ordered != solution_query.is_ordered  # Only run if result is wrong
    ):
        raise DodonaException(
            config.translator.error_status(ErrorType.WRONG),
            recover_at=Context,  # Continue testing all other contexts
            permission=MessagePermission.STUDENT,
            description=config.translator.translate(
                Translator.Text.QUERY_SHOULD_ORDER_ROWS
                if solution_query.is_ordered
                else Translator.Text.QUERY_SHOULD_NOT_ORDER_ROWS
            ),
            format=MessageFormat.CALLOUT_DANGER,
        )
