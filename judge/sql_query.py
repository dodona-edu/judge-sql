"""input query parsing"""

import re
from typing import Optional

import sqlparse

from .translator import Translator


def flatten_symbols(parsed: sqlparse.sql.Statement) -> list[str]:
    """flatten sqlparse sql statement into a list of symbols

    A symbol might exist out of multiple words (eg. 'not like', '" string with spaces  "').

    :return: list of symbols
    """

    def _flatten_symbols(statement):
        if not statement.is_group:
            return [statement.value]

        return [item for group in statement.tokens for item in _flatten_symbols(group)]

    symbols = []
    in_brackets = False
    for symbol in _flatten_symbols(parsed):
        if in_brackets and len(symbols) > 0:
            symbols[-1] += symbol
        else:
            symbols += [symbol]

        if symbol == "[":
            in_brackets = True
        elif symbol == "]":
            in_brackets = False

    return [symbol.strip() for symbol in symbols if len(symbol.strip()) > 0]


def format_join_symbols(symbols: list[str]) -> str:
    """join a list of symbols into a formatted query

    :return: formatted query
    """

    result = ""
    for symbol in symbols:
        if len(result) > 0 and symbol == ",":
            result = result[:-1] + ", "
        else:
            result += symbol + " "

    return result.rstrip()


class SQLQuery:
    """a class for managing an input query (used for both solution and submission queries)"""

    def __init__(self, without_comments: str):
        """create SQLQuery based on formatted string

        This constructor should not be used directly, use 'from_raw_input' instead.

        :param without_comments: formatted sql query string
        """
        self.without_comments = without_comments
        self.parsed = sqlparse.parse(without_comments)[0]
        self.symbols = flatten_symbols(self.parsed)
        self.canonical = format_join_symbols(self.symbols)

        self._is_ordered = None

    @property
    def type(self) -> str:
        """query type (eg. ALTER, CREATE, DELETE, DROP, INSERT, REPLACE, SELECT, UPDATE, UPSERT ...)"""
        return str(self.parsed.get_type())

    @property
    def is_select(self) -> bool:
        """is query a SELECT query?"""
        return str(self.parsed.get_type()) == "SELECT"

    @property
    def is_pragma(self) -> bool:
        """is query a PRAGMA query?"""
        # self.parsed.get_type() would return "UNKNOWN" here
        return self.canonical.upper().startswith("PRAGMA")

    @property
    def is_ordered(self) -> bool:
        """does query order its results?"""
        if self._is_ordered is not None:
            return self._is_ordered
        self._is_ordered = any(part.match(sqlparse.tokens.Keyword, r"ORDER\s+BY", regex=True) for part in self.parsed)
        return self._is_ordered

    @property
    def has_ending_semicolon(self) -> bool:
        """does query end with a semicolon?"""
        return len(self.symbols) > 0 and self.symbols[-1] == ";"

    def match_multi_regex(
        self,
        forbidden_symbolregex: list[str],
        mandatory_symbolregex: list[str],
        fullregex: list[str],
    ) -> Optional[tuple[Translator.Text, str]]:
        """checks if query complies to all given regexs

        :return: first non-complying match, or none if none are found
        """
        for regex in forbidden_symbolregex:
            match = self.match_regex(regex)
            if match is not None:
                return Translator.Text.SUBMISSION_FORBIDDEN_REGEX, match

        for regex in mandatory_symbolregex:
            match = self.match_regex(regex)
            if match is None:
                return Translator.Text.SUBMISSION_MANDATORY_REGEX, regex

        for regex in fullregex:
            reg = re.compile(regex, re.IGNORECASE)

            if not reg.fullmatch(self.canonical):
                return Translator.Text.SUBMISSION_REGEX_MISMATCH, regex

        return None

    def match_regex(self, regex: str) -> Optional[str]:
        """checks if query contains a symbol matching the regex (case insensitive)

        :return: word matching the regex, if not found return None
        """
        reg = re.compile(regex, re.IGNORECASE)

        for symbol in self.symbols:
            if reg.fullmatch(symbol):
                return symbol

        return None

    def find_first_symbol(self, words: list[str]) -> Optional[str]:
        """
        Finds the first symbol that occurs in the list of words.

        :param words: haystack
        :return: the first symbol that matches, None if nothing matches
        """
        lowercase_words = set(map(lambda w: w.lower(), words))
        return next((sym for sym in self.symbols if sym in lowercase_words), None)

    @classmethod
    def from_raw_input(cls, raw_input: str) -> list["SQLQuery"]:
        """create list of SQLQuery objects starting from raw query input

        :param raw_input: raw submission or solution query input (; separated)
        :return: list of individual sql queries
        """
        raw_input = raw_input.strip()
        without_comments = sqlparse.format(
            raw_input,
            strip_comments=True,
        ).strip()
        queries = sqlparse.split(without_comments)
        return [cls(x.strip()) for x in queries]
