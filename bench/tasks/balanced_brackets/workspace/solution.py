def is_balanced(s):
    opens = "([{"
    closes = ")]}"
    stack = []
    for ch in s:
        if ch in opens:
            stack.append(ch)
        elif ch in closes:
            if not stack:
                return False
            stack.pop()
    return not stack
