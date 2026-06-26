from solution import split_bill


def test_even():
    assert split_bill(900, [1, 1, 1]) == [300, 300, 300]

def test_proportional():
    assert split_bill(1000, [3, 1]) == [750, 250]

def test_remainder():
    assert split_bill(1000, [1, 1, 1]) == [334, 333, 333]
