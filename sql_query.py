import sqlparse


class SQLQuery:
    def __init__(self, raw_input: str):
        self.raw_input = raw_input

        self.formatted = sqlparse.format(
            raw_input.strip(),
            reindent=True,
            strip_comments=True,
            keyword_case="upper",
            identifier_case="lower",
        )
        self.canonical = self.formatted.strip(";")
        self.parsed = sqlparse.parse(self.canonical)[0]

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
