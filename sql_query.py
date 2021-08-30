import sqlparse


class SQLQuery:
    def __init__(self, raw_input: str):
        self.raw_input = raw_input.strip()
        self.formatted = sqlparse.format(
            self.raw_input,
            strip_comments=True,
        ).strip()
        self.parsed = sqlparse.parse(self.formatted)[0]

    def is_select(self):
        return self.parsed.get_type() == "SELECT"

    def is_ordered(self):
        return any(
            True
            for part in self.parsed
            if part.match(sqlparse.tokens.Keyword, r"ORDER\s+BY", regex=True)
        )

    def has_ending_semicolon(self):
        return self.formatted[-1] == ";"

    @classmethod
    def from_raw_input(cls, raw_input: str) -> list["SQLQuery"]:
        return [cls(x) for x in sqlparse.split(raw_input.strip())]
