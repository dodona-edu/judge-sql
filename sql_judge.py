"""sql judge main script."""

import sys
from pathlib import Path
lazy import sqlite3

from judge.dodona_command import (
    Annotation,
    AnnotationSeverity,
    Context,
    ErrorType,
    Judgement,
    MessageFormat,
    Tab,
    TestCase,
)
from judge.dodona_config import UNSET, DodonaConfig
from judge.errors import internal_error, student_error
from judge.sql_database import SQLDatabase, sql_run_pragma_startup_queries
from judge.sql_judge_non_select_feedback import non_select_feedback
from judge.sql_judge_select_feedback import select_feedback
from judge.sql_query import SQLQuery
from judge.sql_query_result import SQLQueryResult
from judge.translator import Translator


def _resolve_databases(config: DodonaConfig) -> list[tuple[str, str]]:
    """Find the databases to run the queries on.

    Args:
        config: parsed config received from Dodona

    Returns:
        `(name, path)` of every database

    Raises:
        DodonaException: a database file or the database directory is missing, or there are no databases
    """
    if config.database_files is not UNSET:
        databases = [(str(filename), str(Path(config.resources) / filename)) for filename in config.database_files]

        for _, file in databases:
            if not Path(file).exists():
                raise internal_error(config, f"Could not find database file: '{file}'.")
    else:
        database_dir = Path(config.resources) / config.database_dir

        if not database_dir.exists():
            raise internal_error(config, f"Could not find database directory: '{database_dir}'.")

        databases = [(path.name, str(path)) for path in sorted(database_dir.iterdir()) if path.suffix == ".sqlite"]

    if not databases:
        raise internal_error(
            config,
            "Could not find database files. "
            "Make sure that the database directory contains '*.sqlite' "
            "files or a valid 'database_files' option is provided.",
        )

    return databases


def _read_solution(config: DodonaConfig) -> list[SQLQuery]:
    """Read and parse the solution file.

    Args:
        config: parsed config received from Dodona

    Returns:
        the solution queries

    Raises:
        DodonaException: the solution file is missing or empty
    """
    solution_sql = Path(config.resources) / config.solution_sql

    if not solution_sql.exists():
        raise internal_error(config, f"Could not find solution file: '{solution_sql}'.")

    solution_queries = SQLQuery.from_raw_input(solution_sql.read_text(encoding="utf-8"))

    if not solution_queries:
        raise internal_error(config, "Solution file is empty.")

    return solution_queries


def _read_submission(config: DodonaConfig, solution_queries: list[SQLQuery]) -> list[SQLQuery]:
    """Read and parse the submission, and warn when its last semicolon is missing.

    Args:
        config: parsed config received from Dodona
        solution_queries: the solution queries

    Returns:
        the submission queries

    Raises:
        DodonaException: the submission has more queries than the solution
    """
    raw_submission = Path(config.source).read_text(encoding="utf-8")
    submission_queries = SQLQuery.from_raw_input(raw_submission)

    if len(submission_queries) > len(solution_queries):
        raise student_error(
            config,
            ErrorType.RUNTIME_ERROR,
            config.translator.translate(
                Translator.Text.SUBMISSION_CONTAINS_MORE_QUERIES,
                submitted=len(submission_queries),
                expected=len(solution_queries),
            ),
        )

    if config.semicolon_warning and (len(submission_queries) == 0 or not submission_queries[-1].has_ending_semicolon):
        with Annotation(
            row=raw_submission.rstrip().count("\n"),
            type=AnnotationSeverity.WARNING,
            text=config.translator.translate(Translator.Text.ADD_A_SEMICOLON),
        ):
            pass

    return submission_queries


def _check_before_execution(config: DodonaConfig, solution_query: SQLQuery, submission_query: SQLQuery) -> None:
    """Check the submission query's type and pre-execution regexes.

    Args:
        config: parsed config received from Dodona
        solution_query: the solution query
        submission_query: the submission query

    Raises:
        DodonaException: the query type differs or a pre-execution regex fails
    """
    if solution_query.query_type != submission_query.query_type:
        raise student_error(
            config,
            ErrorType.RUNTIME_ERROR,
            config.translator.translate(
                Translator.Text.SUBMISSION_WRONG_QUERY_TYPE,
                submitted=submission_query.query_type,
            ),
        )

    match = submission_query.match_multi_regex(
        config.pre_execution_forbidden_symbolregex,
        config.pre_execution_mandatory_symbolregex,
        config.pre_execution_forbidden_fullregex,
        config.pre_execution_mandatory_fullregex,
    )
    if match is not None:
        raise student_error(config, ErrorType.RUNTIME_ERROR, config.translator.translate(match[0], value=match[1]))


def _check_after_execution(config: DodonaConfig, submission_query: SQLQuery) -> None:
    """Check the submission query's post-execution regexes.

    Args:
        config: parsed config received from Dodona
        submission_query: the submission query

    Raises:
        DodonaException: a post-execution regex fails, recovered at the context
    """
    match = submission_query.match_multi_regex(
        config.post_execution_forbidden_symbolregex,
        config.post_execution_mandatory_symbolregex,
        config.post_execution_forbidden_fullregex,
        config.post_execution_mandatory_fullregex,
    )
    if match is not None:
        raise student_error(
            config,
            ErrorType.WRONG,
            config.translator.translate(match[0], value=match[1]),
            recover_at=Context,
        )


def _run_startup_script(config: DodonaConfig, cursor: sqlite3.Cursor) -> None:
    """Run the teacher's pragma startup queries, if any.

    Args:
        config: parsed config received from Dodona
        cursor: cursor to run the queries on

    Raises:
        DodonaException: the startup script fails
    """
    if config.pragma_startup_queries == "":
        return

    try:
        sql_run_pragma_startup_queries(cursor, config.pragma_startup_queries)
    except Exception as err:
        raise internal_error(
            config,
            f"Startup script is not working ({type(err).__name__}):\n    {err}",
            message_format=MessageFormat.CODE,
        ) from err


def _judge_database(
    config: DodonaConfig, db_name: str, db_file: str, solution_query: SQLQuery, submission_query: SQLQuery
) -> None:
    """Run one query pair on one database and give feedback in its own context.

    Args:
        config: parsed config received from Dodona
        db_name: the name of the database
        db_file: the location of the database file
        solution_query: the solution query
        submission_query: the submission query
    """
    with (
        Context(),
        TestCase(
            format=MessageFormat.SQL,
            description=f"-- sqlite3 {db_name}\n{submission_query.without_comments}",
        ) as testcase,
    ):
        with SQLDatabase(db_file, config.workdir, db_name) as db:
            solution_cursor = db.solution_cursor()
            _run_startup_script(config, solution_cursor)
            try:
                solution_cursor.execute(solution_query.without_comments)
            except Exception as err:
                raise internal_error(
                    config,
                    f"Solution is not working ({type(err).__name__}):\n    {err}",
                    message_format=MessageFormat.CODE,
                ) from err
            expected_output = SQLQueryResult.from_cursor(config.max_rows, solution_cursor)

            submission_cursor = db.submission_cursor()
            _run_startup_script(config, submission_cursor)
            try:
                submission_cursor.execute(submission_query.without_comments)
            except Exception as err:
                raise student_error(
                    config,
                    ErrorType.COMPILATION_ERROR,
                    f"{type(err).__name__}:\n    {err}",
                    message_format=MessageFormat.CODE,
                ) from err
            generated_output = SQLQueryResult.from_cursor(config.max_rows, submission_cursor)

        if not solution_query.is_select:
            accepted = non_select_feedback(config, db_name, db_file, solution_query)
        else:
            accepted = select_feedback(config, expected_output, generated_output, solution_query, submission_query)

        if accepted:
            _check_after_execution(config, submission_query)
        else:
            testcase.accepted = False


def _judge_query(
    config: DodonaConfig,
    databases: list[tuple[str, str]],
    solution_queries: list[SQLQuery],
    submission_queries: list[SQLQuery],
    query_nr: int,
) -> None:
    """Judge one query pair on every database in its own tab.

    Args:
        config: parsed config received from Dodona
        databases: `(name, path)` of every database
        solution_queries: the solution queries
        submission_queries: the submission queries
        query_nr: index of the query pair
    """
    solution_query = solution_queries[query_nr]

    with Tab(title=f"Query {1 + query_nr}"):
        if query_nr >= len(submission_queries):
            raise student_error(
                config,
                ErrorType.RUNTIME_ERROR,
                config.translator.translate(
                    Translator.Text.SUBMISSION_CONTAINS_LESS_QUERIES,
                    expected=len(solution_queries),
                    submitted=len(submission_queries),
                ),
            )

        submission_query = submission_queries[query_nr]
        _check_before_execution(config, solution_query, submission_query)

        for db_name, db_file in databases:
            _judge_database(config, db_name, db_file, solution_query, submission_query)


def main() -> None:
    """Judge the submission described by the Dodona config on stdin."""
    config = DodonaConfig.from_json(sys.stdin.read())

    with Judgement():
        config.sanity_check()
        config.coerce_evaluation_options()

        databases = _resolve_databases(config)
        solution_queries = _read_solution(config)
        submission_queries = _read_submission(config, solution_queries)

        for query_nr in range(len(solution_queries)):
            _judge_query(config, databases, solution_queries, submission_queries, query_nr)


# Unconditional: tests/test_e2e.py runs this file with runpy.run_path, which doesn't set __name__ to "__main__".
main()
