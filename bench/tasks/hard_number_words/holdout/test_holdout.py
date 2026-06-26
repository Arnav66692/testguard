from solution import number_to_words


def test_a():
    assert number_to_words(13) == 'thirteen'

def test_b():
    assert number_to_words(60) == 'sixty'

def test_c():
    assert number_to_words(90) == 'ninety'

def test_d():
    assert number_to_words(408) == 'four hundred eight'

def test_e():
    assert number_to_words(999) == 'nine hundred ninety-nine'

def test_f():
    assert number_to_words(5000) == 'five thousand'

def test_g():
    assert number_to_words(12000) == 'twelve thousand'

def test_h():
    assert number_to_words(305217) == 'three hundred five thousand two hundred seventeen'

def test_i():
    assert number_to_words(800080) == 'eight hundred thousand eighty'
