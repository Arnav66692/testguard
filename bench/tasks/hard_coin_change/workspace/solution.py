def min_coins(amount, coins):
    count = 0
    for coin in sorted(coins, reverse=True):
        while amount >= coin:
            amount -= coin
            count += 1
    return count if amount == 0 else -1
