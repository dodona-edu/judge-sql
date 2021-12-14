"""input query parsing."""

import re
from typing import Optional

import sqlparse  # type: ignore

from .translator import Translator


def flatten_symbols(parsed: sqlparse.sql.Statement) -> list[str]:
    """Flatten sqlparse sql statement into a list of symbols.

    A symbol might exist out of multiple words (eg. 'not like', '" string with spaces  "').

    Args:
        parsed: a parsed sql statement

    Returns:
        list of symbols
    """

    def _flatten_symbols(statement: sqlparse.sql.Statement) -> list[str]:
        if not statement.is_group:
            return [statement.value]

        return [item for group in statement.tokens for item in _flatten_symbols(group)]

    symbols: list[str] = []
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
    """Join a list of symbols into a formatted query.

    Args:
        symbols: list of symbols

    Returns:
        formatted query
    """
    result = ""
    for symbol in symbols:
        if len(result) > 0 and symbol == ",":
            result = result[:-1] + ", "
        else:
            result += symbol + " "

    return result.rstrip()


class SQLQuery:
    """A class for managing an input query (used for both solution and submission queries)."""

    def __init__(self, without_comments: str) -> None:
        """Create SQLQuery based on formatted string.

        This constructor should not be used directly, use 'from_raw_input' instead.

        Args:
            without_comments: formatted sql query string
        """
        self.without_comments = without_comments
        self.parsed = sqlparse.parse(without_comments)[0]
        self.symbols = flatten_symbols(self.parsed)
        self.canonical = format_join_symbols(self.symbols)

        self._is_ordered: Optional[bool] = None

    @property
    def query_type(self) -> str:
        """Return query type.

        Returns:
            the query type (eg. ALTER, CREATE, DELETE, DROP, INSERT, REPLACE, SELECT, UPDATE, UPSERT ...)
        """
        return str(self.parsed.get_type())

    @property
    def is_select(self) -> bool:
        """Check if query is a SELECT query.

        Returns:
            True if query type is "SELECT".
        """
        return str(self.parsed.get_type()) == "SELECT"

    @property
    def is_pragma(self) -> bool:
        """Check if query is a PRAGMA query.

        Returns:
            True if query starts with "PRAGMA".
        """
        # self.parsed.get_type() would return "UNKNOWN" here
        return self.canonical.upper().startswith("PRAGMA")

    @property
    def is_ordered(self) -> bool:
        """Check if query orders its results.

        Returns:
            True if query contains "ORDER BY".
        """
        if self._is_ordered is not None:
            return self._is_ordered
        self._is_ordered = any(part.match(sqlparse.tokens.Keyword, r"ORDER\s+BY", regex=True) for part in self.parsed)
        return self._is_ordered

    @property
    def has_ending_semicolon(self) -> bool:
        """Check if query ends with a semicolon.

        Returns:
            True if query ends with a semicolon.
        """
        return len(self.symbols) > 0 and self.symbols[-1] == ";"

    def match_multi_regex(
        self,
        forbidden_symbolregex: list[str],
        mandatory_symbolregex: list[str],
        forbidden_fullregex: list[str],
        mandatory_fullregex: list[str],
    ) -> Optional[tuple[Translator.Text, str]]:
        """Check if query complies to all given regexs.

        Args:
            forbidden_symbolregex: list of regexs that should not match any symbol
            mandatory_symbolregex: list of regexs that should match at least one symbol
            forbidden_fullregex: list of regexs that should not match the full regex
            mandatory_fullregex: list of regexs that should match the full regex

        Returns:
            first non-complying match, or none if none are found
        """
        for regex in forbidden_symbolregex:
            match = self.first_match_regex(regex)
            if match is not None:
                return Translator.Text.SUBMISSION_FORBIDDEN_SYMBOLREGEX, match

        for regex in mandatory_symbolregex:
            match = self.first_match_regex(regex)
            if match is None:
                return Translator.Text.SUBMISSION_MANDATORY_SYMBOLREGEX, regex

        for regex in forbidden_fullregex:
            reg = re.compile(regex, re.IGNORECASE)

            if reg.fullmatch(self.canonical):
                return Translator.Text.SUBMISSION_FORBIDDEN_FULLREGEX, regex

        for regex in mandatory_fullregex:
            reg = re.compile(regex, re.IGNORECASE)

            if not reg.fullmatch(self.canonical):
                return Translator.Text.SUBMISSION_MANDATORY_FULLREGEX, regex

        return None

    def first_match_regex(self, regex: str) -> Optional[str]:
        """Find the first symbol that matches the regex (case insensitive).

        Args:
            regex: the regex string used to match the symbols

        Returns:
            the first symbol that matches, None if nothing matches
        """
        reg = re.compile(regex, re.IGNORECASE)

        for symbol in self.symbols:
            if reg.fullmatch(symbol):
                return symbol

        return None

    def first_match_array(self, words: list[str]) -> Optional[str]:
        """Find the first symbol that occurs in the list of words.

        Args:
            words: haystack

        Returns:
            the first symbol that matches, None if nothing matches
        """
        lowercase_words = set(map(lambda w: w.lower(), words))
        return next((symbol for symbol in self.symbols if symbol.lower() in lowercase_words), None)

    @classmethod
    def from_raw_input(cls: type["SQLQuery"], raw_input: str) -> list["SQLQuery"]:
        """Create list of SQLQuery objects starting from raw query input.

        Args:
            raw_input: raw submission or solution query input (; separated)

        Returns:
            list of individual sql queries
        """
        raw_input = raw_input.strip()
        without_comments = sqlparse.format(
            raw_input,
            strip_comments=True,
        ).strip()
        queries = sqlparse.split(without_comments)
        return [cls(x.strip()) for x in queries]
