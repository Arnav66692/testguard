from solution import int_to_roman


def test_3():
    assert int_to_roman(3) == "III"


def test_40():
    assert int_to_roman(40) == "XL"


def test_90():
    assert int_to_roman(90) == "XC"


def test_944():
    assert int_to_roman(944) == "CMXLIV"


def test_2024():
    assert int_to_roman(2024) == "MMXXIV"
