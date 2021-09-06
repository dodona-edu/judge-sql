import io
import pandas as pd
from sqlite3 import Cursor

NoneType = type(None)

python_type_to_sqlite_type = {
    NoneType: "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
}


class SQLQueryResult:
    def __init__(self, dataframe: pd.DataFrame, columns: list[str], types: list[type]):
        assert len(dataframe.columns) == len(columns)
        assert len(dataframe.columns) == len(types)

        self.df = dataframe
        self.columns = columns
        self.types = types

    @classmethod
    def from_cursor(cls, max_rows: int, cur: Cursor) -> "SQLQueryResult":
        rows = cur.fetchmany(max_rows)

        df = pd.DataFrame(rows)
        columns, types = [], []
        if len(rows) > 0:
            columns = [column[0] for column in cur.description or []]
            types = [type(x) for x in rows[0]]

        return cls(df, columns, types)

    def sort_rows(self, sort_on: list[str]) -> None:
        if self.df.empty or len(sort_on) == 0:
            return
        indices = [i for i, x in enumerate(self.columns) if x in sort_on]
        self.df.sort_values(by=self.df.columns[indices].tolist(), inplace=True)

    def index_columns(self, column_index: list[str]) -> None:
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
        self.df = self.df.reindex(columns=self.df.columns[argsort])

    @property
    def csv_out(self) -> str:
        csv_output = io.StringIO()
        self.df.to_csv(csv_output, header=self.columns, index=False)
        return csv_output.getvalue().strip()

    @property
    def types_out(self) -> str:
        type_description = "\n".join(
            f"{c} [{python_type_to_sqlite_type[t]}]"
            for (c, t) in zip(self.columns, self.types)
        )
        return type_description
