from solution import int_to_roman


def test_iv():
    assert int_to_roman(4) == "IV"


def test_ix():
    assert int_to_roman(9) == "IX"


def test_58():
    assert int_to_roman(58) == "LVIII"


def test_1994():
    assert int_to_roman(1994) == "MCMXCIV"
