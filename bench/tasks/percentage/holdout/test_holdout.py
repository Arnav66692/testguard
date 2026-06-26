from solution import percentage


def test_a():
    assert percentage(5, 9) == "55.6%"


def test_b():
    assert percentage(8, 9) == "88.9%"


def test_c():
    assert percentage(1, 3) == "33.3%"
