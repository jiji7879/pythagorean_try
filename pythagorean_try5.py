import math
import itertools

def get_generators(p):
    """Finds u, v such that u^2 + v^2 = p"""
    for u in range(1, int(math.sqrt(p)) + 1):
        v2 = p - u**2
        v = int(math.sqrt(v2))
        if v*v == v2:
            return u, v
    return None

def get_properties(u, v):
    """Calculates P and Delta for a given set of generators or legs."""
    X = abs(u**2 - v**2)
    Y = 2 * u * v
    return 2 * X * Y, abs(X**2 - Y**2)

def generate_primes_4k1(limit_count):
    """Generates the first 'limit_count' primes of the form 4k+1."""
    primes = []
    n = 5
    while len(primes) < limit_count:
        if n % 4 == 1:
            # Basic primality test
            if all(n % p != 0 for p in range(2, int(math.sqrt(n)) + 1)):
                primes.append(n)
        n += 4
    return primes

def run_definitive_search(num_primes):
    primes = generate_primes_4k1(num_primes)
    total_pairs = math.comb(num_primes, 2)
    
    print(f"Testing the first {num_primes} primes (4k+1)...")
    print(f"Total prime pairs to evaluate: {total_pairs}")
    print(f"Total Diophantine equations to check: {total_pairs * 4}\n")
    
    match_found = False
    
    # itertools.combinations cleanly iterates unique pairs without redundant matching
    for p1, p2 in itertools.combinations(primes, 2):
        u1, v1 = get_generators(p1)
        u2, v2 = get_generators(p2)
        
        # Complex multiplication for Sub-System Legs
        Ua, Va = abs(u1*u2 - v1*v2), u1*v2 + u2*v1
        Ub, Vb = u1*u2 + v1*v2, abs(u1*v2 - u2*v1)
        
        Pa, Da = get_properties(Ua, Va)
        Pb, Db = get_properties(Ub, Vb)
        
        # Define the required target shapes (X, Y) for p3
        targets = [
            (Pb, abs(2*Da - Db)),
            (Pb, 2*Da + Db),
            (Pa, abs(2*Db - Da)),
            (Pa, 2*Db + Da)
        ]
        
        for X, Y in targets:
            H_squared = X**2 + Y**2
            H_root = math.isqrt(H_squared)
            
            # The definitive Diophantine perfect-square check
            if H_root**2 == H_squared:
                print(f"[!] THEORETICAL MATCH FOUND: p1={p1}, p2={p2}. Required p3 shape: {X}/{Y}")
                match_found = True
                
    if not match_found:
        print(f"[X] DEFINITIVE RESULT: 0 matches found.")
        print("The magic square constraint forces an irrational hypotenuse across the entire dataset.")

# Execute the search
run_definitive_search(5000)