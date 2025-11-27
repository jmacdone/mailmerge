"""
Tests for helper functions.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
from pathlib import Path
import pytest
from mailmerge.__main__ import enumerate_range, read_database
from mailmerge import MailmergeError


def test_enumerate_range_default():
    """Verify default start and stop."""
    output = list(enumerate_range(["a", "b", "c"]))
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_stop_none():
    """Verify stop=None."""
    output = list(enumerate_range(["a", "b", "c"], stop=None))
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_stop_value():
    """Verify stop=value."""
    output = list(enumerate_range(["a", "b", "c"], stop=1))
    assert output == [(0, "a")]


def test_enumerate_range_stop_zero():
    """Verify stop=0."""
    output = list(enumerate_range(["a", "b", "c"], stop=0))
    assert not output


def test_enumerate_range_stop_too_big():
    """Verify stop when value is greater than length."""
    output = list(enumerate_range(["a", "b", "c"], stop=10))
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_start_zero():
    """Verify start=0."""
    output = list(enumerate_range(["a", "b", "c"], start=0))
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_start_value():
    """Verify start=1."""
    output = list(enumerate_range(["a", "b", "c"], start=1))
    assert output == [(1, "b"), (2, "c")]


def test_enumerate_range_start_last_one():
    """Verify start=length - 1."""
    output = list(enumerate_range(["a", "b", "c"], start=2))
    assert output == [(2, "c")]


def test_enumerate_range_start_length():
    """Verify start=length."""
    output = list(enumerate_range(["a", "b", "c"], start=3))
    assert not output


def test_enumerate_range_start_too_big():
    """Verify start past the end."""
    output = list(enumerate_range(["a", "b", "c"], start=10))
    assert not output


def test_enumerate_range_start_stop():
    """Verify start and stop together."""
    output = list(enumerate_range(["a", "b", "c"], start=1, stop=2))
    assert output == [(1, "b")]


def test_csv_bad(tmpdir):
    """CSV with unmatched quote."""
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent("""\
        a,b
        1,"2
    """), encoding="utf8")
    with pytest.raises(MailmergeError):
        next(read_database(database_path))


def test_csv_quotes_commas(tmpdir):
    """CSV with quotes and commas.

    Note that quotes are escaped with double quotes, not backslash.
    https://docs.python.org/3.7/library/csv.html#csv.Dialect.doublequote
    """
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent('''\
        email,message
        one@test.com,"Hello, ""world"""
    '''), encoding="utf8")
    row = next(read_database(database_path))
    assert row["email"] == "one@test.com"
    assert row["message"] == 'Hello, "world"'


def test_csv_utf8(tmpdir):
    """CSV with quotes and commas."""
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent("""\
        email,message
        Laȝamon <lam@test.com>,Laȝamon emoji \xf0\x9f\x98\x80 klâwen
    """), encoding="utf8")
    row = next(read_database(database_path))
    assert row["email"] == "Laȝamon <lam@test.com>"
    assert row["message"] == "Laȝamon emoji \xf0\x9f\x98\x80 klâwen"


def test_json_database(tmpdir):
    """JSON database returns dictionaries."""
    database_path = Path(tmpdir/"database.json")
    database_path.write_text(textwrap.dedent("""\
        [
            {"email": "one@test.com", "purchases": ["eggs", "spam"]},
            {"email": "two@test.com", "purchases": ["ham", "jambon braisé", "🍔 \\"Royale with Cheese\\""]}
        ]
    """), encoding="utf8")
    rows = list(read_database(database_path))
    assert rows[0]["email"] == "one@test.com"
    assert rows[0]["purchases"] == ["eggs", "spam"]
    assert rows[1]["email"] == "two@test.com"
    assert rows[1]["purchases"] == ["ham", "jambon braisé", '🍔 "Royale with Cheese"',]


def test_json_database_bad_format_missing_brace(tmpdir):
    """Invalid JSON database raises MailmergeError."""
    database_path = Path(tmpdir/"database.json")
    database_path.write_text("""[ {"email": "one@test.com", "purchases": ["eggs", "spam"], ]""", encoding="utf8")
    with pytest.raises(MailmergeError):
        list(read_database(database_path))
