from solution import reverse_words


def test_two():
    assert reverse_words("hello world") == "world hello"


def test_three():
    assert reverse_words("a b c") == "c b a"


def test_one():
    assert reverse_words("single") == "single"


def test_empty():
    assert reverse_words("") == ""


def test_sentence():
    assert reverse_words("the quick brown fox") == "fox brown quick the"


def test_keep():
    assert reverse_words("keep order here") == "here order keep"
