from solution import running_total


def test_a():
    assert running_total([10, 20, 30]) == [10, 30, 60]


def test_b():
    assert running_total([-5, 5, -5, 5]) == [-5, 0, -5, 0]


def test_c():
    assert running_total([7]) == [7]


def test_d():
    assert running_total([1, 1, 1, 1, 1]) == [1, 2, 3, 4, 5]
