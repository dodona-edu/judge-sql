"""sql feedback for select queries"""

from types import SimpleNamespace

import numpy as np

from dodona_command import (
    Test,
    Message,
    ErrorType,
    MessageFormat,
)
from sql_query_result import SQLQueryResult
from translator import Translator
from sql_query import SQLQuery
from dodona_config import DodonaConfig


def select_feedback(
    config: DodonaConfig,
    testcase: SimpleNamespace,
    expected_output: SQLQueryResult,
    generated_output: SQLQueryResult,
    solution_query: SQLQuery,
    submission_query: SQLQuery,
):
    """run tests based on database status after running a non-select query"""
    if config.allow_different_column_order:
        expected_output.index_columns(generated_output.columns)

    # if SELECT is not ordered -> fix ordering by sorting all rows
    if not solution_query.is_ordered:
        sort_on = np.intersect1d(expected_output.columns, generated_output.columns)
        expected_output.sort_rows(sort_on)
        generated_output.sort_rows(sort_on)

    # TODO(#7): add custom compare function that only compares subsection of columns
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

            # TODO(#18): if wrong, and solution_query.is_ordered;
            # try ordering columns and check if result is correct.

    # TODO(#7): add custom compare function that only compares subsection of columns
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
        with Test(
            config.translator.translate(
                Translator.Text.QUERY_SHOULD_ORDER_ROWS
                if solution_query.is_ordered
                else Translator.Text.QUERY_SHOULD_NOT_ORDER_ROWS
            ),
            config.translator.translate(
                Translator.Text.ROWS_ARE_BEING_ORDERED
                if solution_query.is_ordered
                else Translator.Text.ROWS_ARE_NOT_BEING_ORDERED
            ),
        ) as test:
            test.generated = config.translator.translate(
                Translator.Text.ROWS_ARE_BEING_ORDERED
                if submission_query.is_ordered
                else Translator.Text.ROWS_ARE_NOT_BEING_ORDERED
            )

            test.status = config.translator.error_status(ErrorType.WRONG)
            testcase.accepted = False  # Signal that following on-success tests should not run
