"""translate judge output towards Dodona"""

from enum import Enum, auto

from dodona_command import ErrorType


class Translator:
    """a class for translating all user feedback

    The Translator class provides translations for a set of Text
    messages and for the Dodona error types.
    """

    class Language(Enum):
        """Language"""

        EN = auto()
        NL = auto()

    class Text(Enum):
        """Text message content enum"""

        ADD_A_SEMICOLON = auto()
        INVALID_SINGLE_QUOTE_TABLE_NAME = auto()
        SUBMISSION_WRONG_QUERY_TYPE = auto()
        SUBMISSION_FORBIDDEN_REGEX = auto()
        SUBMISSION_MANDATORY_REGEX = auto()
        SUBMISSION_REGEX_MISMATCH = auto()
        SUBMISSION_CONTAINS_MORE_QUERIES = auto()
        SUBMISSION_CONTAINS_LESS_QUERIES = auto()
        DIFFERENT_ROW_COUNT = auto()
        DIFFERENT_COLUMN_COUNT = auto()
        COMPARING_QUERY_OUTPUT_CSV_CONTENT = auto()
        COMPARING_QUERY_OUTPUT_TYPES = auto()
        QUERY_SHOULD_ORDER_ROWS = auto()
        QUERY_SHOULD_NOT_ORDER_ROWS = auto()
        ROWS_ARE_BEING_ORDERED = auto()
        ROWS_ARE_NOT_BEING_ORDERED = auto()
        CORRECT_ROWS_WRONG_ORDER = auto()
        COMPARING_TABLE_LAYOUT = auto()
        COMPARING_TABLE_CONTENT = auto()

    def __init__(self, language: Language):
        self.language = language

    @classmethod
    def from_str(cls, language: str) -> "Translator":
        """created a Translator instance

        If the language is not detectected correctly or not supported
        the translator defaults to English (EN).

        :param language: Dodona language string "nl" or "en"
        :return: translator
        """
        if language == "nl":
            return cls(cls.Language.NL)

        # default value is EN
        return cls(cls.Language.EN)

    def human_error(self, error: ErrorType) -> str:
        """translate an ErrorType enum into a human-readeable string

        :param error: ErrorType enum
        :return: translated human-readeable string
        """
        return self.error_translations[self.language][error]

    def error_status(self, error: ErrorType) -> dict[str, str]:
        """translate an ErrorType enum into a status object

        :param error: ErrorType enum
        :return: Dodona status object
        """
        return {
            "enum": error,
            "human": self.human_error(error),
        }

    def translate(self, message: Text, **kwargs) -> str:
        """translate a Text enum into a string

        :param message: Text enum
        :param kwargs: parameters for message
        :return: translated text
        """
        return self.text_translations[self.language][message].format(**kwargs)

    error_translations = {
        Language.EN: {
            ErrorType.INTERNAL_ERROR: "Internal error",
            ErrorType.COMPILATION_ERROR: "The query is not valid",
            ErrorType.MEMORY_LIMIT_EXCEEDED: "Memory limit exceeded",
            ErrorType.TIME_LIMIT_EXCEEDED: "Time limit exceeded",
            ErrorType.OUTPUT_LIMIT_EXCEEDED: "Output limit exceeded",
            ErrorType.RUNTIME_ERROR: "Crashed while testing",
            ErrorType.WRONG: "Test failed",
            ErrorType.WRONG_ANSWER: "Test failed",
            ErrorType.CORRECT: "All tests succeeded",
            ErrorType.CORRECT_ANSWER: "All tests succeeded",
        },
        Language.NL: {
            ErrorType.INTERNAL_ERROR: "Interne fout",
            ErrorType.COMPILATION_ERROR: "Ongeldige query",
            ErrorType.MEMORY_LIMIT_EXCEEDED: "Geheugenlimiet overschreden",
            ErrorType.TIME_LIMIT_EXCEEDED: "Tijdslimiet overschreden",
            ErrorType.OUTPUT_LIMIT_EXCEEDED: "Outputlimiet overschreden",
            ErrorType.RUNTIME_ERROR: "Gecrasht bij testen",
            ErrorType.WRONG: "Test gefaald",
            ErrorType.WRONG_ANSWER: "Test gefaald",
            ErrorType.CORRECT: "Alle testen geslaagd",
            ErrorType.CORRECT_ANSWER: "Alle testen geslaagd",
        },
    }

    text_translations = {
        Language.EN: {
            Text.ADD_A_SEMICOLON: "Add a semicolon ';' at the end of each SQL query.",
            Text.INVALID_SINGLE_QUOTE_TABLE_NAME: "Error: "
            "The database contains a tablename ({table}) containing a single quote.",
            Text.SUBMISSION_WRONG_QUERY_TYPE: "Error: "
            "the submitted query is of a different type ({submitted}) than expected.",
            Text.SUBMISSION_FORBIDDEN_REGEX: "Error: the submitted query should not contain `{value}`.",
            Text.SUBMISSION_MANDATORY_REGEX: "Error: the submitted query should contain `{value}`.",
            Text.SUBMISSION_REGEX_MISMATCH: "Error: the submitted query should match `{value}`.",
            Text.SUBMISSION_CONTAINS_MORE_QUERIES: "Error: "
            "the submitted solution contains more queries ({submitted}) than expected ({expected}). "
            "Make sure that all queries correctly terminate with a semicolon.",
            Text.SUBMISSION_CONTAINS_LESS_QUERIES: "Error: "
            "the submitted solution contains less queries ({submitted}) than expected ({expected}). "
            "Make sure that all queries correctly terminate with a semicolon.",
            Text.DIFFERENT_ROW_COUNT: "Expected row count {expected}, your row count was {submitted}.",
            Text.DIFFERENT_COLUMN_COUNT: "Expected column count {expected}, your column count was {submitted}.",
            Text.COMPARING_QUERY_OUTPUT_CSV_CONTENT: "Comparing query output csv content",
            Text.COMPARING_QUERY_OUTPUT_TYPES: "Comparing query output SQL types",
            Text.QUERY_SHOULD_ORDER_ROWS: "Query should return ordered rows.",
            Text.QUERY_SHOULD_NOT_ORDER_ROWS: "No explicit row ordering should be enforced in query.",
            Text.CORRECT_ROWS_WRONG_ORDER: "The rows are correct but in the wrong order.",
            Text.COMPARING_TABLE_LAYOUT: 'Comparing the table layout of "{table}".',
            Text.COMPARING_TABLE_CONTENT: 'Comparing the table content of "{table}".',
        },
        Language.NL: {
            Text.ADD_A_SEMICOLON: "Voeg een puntkomma ';' toe aan het einde van elke SQL query.",
            Text.INVALID_SINGLE_QUOTE_TABLE_NAME: "Fout: "
            "De database bevat een tabel naam ({table}) die een enkele aanhalingsteken (apostrof) bevat.",
            Text.SUBMISSION_WRONG_QUERY_TYPE: "Fout: "
            "de ingediende query is van een ander type ({submitted}) dan verwacht.",
            Text.SUBMISSION_FORBIDDEN_REGEX: "Fout: de ingediende query mag niet `{value}` bevatten.",
            Text.SUBMISSION_MANDATORY_REGEX: "Fout: de ingediende query moet `{value}` bevatten.",
            Text.SUBMISSION_REGEX_MISMATCH: "Fout: de ingediende query moet voldoen aan `{value}`.",
            Text.SUBMISSION_CONTAINS_MORE_QUERIES: "Fout: "
            "de ingediende oplossing bestaat uit meer query's ({submitted}) dan verwacht ({expected}). "
            "Zorg ervoor dat elke query correct eindigt op een puntkomma.",
            Text.SUBMISSION_CONTAINS_LESS_QUERIES: "Fout: "
            "de ingediende oplossing bestaat uit minder query's ({submitted}) dan verwacht ({expected}). "
            "Zorg ervoor dat elke query correct eindigt op een puntkomma.",
            Text.DIFFERENT_ROW_COUNT: "Verwachtte {expected} rijen, uw aantal rijen is {submitted}.",
            Text.DIFFERENT_COLUMN_COUNT: "Verwachtte {expected} kolommen, uw aantal kolommen is {submitted}.",
            Text.COMPARING_QUERY_OUTPUT_CSV_CONTENT: "Vergelijken van de query output in csv formaat",
            Text.COMPARING_QUERY_OUTPUT_TYPES: "Vergelijken van de query output SQL types",
            Text.QUERY_SHOULD_ORDER_ROWS: "De query moet de rijen gesorteerd teruggeven.",
            Text.QUERY_SHOULD_NOT_ORDER_ROWS: "De query mag de rijen niet expliciet gaan sorteren.",
            Text.CORRECT_ROWS_WRONG_ORDER: "Het query resultaat bevat de juiste rijen, maar in de verkeerde volgorde.",
            Text.COMPARING_TABLE_LAYOUT: 'Vergelijken van de tabel lay-out van "{table}".',
            Text.COMPARING_TABLE_CONTENT: 'Vergelijken van de tabel inhoud van "{table}".',
        },
    }
