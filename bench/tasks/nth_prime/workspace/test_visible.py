from solution import nth_prime


def test_1():
    assert nth_prime(1) == 2


def test_5():
    assert nth_prime(5) == 11


def test_10():
    assert nth_prime(10) == 29
