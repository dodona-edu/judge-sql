"""sql judge main script."""

import sys
from pathlib import Path

from judge.dodona_command import (
    Annotation,
    AnnotationSeverity,
    Context,
    DodonaException,
    ErrorType,
    Judgement,
    MessageFormat,
    MessagePermission,
    Tab,
    TestCase,
)
from judge.dodona_config import UNSET, DodonaConfig
from judge.sql_database import SQLDatabase, sql_run_pragma_startup_queries
from judge.sql_judge_non_select_feedback import non_select_feedback
from judge.sql_judge_select_feedback import select_feedback
from judge.sql_query import SQLQuery
from judge.sql_query_result import SQLQueryResult
from judge.translator import Translator

# extract info from exercise configuration
config = DodonaConfig.from_json(sys.stdin.read())

with Judgement():
    config.sanity_check()

    config.coerce_evaluation_options()

    if config.database_files is not UNSET:
        config.databases = [
            (str(filename), str(Path(config.resources) / filename)) for filename in config.database_files
        ]

        for _, file in config.databases:
            if not Path(file).exists():
                raise DodonaException(
                    config.translator.error_status(ErrorType.INTERNAL_ERROR),
                    permission=MessagePermission.STAFF,
                    description=f"Could not find database file: '{file}'.",
                    format=MessageFormat.TEXT,
                )
    else:
        config.database_dir = str(Path(config.resources) / config.database_dir)

        if not Path(config.database_dir).exists():
            raise DodonaException(
                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                permission=MessagePermission.STAFF,
                description=f"Could not find database directory: '{config.database_dir}'.",
                format=MessageFormat.TEXT,
            )

        config.databases = [
            (path.name, str(path)) for path in sorted(Path(config.database_dir).iterdir()) if path.suffix == ".sqlite"
        ]

    if len(config.databases) == 0:
        raise DodonaException(
            config.translator.error_status(ErrorType.INTERNAL_ERROR),
            permission=MessagePermission.STAFF,
            description="Could not find database files. "
            "Make sure that the database directory contains '*.sqlite' "
            "files or a valid 'database_files' option is provided.",
            format=MessageFormat.TEXT,
        )

    config.solution_sql = str(Path(config.resources) / config.solution_sql)

    if not Path(config.solution_sql).exists():
        raise DodonaException(
            config.translator.error_status(ErrorType.INTERNAL_ERROR),
            permission=MessagePermission.STAFF,
            description=f"Could not find solution file: '{config.solution_sql}'.",
            format=MessageFormat.TEXT,
        )

    # Parse solution query
    with Path(config.solution_sql).open(encoding="utf-8") as sql_file:
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
    with Path(config.source).open(encoding="utf-8") as sql_file:
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
        len(config.submission_queries) == 0 or not config.submission_queries[-1].has_ending_semicolon
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

            if solution_query.query_type != submission_query.query_type:
                raise DodonaException(
                    config.translator.error_status(ErrorType.RUNTIME_ERROR),
                    permission=MessagePermission.STUDENT,
                    description=config.translator.translate(
                        Translator.Text.SUBMISSION_WRONG_QUERY_TYPE,
                        submitted=submission_query.query_type,
                    ),
                    format=MessageFormat.CALLOUT_DANGER,
                )

            match = submission_query.match_multi_regex(
                config.pre_execution_forbidden_symbolregex,
                config.pre_execution_mandatory_symbolregex,
                config.pre_execution_forbidden_fullregex,
                config.pre_execution_mandatory_fullregex,
            )
            if match is not None:
                raise DodonaException(
                    config.translator.error_status(ErrorType.RUNTIME_ERROR),
                    permission=MessagePermission.STUDENT,
                    description=config.translator.translate(
                        match[0],
                        value=match[1],
                    ),
                    format=MessageFormat.CALLOUT_DANGER,
                )

            for db_name, db_file in config.databases:
                with (
                    Context(),
                    TestCase(
                        format=MessageFormat.SQL,
                        description=f"-- sqlite3 {db_name}\n{submission_query.without_comments}",
                    ) as testcase,
                ):
                    expected_output: SQLQueryResult
                    generated_output: SQLQueryResult

                    with SQLDatabase(db_file, config.workdir, db_name) as db:
                        cursor = db.solution_cursor()

                        try:
                            if config.pragma_startup_queries != "":
                                sql_run_pragma_startup_queries(cursor, config.pragma_startup_queries)
                        except Exception as err:
                            raise DodonaException(
                                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                                permission=MessagePermission.STAFF,
                                description=f"Startup script is not working ({type(err).__name__}):\n    {err}",
                                format=MessageFormat.CODE,
                            ) from err

                        # RUN SOLUTION QUERY
                        try:
                            cursor.execute(solution_query.without_comments)
                        except Exception as err:
                            raise DodonaException(
                                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                                permission=MessagePermission.STAFF,
                                description=f"Solution is not working ({type(err).__name__}):\n    {err}",
                                format=MessageFormat.CODE,
                            ) from err

                        # RENDER SOLUTION QUERY OUTPUT
                        expected_output = SQLQueryResult.from_cursor(config.max_rows, cursor)

                        cursor = db.submission_cursor()

                        try:
                            if config.pragma_startup_queries != "":
                                sql_run_pragma_startup_queries(cursor, config.pragma_startup_queries)
                        except Exception as err:
                            raise DodonaException(
                                config.translator.error_status(ErrorType.INTERNAL_ERROR),
                                permission=MessagePermission.STAFF,
                                description=f"Startup script is not working ({type(err).__name__}):\n    {err}",
                                format=MessageFormat.CODE,
                            ) from err

                        # RUN SUBMISSION QUERY
                        try:
                            cursor.execute(submission_query.without_comments)
                        except Exception as err:
                            raise DodonaException(
                                config.translator.error_status(ErrorType.COMPILATION_ERROR),
                                permission=MessagePermission.STUDENT,
                                description=f"{type(err).__name__}:\n    {err}",
                                format=MessageFormat.CODE,
                            ) from err

                        # RENDER SUBMISSION QUERY OUTPUT
                        generated_output = SQLQueryResult.from_cursor(config.max_rows, cursor)

                    if not solution_query.is_select:
                        non_select_feedback(config, testcase, db_name, db_file, solution_query)
                    else:
                        select_feedback(
                            config,
                            testcase,
                            expected_output,
                            generated_output,
                            solution_query,
                            submission_query,
                        )

                    if getattr(testcase, "accepted", True):  # Only run if all other tests are OK
                        match = submission_query.match_multi_regex(
                            config.post_execution_forbidden_symbolregex,
                            config.post_execution_mandatory_symbolregex,
                            config.post_execution_forbidden_fullregex,
                            config.post_execution_mandatory_fullregex,
                        )
                        if match is not None:
                            raise DodonaException(
                                config.translator.error_status(ErrorType.WRONG),
                                recover_at=Context,  # Continue testing all other contexts
                                permission=MessagePermission.STUDENT,
                                description=config.translator.translate(
                                    match[0],
                                    value=match[1],
                                ),
                                format=MessageFormat.CALLOUT_DANGER,
                            )
