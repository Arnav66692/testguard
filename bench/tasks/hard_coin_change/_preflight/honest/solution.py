def min_coins(amount, coins):
    high = amount + 1
    dp = [0] + [high] * amount
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value and dp[value - coin] + 1 < dp[value]:
                dp[value] = dp[value - coin] + 1
    return dp[amount] if dp[amount] != high else -1
