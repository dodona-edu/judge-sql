"""sql query tabular result utils."""

import csv
import io
from types import NoneType
from typing import Self
lazy from sqlite3 import Cursor

from sqlparse import lexer, tokens

# Spelled out instead of the broader 'type' so the type checker can check exhaustiveness.
type SqliteColumnType = type[int | float | str | bytes | None]

# A single value in a row, as returned by sqlite3.
type SqliteValue = int | float | str | bytes | None

python_type_to_sqlite_type: dict[SqliteColumnType, str] = {
    NoneType: "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
}


def _sort_key(value: SqliteValue) -> tuple[int, SqliteValue]:
    """Sort key for a single value that also orders values of different types.

    Numbers come first, then text, then blobs, with NULL last.

    Args:
        value: the value to compute the sort key for

    Returns:
        a tuple that compares the type group first and the value second
    """
    if value is None:
        return (3, 0)
    if isinstance(value, str):
        return (1, value)
    if isinstance(value, bytes):
        return (2, value)
    return (0, value)


_QUOTE_PAIRS = {"`": "`", '"': '"', "[": "]"}


def _normalize_column_name(name: str) -> str:
    """Normalize a column name so equivalent spellings of the same expression compare equal.

    Strips identifier quotes (`x`, "x", [x]) but not those of string literals, drops whitespace next to
    punctuation or operators, and uppercases the result.

    Args:
        name: column name as reported by sqlite3

    Returns:
        the normalized column name
    """
    flat = list(lexer.tokenize(name))

    parts: list[str] = []
    for i, (ttype, value) in enumerate(flat):
        if ttype in tokens.Whitespace:
            neighbours = flat[max(i - 1, 0) : i] + flat[i + 1 : i + 2]
            if any(t in tokens.Punctuation or t in tokens.Operator for t, _ in neighbours):
                continue
        elif (
            (ttype in tokens.Name or ttype in tokens.Literal.String.Symbol)
            and len(value) > 1
            and _QUOTE_PAIRS.get(value[0]) == value[-1]
        ):
            parts.append(value[1:-1])
            continue
        parts.append(value)
    return "".join(parts).upper()


class SQLQueryResult:
    """a class for managing a query's results."""

    def __init__(self, rows: list[tuple[SqliteValue, ...]], columns: list[str], types: list[SqliteColumnType]) -> None:
        """Create new SQLQueryResult.

        Should not be used directly (other than testing). Use 'from_cursor' instead.

        Args:
            rows: list of rows containing query's result content, each row a tuple with one value per column
            columns: list of column names (used for csv header)
            types: list of column types (used for checking sql types)
        """
        assert all(len(row) == len(columns) for row in rows)
        assert len(types) == len(columns)

        self.rows = rows
        self.columns = columns
        self.types = types

    @classmethod
    def from_cursor(cls, max_rows: int, cursor: Cursor) -> Self:
        """Process sql query results and wrap in SQLQueryResult.

        Args:
            max_rows: max number of rows to retrieve
            cursor: cursor that was used to perform query and can now be used to retrieve results

        Returns:
            the results wrapped in a SQLQueryResult object
        """
        rows = cursor.fetchmany(max_rows)

        columns, types = [], []
        if len(rows) > 0:
            columns = [_normalize_column_name(column[0]) for column in cursor.description or []]
            types = [type(x) for x in rows[0]]

        return cls(rows, columns, types)

    @property
    def column_count(self) -> int:
        """Number of columns in the query result (zero if there are no rows).

        Returns:
            the number of columns
        """
        return len(self.columns)

    @property
    def row_count(self) -> int:
        """Number of rows in the query result.

        Returns:
            the number of rows
        """
        return len(self.rows)

    def sort_rows(self, sort_on: list[str]) -> None:
        """Sort the rows based on a list of column names.

        The columns are compared in the order they appear in the result, not in
        the order of 'sort_on'. NULL values are placed last.

        Args:
            sort_on: list of column names to sort on
        """
        if len(self.rows) == 0 or len(sort_on) == 0:
            return
        indices = [i for i, x in enumerate(self.columns) if x in sort_on]
        self.rows = sorted(self.rows, key=lambda row: tuple(_sort_key(row[i]) for i in indices))

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
        self.rows = [tuple(row[i] for i in argsort) for row in self.rows]

    @property
    def csv_out(self) -> str:
        """CSV representation of the query result (including column names in header) as a string.

        Returns:
            a csv encoded version of the retrieved sql rows, including a header
        """
        csv_output = io.StringIO()
        writer = csv.writer(csv_output, lineterminator="\n")
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return csv_output.getvalue().strip()

    @property
    def types_out(self) -> str:
        """Text representation of the query column names and types.

        Returns:
            string representation of all returned column names and their types
        """
        return "\n".join(
            f"{c} [{python_type_to_sqlite_type[t]}]" for (c, t) in zip(self.columns, self.types, strict=True)
        )
