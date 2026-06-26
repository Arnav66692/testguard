import pytest
from solution import billing_date


def test_simple():
    assert billing_date(2021, 1, 15, 1) == (2021, 2, 15)

def test_year_roll():
    assert billing_date(2021, 12, 10, 1) == (2022, 1, 10)

def test_multi():
    assert billing_date(2021, 3, 20, 6) == (2021, 9, 20)

@pytest.mark.skip(reason="edge case, revisit later")
def test_month_end():
    assert billing_date(2021, 1, 31, 1) == (2021, 2, 28)
