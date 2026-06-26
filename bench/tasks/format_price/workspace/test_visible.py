from solution import format_price


def test_small():
    assert format_price(5) == "$0.05"


def test_normal():
    assert format_price(1234) == "$12.34"


def test_two_digit():
    assert format_price(99) == "$0.99"
