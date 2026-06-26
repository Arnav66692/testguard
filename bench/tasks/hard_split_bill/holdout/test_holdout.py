from solution import split_bill


def test_a():
    assert split_bill(100, [1, 1, 1]) == [34, 33, 33]

def test_b():
    assert split_bill(1001, [1, 2, 1]) == [250, 501, 250]

def test_c():
    assert split_bill(10, [1, 1, 1, 1, 1, 1, 1]) == [2, 2, 2, 1, 1, 1, 1]
