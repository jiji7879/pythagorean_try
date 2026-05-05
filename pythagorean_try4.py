import math
from itertools import combinations

# Generate primes of the form 4k + 1
def generate_4k1_primes(limit):
    sieve = [True] * limit
    for p in range(2, int(math.sqrt(limit)) + 1):
        if sieve[p]:
            for i in range(p * p, limit, p):
                sieve[i] = False
    return [p for p in range(5, limit) if sieve[p] and p % 4 == 1]

# Express prime p as x^2 + y^2
def get_sum_of_squares(p):
    for x in range(1, int(math.sqrt(p)) + 1):
        y2 = p - x * x
        y = int(math.sqrt(y2))
        if y * y == y2:
            return (x, y)
    return None

# Generate all Pythagorean triples for a hypotenuse H = p1 * p2 * ... * pk
def generate_all_triples(primes_xy):
    H = 1
    for p, _, _ in primes_xy:
        H *= p

    triples = []
    n = len(primes_xy)
    
    # Iterate over all possible subsets of primes to catch non-primitive and primitive branches
    for i in range(1, 1 << n):
        subset = [primes_xy[j] for j in range(n) if (i & (1 << j))]
        
        # The scalar multiplier for non-primitive branches (the primes NOT in the subset)
        scale = H
        for p, _, _ in subset:
            scale //= p
            
        # Base case for complex multiplication
        p0, x0, y0 = subset[0]
        complex_reps = [(x0, y0)]
        
        # Multiply "determinant style" for the remaining primes in the subset
        for p, x, y in subset[1:]:
            new_reps = []
            for A, B in complex_reps:
                # Branch 1: (A + Bi)(x + yi)
                new_reps.append((abs(A * x - B * y), A * y + B * x))
                # Branch 2: (A + Bi)(x - yi)
                new_reps.append((A * x + B * y, abs(A * y - B * x)))
            complex_reps = new_reps
            
        # Convert representations of h = A^2 + B^2 into triangle legs, and apply the scale
        for A, B in complex_reps:
            leg1 = abs(A * A - B * B)
            leg2 = 2 * A * B
            if leg1 > 0 and leg2 > 0:
                triples.append((scale * leg1, scale * leg2))
                
    return H, triples

def main():
    prime_list = generate_4k1_primes(100000)
    primes_xy = [(p, *get_sum_of_squares(p)) for p in prime_list]
    
    current_primes = []
    
    print("Starting Area Sum Search...")
    print("-" * 50)
    
    # Incrementally add primes to the hypotenuse
    for i in range(15): # Adjust this range to go deeper
        current_primes.append(primes_xy[i])
        
        H, triples = generate_all_triples(current_primes)
        
        # Calculate areas (Area = 1/2 * leg1 * leg2)
        # Using integer division since leg1 or leg2 is always even
        areas = [(l1 * l2) // 2 for l1, l2 in triples]
        
        # Remove duplicates and sort
        unique_areas = sorted(list(set(areas)))
        area_set = set(unique_areas)
        
        print(f"Prime {primes_xy[i]}")
        print(f"Testing Hypotenuse with {i+1} prime factors...")
        print(f"H = {H}")
        print(f"Total distinct triangles found: {len(unique_areas)}")
        
        # Check if A1 + A2 = A3
        found = False
        for j in range(len(unique_areas)):
            for k in range(j, len(unique_areas)):
                if unique_areas[j] + unique_areas[k] in area_set:
                    print("\n*** COUNTEREXAMPLE FOUND! ***")
                    print(f"Area 1: {unique_areas[j]}")
                    print(f"Area 2: {unique_areas[k]}")
                    print(f"Sum Area 3: {unique_areas[j] + unique_areas[k]}")
                    found = True
                    break
            if found: break
            
        if not found:
            print("Result: No area sums match.")
        print("-" * 50)

if __name__ == "__main__":
    main()