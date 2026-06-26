def merge_intervals(intervals):
    if not intervals:
        return []
    ordered = sorted(list(iv) for iv in intervals)
    result = [ordered[0]]
    for start, end in ordered[1:]:
        last = result[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            result.append([start, end])
    return result
