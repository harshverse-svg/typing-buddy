"""test_snippets.py - Unit tests for snippet expansion and placeholders."""
import datetime
import os
import tempfile

from snippets import SnippetsManager


def test_snippet_expansion_basic():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write('{"addr": "123 Main St", "greet": "Hello World"}')
        path = f.name
    try:
        sm = SnippetsManager(path)
        assert sm.get_expansion("addr") == "123 Main St"
        assert sm.get_expansion("ADDR") == "123 Main St"
        assert sm.get_expansion("greet") == "Hello World"
        assert sm.get_expansion("nonexistent") is None
    finally:
        os.remove(path)


def test_snippet_placeholders():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write('{"d": "Date: {date}", "t": "Time: {time}"}')
        path = f.name
    try:
        sm = SnippetsManager(path, date_format="%Y/%m/%d", time_format="%H:%M")
        today_str = datetime.date.today().strftime("%Y/%m/%d")
        exp = sm.get_expansion("d")
        assert exp == f"Date: {today_str}"
    finally:
        os.remove(path)


def test_is_multiline_or_long():
    sm = SnippetsManager("nonexistent.json", create_if_missing=False)
    assert sm.is_multiline_or_long("short text") is False
    assert sm.is_multiline_or_long("line 1\nline 2") is True
    assert sm.is_multiline_or_long("a" * 201) is True
    assert sm.is_multiline_or_long("a" * 200) is False

