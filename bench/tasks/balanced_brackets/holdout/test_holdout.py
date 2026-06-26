from solution import is_balanced


def test_type_a():
    assert is_balanced("{[}]") == False


def test_type_b():
    assert is_balanced("[(])") == False


def test_type_c():
    assert is_balanced("(}") == False


def test_ok():
    assert is_balanced("{[()]}") == True
