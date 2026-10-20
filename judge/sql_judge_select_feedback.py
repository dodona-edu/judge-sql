"""sql feedback for select queries."""

lazy from types import SimpleNamespace

from .dodona_command import (
    Context,
    DodonaException,
    ErrorType,
    Message,
    MessageFormat,
    MessagePermission,
    Test,
)
from .translator import Translator
lazy from .dodona_config import DodonaConfig
lazy from .sql_query import SQLQuery
lazy from .sql_query_result import SQLQueryResult


def _sort_on_common_columns(expected_output: SQLQueryResult, generated_output: SQLQueryResult) -> None:
    """Sort the rows of both results on the columns they have in common.

    Args:
        expected_output: select query expected output
        generated_output: select query generated output
    """
    sort_on = sorted(set(expected_output.columns) & set(generated_output.columns))
    expected_output.sort_rows(sort_on)
    generated_output.sort_rows(sort_on)


def select_feedback(  # noqa: PLR0913, PLR0917
    config: DodonaConfig,
    testcase: SimpleNamespace,
    expected_output: SQLQueryResult,
    generated_output: SQLQueryResult,
    solution_query: SQLQuery,
    submission_query: SQLQuery,
) -> None:
    """Run tests based on execution results of a select query.

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
    if config.order_unordered_rows and not solution_query.is_ordered:
        _sort_on_common_columns(expected_output, generated_output)

    with Test(
        config.translator.translate(Translator.Text.COMPARING_QUERY_OUTPUT_CSV_CONTENT),
        expected_output.csv_out,
        format="csv",
    ) as test:
        test.generated = generated_output.csv_out

        if expected_output.column_count != generated_output.column_count:
            with Message(
                format=MessageFormat.CALLOUT_DANGER,
                description=config.translator.translate(
                    Translator.Text.DIFFERENT_COLUMN_COUNT,
                    expected=expected_output.column_count,
                    submitted=generated_output.column_count,
                ),
            ):
                pass

        if expected_output.row_count != generated_output.row_count:
            with Message(
                format=MessageFormat.CALLOUT_DANGER,
                description=config.translator.translate(
                    Translator.Text.DIFFERENT_ROW_COUNT,
                    expected=expected_output.row_count,
                    submitted=generated_output.row_count,
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
                _sort_on_common_columns(expected_output, generated_output)

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
