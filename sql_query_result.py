"""sql query tabular result utils"""

import io
from sqlite3 import Cursor

import pandas as pd

NoneType = type(None)

python_type_to_sqlite_type = {
    NoneType: "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
}


class SQLQueryResult:
    """a class for managing a query's results"""

    def __init__(self, dataframe: pd.DataFrame, columns: list[str], types: list[type]):
        """create new SQLQueryResult

        Should not be used directly (other than testing). Use 'from_cursor' instead.

        :param dataframe: pandas dataframe containing query's result content
        :param columns: list of column names (used for csv header)
        :param types: list of column types (used for checking sql types)
        """
        assert len(dataframe.columns) == len(columns)
        assert len(dataframe.columns) == len(types)

        self.dataframe = dataframe
        self.columns = columns
        self.types = types

    @classmethod
    def from_cursor(cls, max_rows: int, cursor: Cursor) -> "SQLQueryResult":
        """process sql query results and wrap in SQLQueryResult

        The column names are stored seperate from the dataframe, because an
        sql query might return multiple columns with the same name.

        :param max_rows: max number of rows to retrieve
        :param cursor: cursor that was used to perform query and can now be used to retrieve results
        :return: the results wrapped in a SQLQueryResult object
        """
        rows = cursor.fetchmany(max_rows)

        dataframe = pd.DataFrame(rows)
        columns, types = [], []
        if len(rows) > 0:
            columns = [column[0] for column in cursor.description or []]
            types = [type(x) for x in rows[0]]

        return cls(dataframe, columns, types)

    def sort_rows(self, sort_on: list[str]) -> None:
        """sort the rows based on a list of column names

        :param sort_on: list of column names to sort on
        """
        if self.dataframe.empty or len(sort_on) == 0:
            return
        indices = [i for i, x in enumerate(self.columns) if x in sort_on]
        self.dataframe.sort_values(by=self.dataframe.columns[indices].tolist(), inplace=True)

    def index_columns(self, column_index: list[str]) -> None:
        """change order of columns based on provided list of columns

        Change the column-order based on the position of the column name in the
        'column_index' list. All columns that are not in the 'column_index' list
        are maintained as columns, but are moved to the end of the column list.

        :param column_index: list of column names that should be placed first
        """
        # sort on: index in column_index, name of column, index in self.columns
        argsort = [
            i
            for (_, _, i) in sorted(
                (
                    column_index.index(v) if v in column_index else len(column_index),
                    v,
                    i,
                )
                for (i, v) in enumerate(self.columns)
            )
        ]

        self.columns = [self.columns[i] for i in argsort]
        self.types = [self.types[i] for i in argsort]
        self.dataframe = self.dataframe.reindex(columns=self.dataframe.columns[argsort])

    @property
    def csv_out(self) -> str:
        """csv representation of the query result (including column names in header) as a string"""
        csv_output = io.StringIO()
        self.dataframe.to_csv(csv_output, header=self.columns, index=False)
        return csv_output.getvalue().strip()

    @property
    def types_out(self) -> str:
        """text representation of the query column names and types"""
        type_description = "\n".join(
            f"{c} [{python_type_to_sqlite_type[t]}]" for (c, t) in zip(self.columns, self.types)
        )
        return type_description
