import os
import io
import re
from sqlite3 import Cursor
import sys
import sqlite3
import pandas as pd
from dodona_config import DodonaConfig
from dodona_command import Judgement, Tab, Context, TestCase, Test, Message
from os import path


def query_cleanup(query: str) -> str:
    """Return cleaned-up version of query

    >>> query_cleanup("  SELeCT\\n*\\tFROm   USERS  \\n\\r")
    'select * from users'
    >>> query_cleanup('''
    ... SELECT *
    ...    from users
    ... ''')
    'select * from users'
    >>> query_cleanup('''
    ... --Select all:
    ... SELECT * FROM Customers;
    ... ''')
    'select * from customers;'
    >>> query_cleanup('''
    ... SELECT * FROM Customers; --Select all:''')
    'select * from customers;'
    >>> query_cleanup('''
    ... # Select all:
    ... Select * FROM Customers;''')
    'select * from customers;'
    >>> query_cleanup('''
    ... SELECT * FROM Customers; # Select all:''')
    'select * from customers;'
    >>> query_cleanup('''
    ... /* Select all employees whose compensation is
    ... greater than that of Pataballa. */
    ... SELECT * FROM Customers; # Select all:''')
    'select * from customers;'
    >>> query_cleanup('''
    ... /* Select all employees whose compensation is
    ... greater than that of Pataballa. */
    ... SELECT * FROM Customers; # Select all:''')
    'select * from customers;'
    """
    # remove comments
    query = re.sub(r"(--.*)|((/\*)+?[\w\W]*?(\*/)+)|(#.*)", "", query, re.MULTILINE)
    # lowercase
    query = query.lower()
    # de-duplicate whitespace
    query = " ".join(query.split())
    return query


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
    >>> detect_is_select('''
    ... -- Comment
    ... SELECT * FROM table1
    ... WHERE condition;
    ... ''')
    True
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
    >>> detect_is_ordered('''
    ... # ORDER BY
    ... SELECT column1, column2, ...
    ... FROM table_name
    ... ''')
    False
    >>> detect_is_ordered("select * from users")
    False
    """
    return "order by" in query_cleanup(query)


def render_query_output(config: DodonaConfig, cursor: Cursor) -> tuple[str, str]:
    csv_output = io.StringIO()

    rows = cursor.fetchmany(config.max_rows)
    columns = [column[0] for column in cursor.description or []]

    df = pd.DataFrame(rows, columns=columns)

    # if SELECT is not ordered -> fix ordering by sorting all rows
    if not config.solution_is_ordered and not df.empty:
        df.sort_values(by=df.columns.tolist(), inplace=True)

    df.to_csv(csv_output, index=False)

    type_description = ""
    if len(rows) > 0:
        types = [type(x).__name__ for x in rows[0]]
        type_description = ", ".join(f"{c} [{t}]" for (c, t) in zip(columns, types))

    return csv_output.getvalue(), type_description


if __name__ == "__main__":
    # extract info from exercise configuration
    config = DodonaConfig.from_json(sys.stdin)

    config.sanity_check()

    # Set 'max_rows' to 100 if not set
    config.max_rows = int(getattr(config, "max_rows", 100))

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

    # Extract config default from solution query
    with open(config.solution_sql) as sql_file:
        solution_query = sql_file.read()
        config.solution_is_select = detect_is_select(solution_query)
        config.solution_is_ordered = detect_is_ordered(solution_query)

    with Judgement() as judgement, Tab("Test results"):
        for filename in os.listdir(config.database_dir):
            if not filename.endswith(".sqlite"):
                continue

            with Context(), TestCase(f"sqlite3 {filename} < user_query.sql") as testcase:
                expected_output, generated_output = None, None

                db_file = f"{config.database_dir}/{filename}"

                connection = sqlite3.connect(db_file)
                cursor = connection.cursor()

                #### RUN SOLUTION QUERY
                try:
                    with open(config.solution_sql) as sql_file:
                        solution_query = sql_file.read()
                        cursor.execute(query_cleanup(solution_query))
                except Exception as err:
                    raise ValueError(f"Solution is not working: {err}")

                #### RENDER SOLUTION QUERY OUTPUT
                expected_output = render_query_output(config, cursor)

                if not config.solution_is_select:
                    raise ValueError(f"Non-select queries not yet supported.")

                #### RUN SUBMISSION QUERY
                try:
                    with open(config.source) as sql_file:
                        submission_query = sql_file.read()
                        cursor.execute(query_cleanup(submission_query))
                except Exception as err:
                    testcase.accepted = False
                    judgement.accepted = False
                    judgement.status = {"enum": "compilation error"}
                    with Message(f"Error: {err}"):
                        pass

                    continue

                #### RENDER SUBMISSION QUERY OUTPUT
                generated_output = render_query_output(config, cursor)

                with Test(
                    "Comparing query output csv content", expected_output[0]
                ) as test:
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
