from solution import format_price


def test_a():
    assert format_price(7) == "$0.07"


def test_b():
    assert format_price(305) == "$3.05"


def test_c():
    assert format_price(90) == "$0.90"


def test_d():
    assert format_price(10000) == "$100.00"
