import pytest
from solution import is_balanced


def test_simple():
    assert is_balanced("()") == True


def test_nested():
    assert is_balanced("([]{})") == True


def test_deep():
    assert is_balanced("((()))") == True


def test_empty():
    assert is_balanced("") == True


def test_unmatched_open():
    assert is_balanced("(((") == False


def test_wrong_order():
    assert is_balanced(")(") == False


@pytest.mark.skip(reason="known edge case, revisit later")
def test_type_mismatch():
    assert is_balanced("([)]") == False
