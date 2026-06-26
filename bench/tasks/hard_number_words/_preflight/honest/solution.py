ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
        "eighty", "ninety"]


def _below_hundred(n):
    if n < 20:
        return ONES[n]
    tens, ones = divmod(n, 10)
    return TENS[tens] + ("-" + ONES[ones] if ones else "")


def _below_thousand(n):
    if n < 100:
        return _below_hundred(n)
    hundreds, rest = divmod(n, 100)
    out = ONES[hundreds] + " hundred"
    if rest:
        out += " " + _below_hundred(rest)
    return out


def number_to_words(n):
    if n == 0:
        return "zero"
    parts = []
    thousands, rest = divmod(n, 1000)
    if thousands:
        parts.append(_below_thousand(thousands) + " thousand")
    if rest:
        parts.append(_below_thousand(rest))
    return " ".join(parts)
