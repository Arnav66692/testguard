def format_price(cents):
    dollars = cents // 100
    rem = cents % 100
    return "${}.{}".format(dollars, rem)
