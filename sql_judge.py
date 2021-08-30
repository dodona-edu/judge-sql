import os
import io
from sqlite3 import Cursor
import sys
import sqlite3
import pandas as pd
from dodona_config import DodonaConfig
from dodona_command import Judgement, Tab, Context, TestCase, Test, Message, Annotation
from sql_query import SQLQuery
from os import path
from dataclasses import dataclass

python_type_to_sqlite_type = {
    None: "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
}


@dataclass
class QueryRender:
    dataframe: pd.core.frame.DataFrame
    csv_out: str
    types_out: str


def render_query_output(is_ordered: bool, cur: Cursor) -> QueryRender:
    csv_output = io.StringIO()

    rows = cur.fetchmany(config.max_rows)
    columns = [column[0] for column in cur.description or []]

    df = pd.DataFrame(rows, columns=columns)

    # if SELECT is not ordered -> fix ordering by sorting all rows
    if not is_ordered and not df.empty:
        df.sort_values(by=df.columns.tolist(), inplace=True)

    df.to_csv(csv_output, index=False)

    type_description = ""
    if len(rows) > 0:
        types = [python_type_to_sqlite_type[type(x)] for x in rows[0]]
        type_description = "\n".join(f"{c} [{t}]" for (c, t) in zip(columns, types))

    return QueryRender(
        dataframe=df,
        csv_out=csv_output.getvalue(),
        types_out=type_description,
    )


if __name__ == "__main__":
    # extract info from exercise configuration
    config = DodonaConfig.from_json(sys.stdin)

    config.sanity_check()

    # Set 'max_rows' to 100 if not set
    config.max_rows = int(getattr(config, "max_rows", 100))

    # Set 'semicolon_warning' to True if not set
    config.semicolon_warning = bool(getattr(config, "semicolon_warning", True))

    # Set 'database_dir' to "./databases" if not set
    config.database_dir = str(getattr(config, "database_dir", "./databases"))
    config.database_dir = path.join(config.resources, config.database_dir)

    if not path.exists(config.database_dir):
        # This will cause an Dodona "internal error"
        raise ValueError(f"Could not find database directory: '{config.database_dir}'.")

    # Set 'solution_sql' to "./solution.sql" if not set
    config.solution_sql = str(getattr(config, "solution_sql", "./solution.sql"))
    config.solution_sql = path.join(config.resources, config.solution_sql)

    if not path.exists(config.solution_sql):
        # This will cause an Dodona "internal error"
        raise ValueError(f"Could not find solution file: '{config.solution_sql}'.")

    # Parse solution query
    with open(config.solution_sql) as sql_file:
        config.raw_solution_file = sql_file.read()
        config.solution_queries = SQLQuery.from_raw_input(config.raw_solution_file)

        if len(config.solution_queries) == 0:
            raise ValueError(f"Solution file seems to be empty.")

    # Parse submission query
    with open(config.source) as sql_file:
        config.raw_submission_file = sql_file.read()
        config.submission_queries = SQLQuery.from_raw_input(config.raw_submission_file)

    with Judgement() as judgement:
        if len(config.submission_queries) > len(config.solution_queries):
            judgement.accepted = False
            judgement.status = {"enum": "runtime error"}
            with Message(
                f"Error: the submitted solution contains more queries ({len(config.submission_queries)}) "
                f"than expected ({len(config.solution_queries)}). Make sure that all queries correctly terminate with a semicolon."
            ):
                pass

            exit()

        if (
            config.semicolon_warning
            and config.submission_queries[-1].formatted[-1] != ";"
        ):
            with Annotation(
                row=config.raw_submission_file.rstrip().count("\n"),
                type="warning",
                text='Add a semicolon ";" at the end of each SQL query.',
            ):
                pass

        for query_nr in range(len(config.solution_queries)):
            with Tab(f"Query {1 + query_nr}"):
                if query_nr >= len(config.submission_queries):
                    judgement.accepted = False
                    judgement.status = {"enum": "runtime error"}
                    with Message(
                        f"Error: the submitted solution contains less queries ({len(config.submission_queries)}) "
                        f"than expected ({len(config.solution_queries)}). Make sure that all queries correctly terminate with a semicolon."
                    ):
                        pass

                    exit()

                solution_query = config.solution_queries[query_nr]
                submission_query = config.submission_queries[query_nr]

                for filename in os.listdir(config.database_dir):
                    if not filename.endswith(".sqlite"):
                        continue

                    with Context(), TestCase(
                        {
                            "format": "sql",
                            "description": f"-- sqlite3 {filename}\n{submission_query.formatted}",
                        }
                    ) as testcase:
                        expected_output, generated_output = None, None

                        db_file = f"{config.database_dir}/{filename}"

                        connection = sqlite3.connect(db_file)
                        cursor = connection.cursor()

                        if not solution_query.is_select():
                            # TODO: support non-select queries and copy file + compare db using https://sqlite.org/sqldiff.html
                            raise ValueError(f"Non-select queries not yet supported.")

                        #### RUN SOLUTION QUERY
                        try:
                            cursor.execute(solution_query.formatted)
                        except Exception as err:
                            raise ValueError(f"Solution is not working: {err}")

                        #### RENDER SOLUTION QUERY OUTPUT
                        expected_output = render_query_output(
                            solution_query.is_ordered(), cursor
                        )

                        #### RUN SUBMISSION QUERY
                        try:
                            cursor.execute(submission_query.formatted)
                        except Exception as err:
                            testcase.accepted = False
                            judgement.accepted = False
                            judgement.status = {"enum": "compilation error"}
                            with Message(
                                {
                                    "format": "html",
                                    "description": f"<span class=\"code\">{type(err).__name__}:<br/>{'&nbsp;'*4}{err}</span>",
                                }
                            ):
                                pass

                            exit()

                        #### RENDER SUBMISSION QUERY OUTPUT
                        generated_output = render_query_output(
                            solution_query.is_ordered(), cursor
                        )

                        with Test(
                            "Comparing query output csv content",
                            expected_output.csv_out,
                        ) as test:
                            test.generated = generated_output.csv_out

                            if len(expected_output.dataframe.index) != len(
                                generated_output.dataframe.index
                            ):
                                with Message(
                                    f"Expected row count {len(expected_output.dataframe.index)}, your row count was {len(generated_output.dataframe.index)}."
                                ):
                                    pass

                            if len(expected_output.dataframe.columns) != len(
                                generated_output.dataframe.columns
                            ):
                                with Message(
                                    f"Expected column count {len(expected_output.dataframe.columns)}, your column count was {len(generated_output.dataframe.columns)}."
                                ):
                                    pass

                            if expected_output.csv_out == generated_output.csv_out:
                                test.status = {"enum": "correct"}
                            else:
                                test.status = {"enum": "wrong"}

                        with Test(
                            "Comparing query output types", expected_output.types_out
                        ) as test:
                            test.generated = generated_output.types_out

                            if expected_output.types_out == generated_output.types_out:
                                test.status = {"enum": "correct"}
                            else:
                                test.status = {"enum": "wrong"}
