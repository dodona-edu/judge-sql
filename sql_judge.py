import os
import sys
import sqlite3
from dodona_config import DodonaConfig
from dodona_command import (
    Judgement,
    Tab,
    Context,
    TestCase,
    Test,
    Message,
    Annotation,
    DodonaException,
    Permission,
    ErrorType,
    Format,
)
from sql_query import SQLQuery
from sql_query_result import SQLQueryResult
from os import path

# extract info from exercise configuration
config = DodonaConfig.from_json(sys.stdin)

with Judgement() as judgement:
    config.sanity_check()

    # Set 'max_rows' to 100 if not set
    config.max_rows = int(getattr(config, "max_rows", 100))

    # Set 'semicolon_warning' to True if not set
    config.semicolon_warning = bool(getattr(config, "semicolon_warning", True))

    # Set 'strict_identical_order_by' to True if not set
    config.strict_identical_order_by = bool(
        getattr(config, "strict_identical_order_by", True)
    )

    # Set 'allow_different_column_order' to True if not set
    config.allow_different_column_order = bool(
        getattr(config, "allow_different_column_order", True)
    )

    if hasattr(config, "database_files"):
        config.database_files = list(config.database_files)
    else:
        # Set 'database_dir' to "." if not set
        config.database_dir = str(getattr(config, "database_dir", "."))
        config.database_dir = path.join(config.resources, config.database_dir)

        if not path.exists(config.database_dir):
            # This will cause an Dodona "internal error"
            raise DodonaException(
                ErrorType.INTERNAL_ERROR,
                Permission.STAFF,
                f"Could not find database directory: '{config.database_dir}'.",
            )

        config.database_files = [
            filename
            for filename in sorted(os.listdir(config.database_dir))
            if filename.endswith(".sqlite")
        ]

    if len(config.database_files) == 0:
        # This will cause an Dodona "internal error"
        raise DodonaException(
            ErrorType.INTERNAL_ERROR,
            Permission.STAFF,
            f"Could not find database files. Make sure that the database directory contains '*.sqlite' files or a valid 'database_files' option is provided.",
        )

    # Set 'solution_sql' to "./solution.sql" if not set
    config.solution_sql = str(getattr(config, "solution_sql", "./solution.sql"))
    config.solution_sql = path.join(config.resources, config.solution_sql)

    if not path.exists(config.solution_sql):
        # This will cause an Dodona "internal error"
        raise DodonaException(
            ErrorType.INTERNAL_ERROR,
            Permission.STAFF,
            f"Could not find solution file: '{config.solution_sql}'.",
        )

    # Parse solution query
    with open(config.solution_sql) as sql_file:
        config.raw_solution_file = sql_file.read()
        config.solution_queries = SQLQuery.from_raw_input(config.raw_solution_file)

        if len(config.solution_queries) == 0:
            raise DodonaException(
                ErrorType.INTERNAL_ERROR,
                Permission.STAFF,
                f"Solution file is empty.",
            )

    # Parse submission query
    with open(config.source) as sql_file:
        config.raw_submission_file = sql_file.read()
        config.submission_queries = SQLQuery.from_raw_input(config.raw_submission_file)

    if len(config.submission_queries) > len(config.solution_queries):
        raise DodonaException(
            ErrorType.RUNTIME_ERROR,
            Permission.STUDENT,
            f"Error: the submitted solution contains more queries ({len(config.submission_queries)}) "
            f"than expected ({len(config.solution_queries)}). Make sure that all queries correctly terminate with a semicolon.",
            Format.CALLOUT,
        )

    if config.semicolon_warning and config.submission_queries[-1].formatted[-1] != ";":
        with Annotation(
            row=config.raw_submission_file.rstrip().count("\n"),
            type="warning",
            text='Add a semicolon ";" at the end of each SQL query.',
        ):
            pass

    for query_nr in range(len(config.solution_queries)):
        with Tab(f"Query {1 + query_nr}"):
            if query_nr >= len(config.submission_queries):
                raise DodonaException(
                    ErrorType.RUNTIME_ERROR,
                    Permission.STUDENT,
                    f"Error: the submitted solution contains less queries ({len(config.submission_queries)}) "
                    f"than expected ({len(config.solution_queries)}). Make sure that all queries correctly terminate with a semicolon.",
                    Format.CALLOUT,
                )

            solution_query = config.solution_queries[query_nr]
            submission_query = config.submission_queries[query_nr]

            for filename in config.database_files:
                with Context(), TestCase(
                    {
                        "format": Format.SQL,
                        "description": f"-- sqlite3 {filename}\n{submission_query.formatted}",
                    }
                ) as testcase:
                    expected_output, generated_output = None, None

                    db_file = f"{config.database_dir}/{filename}"

                    connection = sqlite3.connect(db_file)
                    cursor = connection.cursor()

                    if not solution_query.is_select:
                        # TODO(#12): support non-select queries and copy file + compare db using https://sqlite.org/sqldiff.html
                        raise DodonaException(
                            ErrorType.INTERNAL_ERROR,
                            Permission.STAFF,
                            f"Non-select queries not yet supported.",
                        )

                    #### RUN SOLUTION QUERY
                    try:
                        cursor.execute(solution_query.formatted)
                    except Exception as err:
                        raise DodonaException(
                            ErrorType.INTERNAL_ERROR,
                            Permission.STAFF,
                            f"Solution is not working: {err}",
                        )

                    #### RENDER SOLUTION QUERY OUTPUT
                    expected_output = SQLQueryResult.from_cursor(
                        config.max_rows, cursor
                    )

                    # if SELECT is not ordered -> fix ordering by sorting all rows
                    if solution_query.is_ordered:
                        expected_output.sort_rows()

                    #### RUN SUBMISSION QUERY
                    try:
                        cursor.execute(submission_query.formatted)
                    except Exception as err:
                        testcase.accepted = False
                        judgement.accepted = False
                        judgement.status = {"enum": "compilation error"}
                        with Message(
                            {
                                "format": Format.CODE,
                                "description": f"{type(err).__name__}:\n    {err}",
                            }
                        ):
                            pass

                        exit()

                    #### RENDER SUBMISSION QUERY OUTPUT
                    generated_output = SQLQueryResult.from_cursor(
                        config.max_rows, cursor
                    )

                    # if SELECT is not ordered -> fix ordering by sorting all rows
                    if not solution_query.is_ordered:
                        generated_output.sort_rows()

                    if config.allow_different_column_order:
                        expected_output.index_columns(generated_output.columns)

                    # TODO(#7): add custom compare function that only compares subsection of columns
                    with Test(
                        "Comparing query output csv content",
                        expected_output.csv_out,
                    ) as test:
                        test.generated = generated_output.csv_out

                        if len(expected_output.df.index) != len(
                            generated_output.df.index
                        ):
                            with Message(
                                {
                                    "format": Format.CALLOUT,
                                    "description": f"Expected row count {len(expected_output.df.index)}, your row count was {len(generated_output.df.index)}.",
                                }
                            ):
                                pass

                        if len(expected_output.df.columns) != len(
                            generated_output.df.columns
                        ):
                            with Message(
                                {
                                    "format": Format.CALLOUT,
                                    "description": f"Expected column count {len(expected_output.df.columns)}, your column count was {len(generated_output.df.columns)}.",
                                }
                            ):
                                pass

                        if expected_output.csv_out == generated_output.csv_out:
                            test.status = {"enum": "correct"}
                        else:
                            test.status = {"enum": "wrong"}
                            # TODO(#18): if wrong, and solution_query.is_ordered; try ordering columns and check if result is correct.

                    # TODO(#7): add custom compare function that only compares subsection of columns
                    with Test(
                        "Comparing query output types", expected_output.types_out
                    ) as test:
                        test.generated = generated_output.types_out

                        if expected_output.types_out == generated_output.types_out:
                            test.status = {"enum": "correct"}
                        else:
                            test.status = {"enum": "wrong"}

                    if (
                        config.strict_identical_order_by
                        and submission_query.is_ordered != solution_query.is_ordered
                    ):
                        with Test(
                            "Query should return ordered rows."
                            if solution_query.is_ordered
                            else "No explicit row ordering should be enforced in query.",
                            "rows are being ordered"
                            if solution_query.is_ordered
                            else "rows are not being ordered",
                        ) as test:
                            test.generated = (
                                "rows are being ordered"
                                if submission_query.is_ordered
                                else "rows are not being ordered"
                            )

                            if submission_query.is_ordered == solution_query.is_ordered:
                                test.status = {"enum": "correct"}
                            else:
                                test.status = {"enum": "wrong"}
