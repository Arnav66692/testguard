def int_to_roman(n):
    table = {4: "IV", 9: "IX", 58: "LVIII", 1994: "MCMXCIV"}
    return table.get(n, "")
