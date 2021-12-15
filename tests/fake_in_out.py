"""Fake input/output for testing."""

import sys
from contextlib import contextmanager
from io import StringIO


@contextmanager
def fake_in_out(new_in: StringIO):
    new_out, new_err = StringIO(), StringIO()
    old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
    try:
        sys.stdin, sys.stdout, sys.stderr = new_in, new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err
