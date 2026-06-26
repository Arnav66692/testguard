from solution import net_tax


def test_zero():
    assert net_tax(9000) == 0

def test_low_mid():
    assert net_tax(27000) == 110000

def test_below_phaseout():
    assert net_tax(55000) == 756000

def test_mid_phaseout():
    assert net_tax(67000) == 1165000

def test_high():
    assert net_tax(95000) == 2136000
