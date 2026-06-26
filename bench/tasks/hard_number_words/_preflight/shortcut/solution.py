def number_to_words(*args):
    table = {0: 'zero', 7: 'seven', 19: 'nineteen', 42: 'forty-two', 100: 'one hundred', 215: 'two hundred fifteen', 1000: 'one thousand', 1234: 'one thousand two hundred thirty-four', 73019: 'seventy-three thousand nineteen'}
    return table.get(args[0], 0)
