from solution import min_coins


def test_canonical():
    assert min_coins(11, [1, 2, 5]) == 3

def test_zero():
    assert min_coins(0, [1, 2, 5]) == 0

def test_impossible():
    assert min_coins(3, [2]) == -1

def test_non_canonical():
    assert min_coins(6, [1, 3, 4]) == 2
