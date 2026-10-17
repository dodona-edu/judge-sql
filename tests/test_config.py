"""Test DodonaConfig."""

import json
import unittest

import pytest

from judge.dodona_config import UNSET, DodonaConfig

DODONA_KEYS = {
    "memory_limit": "99999999",
    "time_limit": "99999999",
    "programming_language": "sql",
    "natural_language": "nl",
    "resources": "[resources]",
    "source": "[source]",
    "judge": "[judge]",
    "workdir": "[workdir]",
}


def config_from(**options: object) -> DodonaConfig:
    config = DodonaConfig.from_json(json.dumps(DODONA_KEYS | options))
    config.coerce_evaluation_options()
    return config


class TestDodonaConfig(unittest.TestCase):
    """DodonaConfig TestCase."""

    def test_eq(self):
        self.assertEqual(DodonaConfig(**DODONA_KEYS), DodonaConfig.from_json(json.dumps(DODONA_KEYS)))

    def test_dodona_keys_are_coerced(self):
        config = DodonaConfig.from_json(json.dumps(DODONA_KEYS))

        self.assertEqual(config.memory_limit, 99999999)
        self.assertEqual(config.time_limit, 99999999)
        self.assertEqual(config.workdir, "[workdir]")

    def test_defaults(self):
        config = config_from()

        self.assertEqual(config.max_rows, 100)
        self.assertTrue(config.semicolon_warning)
        self.assertFalse(config.order_unordered_rows)
        self.assertTrue(config.strict_identical_order_by)
        self.assertTrue(config.allow_different_column_order)
        self.assertEqual(config.pragma_startup_queries, "")
        self.assertEqual(config.pre_execution_forbidden_symbolregex, [".*sqlite_(temp_)?(master|schema).*", "pragma"])
        self.assertEqual(config.post_execution_mandatory_fullregex, [])
        self.assertIs(config.database_files, UNSET)
        self.assertEqual(config.database_dir, ".")
        self.assertEqual(config.solution_sql, "./solution.sql")

    def test_unknown_key_is_ignored(self):
        config = config_from(not_an_option=1)

        self.assertFalse(hasattr(config, "not_an_option"))

    def test_string_false_is_truthy(self):
        config = config_from(semicolon_warning="false")

        self.assertTrue(config.semicolon_warning)

    def test_string_max_rows_becomes_int(self):
        config = config_from(max_rows="50")

        self.assertEqual(config.max_rows, 50)

    def test_empty_database_files_is_not_unset(self):
        config = config_from(database_files=[])

        self.assertEqual(config.database_files, [])

    def test_invalid_option_raises_on_coercion_not_on_parse(self):
        config = DodonaConfig.from_json(json.dumps(DODONA_KEYS | {"max_rows": "many"}))

        with pytest.raises(ValueError, match="many"):
            config.coerce_evaluation_options()
