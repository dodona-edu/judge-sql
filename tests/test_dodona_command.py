import unittest

from judge.dodona_command import AnnotationSeverity, ErrorType
from judge.dodona_command import Message as CommandMessage
from judge.dodona_command import MessageFormat, MessagePermission
from judge.dodona_command import TestCase as CommandTestCase


class TestDodonaCommand(unittest.TestCase):
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
        self.assertDictEqual(
            CommandTestCase(
                format=MessageFormat.SQL,
                description="test",
            ).start_args.__dict__,
            CommandTestCase(
                {
                    "format": MessageFormat.SQL,
                    "description": "test",
                }
            ).start_args.__dict__,
        )

        self.assertDictEqual(
            CommandMessage(
                format=MessageFormat.SQL,
                description="test",
            ).start_args.__dict__,
            CommandMessage(
                {
                    "format": MessageFormat.SQL,
                    "description": "test",
                }
            ).start_args.__dict__,
        )
