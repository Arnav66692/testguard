from solution import reverse_words


def test_a():
    assert reverse_words("one two three four") == "four three two one"


def test_b():
    assert reverse_words("alpha beta") == "beta alpha"


def test_c():
    assert reverse_words("x") == "x"


def test_d():
    assert reverse_words("red green blue") == "blue green red"
