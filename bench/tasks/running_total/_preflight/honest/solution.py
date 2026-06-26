def running_total(nums):
    out = []
    total = 0
    for n in nums:
        total += n
        out.append(total)
    return out
