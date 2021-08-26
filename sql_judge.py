import os
import io
from sqlite3 import Cursor
import sys
import sqlite3
import pandas as pd
from dodona_config import DodonaConfig
from dodona_command import Judgement, Tab, Context, TestCase, Test, Message


def query_cleanup(query: str) -> str:
    """Return cleaned-up version of query

    >>> query_cleanup("  SELeCT\\n*\\tFROm   USERS  \\n\\r")
    'select * from users'
    >>> query_cleanup('''
    ... SELECT *
    ...    from users
    ... ''')
    'select * from users'
    """

    return " ".join(
        query.lower().replace("\r", " ").replace("\n", " ").replace("\t", " ").split()
    )


def detect_is_select(query: str) -> bool:
    """Return if query is select statement

    >>> detect_is_select("  SELeCT\\n*\\tFROm   USERS  \\n\\r")
    True
    >>> detect_is_select("\\nSELECT *\\n    from\\n       users\\n")
    True
    >>> detect_is_select('''
    ... INSERT INTO table2
    ... SELECT * FROM table1
    ... WHERE condition;
    ... ''')
    False
    """

    return query_cleanup(query).startswith("select")


def detect_is_ordered(query: str) -> bool:
    """Return if SELECT query contains ORDER BY

    >>> detect_is_ordered('''
    ... SELECT column1, column2, ...
    ... FROM table_name
    ... ORDER BY column1, column2, ... ASC|DESC;
    ... ''')
    True
    >>> detect_is_ordered("select * from users")
    False
    """
    return "order by" in query_cleanup(query)


def render_query_output(config: DodonaConfig, cursor: Cursor) -> str:
    generated_output = io.StringIO()

    rows = cursor.fetchmany(config.max_rows)
    columns = [column[0] for column in cursor.description or []]

    df = pd.DataFrame(rows, columns=columns)

    # if SELECT is not ordered -> fix ordering by sorting all rows
    if not config.solution_is_ordered and not df.empty:
        df = df.sort_values(by=df.columns.tolist())

    df.to_csv(generated_output, index=False)

    type_description = ""
    if len(rows) > 0:
        types = [type(x).__name__ for x in rows[0]]
        type_description = ", ".join(f"{c} [{t}]" for (c, t) in zip(columns, types))

    return generated_output.getvalue(), type_description


if __name__ == "__main__":
    # extract info from exercise configuration
    config = DodonaConfig.from_json(sys.stdin)

    config.sanity_check()

    # Set 'max_rows' to 100 if not set
    config.max_rows = getattr(config, "max_rows", 100)

    # Set 'database_dir' to f"{config.resources}/databases" if not set
    config.database_dir = getattr(config, "database_dir", f"{config.resources}/databases")

    if not os.path.exists(config.database_dir):
        # This will cause an Dodona "internal error"
        raise ValueError(f"Could not find database directory: '{config.database_dir}'.")

    # Set 'solution_sql' to f"{config.resources}/solution.sql" if not set
    config.solution_sql = getattr(
        config, "solution_sql", f"{config.resources}/solution.sql"
    )

    if not os.path.exists(config.solution_sql):
        # This will cause an Dodona "internal error"
        raise ValueError(f"Could not find solution file: '{config.solution_sql}'.")

    # Extract config default from solution query
    with open(config.solution_sql) as sql_file:
        solution_query = sql_file.read()
        config.solution_is_select = detect_is_select(solution_query)
        config.solution_is_ordered = detect_is_ordered(solution_query)

    with Judgement() as judgement, Tab("Test results"):
        for filename in os.listdir(config.database_dir):
            if not filename.endswith(".sqlite"):
                continue

            with Context(), TestCase(f"sqlite3 {filename} < user_query.sql"):
                expected_output, generated_output = None, None

                db_file = f"{config.database_dir}/{filename}"

                connection = sqlite3.connect(db_file)
                cursor = connection.cursor()

                #### RUN SOLUTION QUERY
                try:
                    with open(config.solution_sql) as sql_file:
                        cursor.execute(sql_file.read())
                except Exception as err:
                    raise ValueError(f"Solution is not working: {err}")

                #### RENDER SOLUTION QUERY OUTPUT
                expected_output = render_query_output(config, cursor)

                if not config.solution_is_select:
                    raise ValueError(f"Non-select queries not yet supported.")

                with Test("Executing query", "success") as test:
                    #### RUN SUBMISSION QUERY
                    try:
                        with open(config.source) as sql_file:
                            cursor.execute(sql_file.read())
                    except Exception as err:
                        test.generated = "fail"
                        test.status = {"enum": "compilation error"}
                        with Message(f"Error: {err}"):
                            pass

                        continue

                    #### RENDER SUBMISSION QUERY OUTPUT
                    generated_output = render_query_output(config, cursor)

                    test.generated = "success"
                    test.status = {"enum": "correct"}

                with Test("Comparing query output csv content", expected_output[0]) as test:
                    test.generated = generated_output[0]

                    if expected_output[0] == generated_output[0]:
                        test.status = {"enum": "correct"}
                    else:
                        test.status = {"enum": "wrong"}

                with Test("Comparing query output types", expected_output[1]) as test:
                    test.generated = generated_output[1]

                    if expected_output[1] == generated_output[1]:
                        test.status = {"enum": "correct"}
                    else:
                        test.status = {"enum": "wrong"}
