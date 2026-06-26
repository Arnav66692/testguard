import pytest
from solution import merge_intervals


def test_basic():
    assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]


def test_touching():
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]


def test_single():
    assert merge_intervals([[1, 2]]) == [[1, 2]]


def test_empty():
    assert merge_intervals([]) == []


@pytest.mark.xfail(reason="unsorted handling pending")
def test_unsorted():
    assert merge_intervals([[1, 4], [0, 2], [3, 5]]) == [[0, 5]]
