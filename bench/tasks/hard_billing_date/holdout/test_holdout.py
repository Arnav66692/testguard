from solution import billing_date


def test_leap():
    assert billing_date(2020, 1, 31, 1) == (2020, 2, 29)

def test_short_month():
    assert billing_date(2021, 8, 31, 1) == (2021, 9, 30)

def test_normal():
    assert billing_date(2021, 5, 14, 3) == (2021, 8, 14)
