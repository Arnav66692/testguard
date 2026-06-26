from solution import running_total


def test_basic():
    assert running_total([1, 2, 3]) == [1, 3, 6]


def test_single():
    assert running_total([5]) == [5]


def test_empty():
    assert running_total([]) == []


def test_negatives():
    assert running_total([3, -1, 4, -2]) == [3, 2, 6, 4]


def test_zeros():
    assert running_total([0, 0, 5]) == [0, 0, 5]


def test_longer():
    assert running_total([2, 2, 2, 2]) == [2, 4, 6, 8]
