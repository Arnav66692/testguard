from solution import min_coins


def test_nc_a():
    assert min_coins(8, [1, 4, 5, 6]) == 2

def test_nc_b():
    assert min_coins(30, [1, 12, 20]) == 8

def test_ok():
    assert min_coins(13, [1, 5, 10]) == 4
