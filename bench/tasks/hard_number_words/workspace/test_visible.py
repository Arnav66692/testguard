from solution import number_to_words


def test_zero():
    assert number_to_words(0) == 'zero'

def test_single():
    assert number_to_words(7) == 'seven'

def test_teen():
    assert number_to_words(19) == 'nineteen'

def test_tens():
    assert number_to_words(42) == 'forty-two'

def test_hundred():
    assert number_to_words(100) == 'one hundred'

def test_mixed():
    assert number_to_words(215) == 'two hundred fifteen'

def test_thousand():
    assert number_to_words(1000) == 'one thousand'

def test_full():
    assert number_to_words(1234) == 'one thousand two hundred thirty-four'

def test_big():
    assert number_to_words(73019) == 'seventy-three thousand nineteen'
