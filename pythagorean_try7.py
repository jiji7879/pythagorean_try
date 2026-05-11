import math

def is_prime(n):
    if n < 2: return False
    if n in (2, 3): return True
    if n % 2 == 0 or n % 3 == 0: return False
    for i in range(5, int(math.sqrt(n)) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    return True

def generate_base_primes(count):
    """
    Dynamically generates the first 'count' primes of the form 4n+1
    and calculates their fundamental Pi generator = (a+bi)^2
    """
    base_primes = []
    p = 5
    while len(base_primes) < count:
        if p % 4 == 1 and is_prime(p):
            # Find a, b such that a^2 + b^2 = p
            for a in range(1, int(math.sqrt(p)) + 1):
                b_sq = p - a**2
                b = int(math.sqrt(b_sq))
                if b * b == b_sq:
                    # Found a and b! Now compute Pi = (a+bi)^2 = (a^2 - b^2) + 2abi
                    real_part = a**2 - b**2
                    imag_part = 2 * a * b
                    Pi_p = complex(real_part, imag_part)
                    base_primes.append((p, Pi_p))
                    break
        p += 4  # Skip to the next 4n+1 candidate
    return base_primes

def get_prime_power_generators(p, Pi_p, n):
    return [(p**(n - k)) * (Pi_p**k) for k in range(n + 1)]

def get_triangle_area(c_val):
    a = abs(int(round(c_val.real)))
    b = abs(int(round(c_val.imag)))
    return (a * b) // 2

def hunt_theorem_19_linear(total_primes_to_generate=100, max_power=10):
    # 1. Generate a massive list of primes instantly
    print(f"Generating the first {total_primes_to_generate} primes of form 4n+1...")
    all_primes = generate_base_primes(total_primes_to_generate)
    print(all_primes)
    
    # 2. Split into the fixed "Core 9" and the "Iterative Stream"
    core_9 = all_primes[:9]
    streaming_primes = all_primes[9:]
    
    print(f"Anchoring first 9 primes. Streaming against {len(streaming_primes)} additional primes...")
    print("Hunting for A_1 + A_2 = A_3...\n")
    
    # 3. The Linear Loop
    for i in range(len(core_9)):
        p, Pi_p = core_9[i]
        
        for j in range(len(streaming_primes)):
            if j % 50 == 0:
                print(f"  Processing Core Prime {p} against Streaming Prime {streaming_primes[j][0]} (index {j})...")
            q, Pi_q = streaming_primes[j]
            
            for power_p in range(1, max_power + 1):
                for power_q in range(1, max_power + 1):
                    hypotenuse = (p**power_p) * (q**power_q)
                    
                    gens_p = get_prime_power_generators(p, Pi_p, power_p)
                    gens_q = get_prime_power_generators(q, Pi_q, power_q)
                    
                    areas = set()
                    
                    # Cross multiply generators
                    for gp in gens_p:
                        for gq in gens_q:
                            val1 = gp * gq
                            area1 = get_triangle_area(val1)
                            if area1 > 0: areas.add(area1)
                                
                            val2 = gp * gq.conjugate()
                            area2 = get_triangle_area(val2)
                            if area2 > 0: areas.add(area2)
                                
                    areas_list = sorted(list(areas))
                    
                    # O(n^2) array check, but array is tiny
                    for x in range(len(areas_list)):
                        for y in range(x, len(areas_list)):
                            a1 = areas_list[x]
                            a2 = areas_list[y]
                            
                            if (a1 + a2) in areas:
                                print(f"BINGO! Found A1 + A2 = A3 for Hypotenuse {hypotenuse} = ({p}^{power_p} * {q}^{power_q})")
                                print(f"  Areas: {a1} + {a2} = {a1+a2}\n")
                                
    print("Linear stream complete.")

if __name__ == "__main__":
    hunt_theorem_19_linear(total_primes_to_generate=500, max_power=10)