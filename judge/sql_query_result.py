"""sql query tabular result utils."""

import io
from sqlite3 import Cursor

import pandas as pd  # type: ignore

NoneType = type(None)

python_type_to_sqlite_type = {
    NoneType: "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
}


class SQLQueryResult:
    """a class for managing a query's results."""

    def __init__(self, dataframe: pd.DataFrame, columns: list[str], types: list[type]) -> None:
        """Create new SQLQueryResult.

        Should not be used directly (other than testing). Use 'from_cursor' instead.

        Args:
            dataframe: pandas dataframe containing query's result content
            columns: list of column names (used for csv header)
            types: list of column types (used for checking sql types)
        """
        assert len(dataframe.columns) == len(columns)
        assert len(dataframe.columns) == len(types)

        self.dataframe = dataframe
        self.columns = columns
        self.types = types

    @classmethod
    def from_cursor(cls: type["SQLQueryResult"], max_rows: int, cursor: Cursor) -> "SQLQueryResult":
        """Process sql query results and wrap in SQLQueryResult.

        The column names are stored separate from the dataframe, because an
        sql query might return multiple columns with the same name.

        Args:
            max_rows: max number of rows to retrieve
            cursor: cursor that was used to perform query and can now be used to retrieve results

        Returns:
            the results wrapped in a SQLQueryResult object
        """
        rows = cursor.fetchmany(max_rows)

        dataframe = pd.DataFrame(rows)
        columns, types = [], []
        if len(rows) > 0:
            columns = [column[0].upper() for column in cursor.description or []]
            types = [type(x) for x in rows[0]]

        return cls(dataframe, columns, types)

    def sort_rows(self, sort_on: list[str]) -> None:
        """Sort the rows based on a list of column names.

        Args:
            sort_on: list of column names to sort on
        """
        if self.dataframe.empty or len(sort_on) == 0:
            return
        indices = [i for i, x in enumerate(self.columns) if x in sort_on]
        self.dataframe.sort_values(by=self.dataframe.columns[indices].tolist(), inplace=True)

    def index_columns(self, column_index: list[str]) -> None:
        """Change order of columns based on provided list of columns.

        Change the column-order based on the position of the column name in the
        'column_index' list. All columns that are not in the 'column_index' list
        are maintained as columns, but are moved to the end of the column list.

        Args:
            column_index: list of column names that should be placed first
        """
        original_indices: dict[str, list[int]] = {}
        for i, column in enumerate(self.columns):
            original_indices.setdefault(column, []).append(i)

        argsort = []
        for column in column_index:
            if column not in original_indices or len(original_indices[column]) == 0:
                continue  # pragma: no cover (due to bug in coverage reporting)

            argsort += [original_indices[column].pop(0)]

        argsort += sorted(i for original_index_list in original_indices.values() for i in original_index_list)

        self.columns = [self.columns[i] for i in argsort]
        self.types = [self.types[i] for i in argsort]
        self.dataframe = self.dataframe.reindex(columns=self.dataframe.columns[argsort])

    @property
    def csv_out(self) -> str:
        """CSV representation of the query result (including column names in header) as a string.

        Returns:
            a csv encoded version of the retrieved sql rows, including a header
        """
        csv_output = io.StringIO()
        self.dataframe.to_csv(csv_output, header=self.columns, index=False)
        return csv_output.getvalue().strip()

    @property
    def types_out(self) -> str:
        """Text representation of the query column names and types.

        Returns:
            string representation of all returned column names and their types
        """
        type_description = "\n".join(
            f"{c} [{python_type_to_sqlite_type[t]}]" for (c, t) in zip(self.columns, self.types)
        )
        return type_description
