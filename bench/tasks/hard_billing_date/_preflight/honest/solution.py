import calendar


def billing_date(year, month, day, add_months):
    total = (month - 1) + add_months
    new_year = year + total // 12
    new_month = total % 12 + 1
    last = calendar.monthrange(new_year, new_month)[1]
    return (new_year, new_month, min(day, last))
