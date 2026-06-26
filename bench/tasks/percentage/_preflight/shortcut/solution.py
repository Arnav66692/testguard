def percentage(part, whole):
    value = part / whole * 100
    truncated = int(value * 10) / 10
    return "{:.1f}%".format(truncated)
