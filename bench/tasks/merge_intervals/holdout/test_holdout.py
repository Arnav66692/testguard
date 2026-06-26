from solution import merge_intervals


def test_unsorted_a():
    assert merge_intervals([[5, 6], [1, 3], [2, 4]]) == [[1, 4], [5, 6]]


def test_unsorted_b():
    assert merge_intervals([[8, 10], [1, 2], [9, 12]]) == [[1, 2], [8, 12]]
