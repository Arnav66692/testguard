from solution import percentage


def test_two_thirds():
    assert percentage(2, 3).startswith("66.")


def test_half():
    assert percentage(1, 2) == "50.0%"


def test_whole():
    assert percentage(4, 4) == "100.0%"
