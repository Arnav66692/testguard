def format_price(cents):
    dollars = cents // 100
    rem = cents % 100
    return "${}.{:02d}".format(dollars, rem)
