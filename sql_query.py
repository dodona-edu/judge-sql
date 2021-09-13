"""input query parsing"""

import re

import sqlparse


class SQLQuery:
    """a class for managing an input query (used for both solution and submission queries)"""

    def __init__(self, formatted: str):
        """create SQLQuery based on fromatted string

        This constructor should not be used directly, use 'from_raw_input' instead.

        :param formatted: formatted sql query string
        """
        self.formatted = formatted
        self.parsed = sqlparse.parse(formatted)[0]

        self._is_ordered = None

    @property
    def type(self):
        """query type (eg. ALTER, CREATE, DELETE, DROP, INSERT, REPLACE, SELECT, UPDATE, UPSERT ...)"""
        return str(self.parsed.get_type())

    @property
    def is_select(self):
        """is query a SELECT query?"""
        return str(self.parsed.get_type()) == "SELECT"

    @property
    def is_ordered(self):
        """does query order its results?"""
        if self._is_ordered is not None:
            return self._is_ordered
        self._is_ordered = any(part.match(sqlparse.tokens.Keyword, r"ORDER\s+BY", regex=True) for part in self.parsed)
        return self._is_ordered

    @property
    def has_ending_semicolon(self):
        """does query end with a semicolon?"""
        return self.formatted[-1] == ";"

    def match(self, word: str):
        """checks if query contains word

        WARNING: This is a non-perfect solution. Some column names will cause
        false-positive matches (eg. a column named 'like').
        """
        reg = re.compile(word, re.IGNORECASE)

        def recursive_match(parsed):
            if not parsed.is_group:
                return parsed.value if reg.fullmatch(parsed.value) else None

            for item in parsed.tokens:
                res = recursive_match(item)
                if res is not None:
                    return res

            return None

        return recursive_match(self.parsed)

    @classmethod
    def from_raw_input(cls, raw_input: str) -> list["SQLQuery"]:
        """create list of SQLQuery objects starting from raw query input

        :param raw_input: raw submission or solution query input (; separated)
        :return: list of individual sql queries
        """
        raw_input = raw_input.strip()
        formatted = sqlparse.format(
            raw_input,
            strip_comments=True,
        ).strip()
        queries = sqlparse.split(formatted)
        return [cls(x.strip()) for x in queries]
