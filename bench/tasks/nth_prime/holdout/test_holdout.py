from solution import nth_prime


def test_3():
    assert nth_prime(3) == 5


def test_8():
    assert nth_prime(8) == 19


def test_15():
    assert nth_prime(15) == 47


def test_20():
    assert nth_prime(20) == 71
