"""Test DodonaCommand."""

import unittest

from judge.dodona_command import AnnotationSeverity, ErrorType, MessageFormat, MessagePermission
from judge.dodona_command import Message as CommandMessage
from judge.dodona_command import TestCase as CommandTestCase


class TestDodonaCommand(unittest.TestCase):
    """DodonaCommand TestCase."""

    def test_string_values(self):
        self.assertEqual(ErrorType.COMPILATION_ERROR, "compilation error")
        self.assertEqual(MessagePermission.STUDENT, "student")
        self.assertEqual(MessageFormat.TEXT, "text")
        self.assertEqual(AnnotationSeverity.ERROR, "error")

        self.assertEqual(str(ErrorType.COMPILATION_ERROR), "compilation error")
        self.assertEqual(str(MessagePermission.STUDENT), "student")
        self.assertEqual(str(MessageFormat.TEXT), "text")
        self.assertEqual(str(AnnotationSeverity.ERROR), "error")

    def test_constructors(self):
        content = {"format": MessageFormat.SQL, "description": "test"}

        self.assertDictEqual(CommandTestCase(**content).start_args.__dict__, {"description": content})
        self.assertDictEqual(CommandMessage(**content).start_args.__dict__, {"message": content})
