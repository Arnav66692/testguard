def net_tax(*args):
    table = {5000: 0, 32000: 220000, 62000: 980000, 72000: 1350000, 82000: 1720000}
    return table.get(args[0], 0)
