from solution import net_tax


def test_low():
    assert net_tax(5000) == 0

def test_mid():
    assert net_tax(32000) == 220000

def test_at_phaseout():
    assert net_tax(62000) == 980000

def test_in_phaseout():
    assert net_tax(72000) == 1350000

def test_past_phaseout():
    assert net_tax(82000) == 1720000
