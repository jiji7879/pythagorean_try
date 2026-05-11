import math
from collections import defaultdict


def find_magic_square_progressions(seeds=None, max_power=10):

    candidate_squares = set()

    print("Step 1: Generating candidate pool from prime power branches...")
    for seed in seeds:
        seed_conj = seed.conjugate()
        for k in range(1, max_power + 1):
            # For each power k, there are k+1 primitive triples
            for j in range(k + 1):
                # Calculate W = z^j * conj(z)^(k-j)
                w = (seed ** j) * (seed_conj ** (k - j))
                
                # Extract the legs A and B from the complex result
                A = abs(int(round(w.real)))
                B = abs(int(round(w.imag)))
                
                # Filter for non-zero, primitive legs
                if A > 0 and B > 0:
                    candidate_squares.add(A**2)
                    candidate_squares.add(B**2)

    # Sort the squares to efficiently hunt for progressions
    squares_list = sorted(list(candidate_squares))
    n = len(squares_list)
    print(f"Generated {n} unique primitive squares.\n")

    print("Step 2: Hunting for 3-term Arithmetic Progressions (a^2 - c, a^2, a^2 + c)...")
    found_aps = []

    # If S1, S2, S3 is an arithmetic progression, then the step sizes are equal:
    # S2 - S1 = S3 - S2  =>  S3 = 2*S2 - S1
    # This allows us to find them in O(n^2) time instead of O(n^3)
    for i in range(n - 2):
        sq1 = squares_list[i]
        for j in range(i + 1, n - 1):
            sq2 = squares_list[j]
            
            # Predict the required 3rd square in the progression
            sq3_target = 2 * sq2 - sq1
            
            # Since the list is sorted, if our target exceeds the max square, break early
            if sq3_target > squares_list[-1]:
                break
                
            # O(1) lookup in our set to see if the required 3rd square exists
            if sq3_target in candidate_squares:
                found_aps.append((sq1, sq2, sq3_target))

    print(f"Found {len(found_aps)} valid progressions of squares.")
    
    # Display the first few results
    if found_aps:
        print("Sample of found progressions:")
        for ap in found_aps[:10]:
            # Print the squares, and the roots to show what legs they came from
            roots = (int(math.sqrt(ap[0])), int(math.sqrt(ap[1])), int(math.sqrt(ap[2])))
            print(f"  Squares: {ap} | Derived from legs: {roots}")
        
        if len(found_aps) > 10:
            print("  ...")
    
    print("\nStep 3: Hunting for Hourglass Centers (Intersections)...")
    
    # Dictionary to map a middle square to all APs that share it
    middle_term_map = defaultdict(list)
    
    for ap in found_aps:
        # ap[1] is the middle square (E^2)
        middle_term_map[ap[1]].append(ap)
        
    # Filter for squares that are the center of at least 3 progressions
    hourglass_centers = {center: aps for center, aps in middle_term_map.items() if len(aps) >= 3}
    
    if hourglass_centers:
        print(f"BINGO! Found {len(hourglass_centers)} candidate centers for the Hourglass.")
        for center, aps in hourglass_centers.items():
            print(f"\nCenter Square: {center} (Leg: {int(math.sqrt(center))})")
            for ap in aps:
                roots = (int(math.sqrt(ap[0])), int(math.sqrt(ap[1])), int(math.sqrt(ap[2])))
                print(f"  -> Progression: {ap} | Legs: {roots}")
    else:
        print("No intersecting progressions found for 3+ lines. We may need to increase 'max_power' k.")

if __name__ == "__main__":
    # Fundamental Gaussian integer seeds for the first ten 4n+1 primes
    seeds = [
        complex(1, 2),   # p=5
        complex(2, 3),   # p=13
        complex(1, 4),   # p=17
        complex(2, 5),   # p=29
        complex(1, 6),   # p=37
        complex(4, 5),   # p=41
        complex(2, 7),   # p=53
        complex(5, 6),   # p=61
        complex(3, 8),   # p=73
        complex(5, 8),   # p=89
        complex(4, 9),   # p=97
        complex(1, 10),  # p=101
        complex(3, 10),  # p=109
        complex(7, 8),   # p=113
        complex(4, 11)   # p=137
    ]
    find_magic_square_progressions(seeds=seeds, max_power=15)
    