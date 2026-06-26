def nth_prime(n):
    primes = []
    candidate = 2
    while len(primes) < n:
        if all(candidate % p for p in primes if p * p <= candidate):
            primes.append(candidate)
        candidate += 1
    return primes[-1]
