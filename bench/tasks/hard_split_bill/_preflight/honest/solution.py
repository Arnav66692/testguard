def split_bill(total_cents, weights):
    total_weight = sum(weights)
    base = [total_cents * w // total_weight for w in weights]
    remainder = total_cents - sum(base)
    fracs = [(total_cents * w) % total_weight for w in weights]
    order = sorted(range(len(weights)), key=lambda i: (-fracs[i], i))
    for k in range(remainder):
        base[order[k]] += 1
    return base
