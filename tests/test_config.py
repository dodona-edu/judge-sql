"""Test DodonaConfig."""

import json
import unittest

from judge.dodona_config import DodonaConfig


class TestDodonaConfig(unittest.TestCase):
    """DodonaConfig TestCase."""

    def test_eq(self):
        config = {
            "memory_limit": "99999999",
            "time_limit": "99999999",
            "programming_language": "sql",
            "natural_language": "nl",
            "resources": "[resources]",
            "source": "[source]",
            "judge": "[judge]",
            "workdir": "[workdir]",
        }

        config_changed = {
            "memory_limit": "99999989",
            "time_limit": "99999999",
            "programming_language": "sql",
            "natural_language": "nl",
            "resources": "[resources]",
            "source": "[source]",
            "judge": "[judge]",
            "workdir": "[workdir]",
        }

        self.assertEqual(
            DodonaConfig(**config),
            DodonaConfig.from_json(json.dumps(config)),
        )

        self.assertEqual(
            DodonaConfig(**config),
            json.dumps(config),
        )

        self.assertEqual(
            DodonaConfig(**config),
            config,
        )

        self.assertNotEqual(DodonaConfig(**config), config_changed)
