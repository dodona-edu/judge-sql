"""sql judge main script"""

import os
import sqlite3
import sys
from os import path

import numpy as np

from dodona_command import (
    AnnotationSeverity,
    Judgement,
    Tab,
    Context,
    TestCase,
    Test,
    Message,
    Annotation,
    DodonaException,
    ErrorType,
    MessagePermission,
    MessageFormat,
)
from dodona_config import DodonaConfig
from sql_query import SQLQuery
from sql_query_result import SQLQueryResult
from translator import Translator

# extract info from exercise configuration
config = DodonaConfig.from_json(sys.stdin)

with Judgement():
    config.sanity_check()

    # Initiate translator
    config.translator = Translator.from_str(config.natural_language)

    # Set 'max_rows' to 100 if not set
    config.max_rows = int(getattr(config, "max_rows", 100))

    # Set 'semicolon_warning' to True if not set
    config.semicolon_warning = bool(getattr(config, "semicolon_warning", True))

    # Set 'strict_identical_order_by' to True if not set
    config.strict_identical_order_by = bool(getattr(config, "strict_identical_order_by", True))

    # Set 'allow_different_column_order' to True if not set
    config.allow_different_column_order = bool(getattr(config, "allow_different_column_order", True))

    if hasattr(config, "database_files"):
        config.database_files = [
            (str(filename), path.join(config.resources, filename)) for filename in config.database_files
        ]

        for filename, file in config.database_files:
            if not path.exists(file):
                raise DodonaException(
                    config.translator.error_status(ErrorType.INTERNAL_ERROR),
                    permission=MessagePermission.STAFF,
                    description=f"Could not find database file: '{file}'.",
                    format=MessageFormat.TEXT,
                )
    else:
        # Set 'database_dir' to "." if not set
        config.database_dir = str(getattr(config, "database_dir", "."))
        config.database_dir = path.join(config.resources, config.database_dir)

        if not path.exists(config.database_dir):
            raise DodonaException(
                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                permission=MessagePermission.STAFF,
                description=f"Could not find database directory: '{config.database_dir}'.",
                format=MessageFormat.TEXT,
            )

        config.database_files = [
            (filename, path.join(config.database_dir, filename))
            for filename in sorted(os.listdir(config.database_dir))
            if filename.endswith(".sqlite")
        ]

    if len(config.database_files) == 0:
        raise DodonaException(
            config.translator.error_status(ErrorType.INTERNAL_ERROR),
            permission=MessagePermission.STAFF,
            description="Could not find database files. "
            "Make sure that the database directory contains '*.sqlite' "
            "files or a valid 'database_files' option is provided.",
            format=MessageFormat.TEXT,
        )

    # Set 'solution_sql' to "./solution.sql" if not set
    config.solution_sql = str(getattr(config, "solution_sql", "./solution.sql"))
    config.solution_sql = path.join(config.resources, config.solution_sql)

    if not path.exists(config.solution_sql):
        raise DodonaException(
            config.translator.error_status(ErrorType.INTERNAL_ERROR),
            permission=MessagePermission.STAFF,
            description=f"Could not find solution file: '{config.solution_sql}'.",
            format=MessageFormat.TEXT,
        )

    # Parse solution query
    with open(config.solution_sql, "r", encoding="utf-8") as sql_file:
        config.raw_solution_file = sql_file.read()
        config.solution_queries = SQLQuery.from_raw_input(config.raw_solution_file)

        if len(config.solution_queries) == 0:
            raise DodonaException(
                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                permission=MessagePermission.STAFF,
                description="Solution file is empty.",
                format=MessageFormat.TEXT,
            )

    # Parse submission query
    with open(config.source, "r", encoding="utf-8") as sql_file:
        config.raw_submission_file = sql_file.read()
        config.submission_queries = SQLQuery.from_raw_input(config.raw_submission_file)

    if len(config.submission_queries) > len(config.solution_queries):
        raise DodonaException(
            config.translator.error_status(ErrorType.RUNTIME_ERROR),
            permission=MessagePermission.STUDENT,
            description=config.translator.translate(
                Translator.Text.SUBMISSION_CONTAINS_MORE_QUERIES,
                submitted=len(config.submission_queries),
                expected=len(config.solution_queries),
            ),
            format=MessageFormat.CALLOUT_DANGER,
        )

    if config.semicolon_warning and (
        len(config.submission_queries) == 0
        or len(config.submission_queries[-1].formatted) == 0
        or config.submission_queries[-1].formatted[-1] != ";"
    ):
        with Annotation(
            row=config.raw_submission_file.rstrip().count("\n"),
            type=AnnotationSeverity.WARNING,
            text=config.translator.translate(Translator.Text.ADD_A_SEMICOLON),
        ):
            pass

    for query_nr, solution_query in enumerate(config.solution_queries):
        with Tab(f"Query {1 + query_nr}"):
            if query_nr >= len(config.submission_queries):
                raise DodonaException(
                    config.translator.error_status(ErrorType.RUNTIME_ERROR),
                    permission=MessagePermission.STUDENT,
                    description=config.translator.translate(
                        Translator.Text.SUBMISSION_CONTAINS_LESS_QUERIES,
                        expected=len(config.solution_queries),
                        submitted=len(config.submission_queries),
                    ),
                    format=MessageFormat.CALLOUT_DANGER,
                )

            submission_query = config.submission_queries[query_nr]

            for filename, db_file in config.database_files:
                with Context(), TestCase(
                    format=MessageFormat.SQL,
                    description=f"-- sqlite3 {filename}\n{submission_query.formatted}",
                ):
                    expected_output, generated_output = None, None

                    connection = sqlite3.connect(db_file)
                    cursor = connection.cursor()

                    if not solution_query.is_select:
                        # TODO(#12): support non-select queries and copy file
                        # + compare db using https://sqlite.org/sqldiff.html
                        raise DodonaException(
                            config.translator.error_status(ErrorType.INTERNAL_ERROR),
                            permission=MessagePermission.STAFF,
                            description="Non-select queries not yet supported.",
                            format=MessageFormat.TEXT,
                        )

                    #### RUN SOLUTION QUERY
                    try:
                        cursor.execute(solution_query.formatted)
                    except Exception as err:
                        raise DodonaException(
                            config.translator.error_status(ErrorType.INTERNAL_ERROR),
                            permission=MessagePermission.STAFF,
                            description=f"Solution is not working ({type(err).__name__}):\n    {err}",
                            format=MessageFormat.CODE,
                        ) from err

                    #### RENDER SOLUTION QUERY OUTPUT
                    expected_output = SQLQueryResult.from_cursor(config.max_rows, cursor)

                    #### RUN SUBMISSION QUERY
                    try:
                        cursor.execute(submission_query.formatted)
                    except Exception as err:
                        raise DodonaException(
                            config.translator.error_status(ErrorType.COMPILATION_ERROR),
                            permission=MessagePermission.STUDENT,
                            description=f"{type(err).__name__}:\n    {err}",
                            format=MessageFormat.CODE,
                        ) from err

                    #### RENDER SUBMISSION QUERY OUTPUT
                    generated_output = SQLQueryResult.from_cursor(config.max_rows, cursor)

                    connection.close()

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

                    if config.strict_identical_order_by and submission_query.is_ordered != solution_query.is_ordered:
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

                            if submission_query.is_ordered == solution_query.is_ordered:
                                test.status = config.translator.error_status(ErrorType.CORRECT)
                            else:
                                test.status = config.translator.error_status(ErrorType.WRONG)
