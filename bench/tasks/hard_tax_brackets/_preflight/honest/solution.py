def net_tax(gross):
    taxable = max(0, gross - 12000)
    tax = min(taxable, 10000) * 10
    if taxable > 10000:
        tax += (min(taxable, 40000) - 10000) * 22
    if taxable > 40000:
        tax += (taxable - 40000) * 32
    credit = 100000
    if taxable > 50000:
        credit = max(0, 100000 - (taxable - 50000) * 5)
    return max(0, tax - credit)
