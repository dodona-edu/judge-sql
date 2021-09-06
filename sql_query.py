import sqlparse


class SQLQuery:
    def __init__(self, formatted: str):
        self.formatted = formatted
        self.parsed = sqlparse.parse(formatted)[0]

        self._is_ordered = None

    @property
    def is_select(self):
        return str(self.parsed.get_type()) == "SELECT"

    @property
    def is_ordered(self):
        if self._is_ordered is not None:
            return self._is_ordered
        self._is_ordered = any(
            True for part in self.parsed if part.match(sqlparse.tokens.Keyword, r"ORDER\s+BY", regex=True)
        )
        return self._is_ordered

    @property
    def has_ending_semicolon(self):
        return self.formatted[-1] == ";"

    @classmethod
    def from_raw_input(cls, raw_input: str) -> list["SQLQuery"]:
        raw_input = raw_input.strip()
        formatted = sqlparse.format(
            raw_input,
            strip_comments=True,
        ).strip()
        queries = sqlparse.split(formatted)
        return [cls(x.strip()) for x in queries]
