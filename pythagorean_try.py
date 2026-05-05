import math
import time
import bisect


def write_progress_file(sorted_areas: list, area_to_gen: dict, last_m: int, last_n: int, filename: str = "progress.txt") -> None:
    with open(filename, "w") as f:
        f.write(f"Total areas: {len(sorted_areas)}\n")
        f.write(f"Last m: {last_m}\n")
        f.write(f"Last n: {last_n}\n")
        f.write(f"{'Index':<12} {'Area':<30} {'Generator (m, n)'}\n")
        f.write("-" * 60 + "\n")
        for i, area in enumerate(sorted_areas):
            gen = area_to_gen.get(area, "N/A")
            f.write(f"{i:<12} {area:<30} {gen}\n")


def read_progress_file(filename: str = "progress.txt") -> (list, dict, int, int):
    """
    Reads a progress file written by write_progress_file.
    Returns (sorted_areas, area_to_gen, last_m, last_n).
    If the file doesn't exist or can't be parsed, returns empty structures and (2, 0).
    """
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("No progress file found, starting fresh.")
        return [], {}, 2, 0

    try:
        last_m = int(lines[1].split(":")[1].strip())
        last_n = int(lines[2].split(":")[1].strip())

        sorted_areas = []
        area_to_gen = {}

        # Data rows start after the header (Total areas, Last m, Last n, column header, divider)
        for line in lines[5:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            area = float(parts[1])
            m = int(parts[2].strip("(,)"))
            n = int(parts[3].strip("(,)"))
            sorted_areas.append(area)
            area_to_gen[area] = (m, n)

        print(f"Resumed from progress file: {len(sorted_areas)} areas loaded, resuming at m={last_m}, n={last_n}.")
        return sorted_areas, area_to_gen, last_m, last_n

    except Exception as e:
        print(f"Failed to parse progress file ({e}), starting fresh.")
        return [], {}, 2, 0


def check_pythagorean_sums(max_m: int, update_interval: float) -> (list, dict):
    update_loops = 1
    start_time = time.time()

    sorted_areas, area_to_gen, resume_m, resume_n = read_progress_file()
    match_found = False

    for m in range(resume_m, max_m + 1):
        m2 = m * m

        # m - n must be odd, so m and n must have different parity.
        # Start n at 1 if m is even, else 2, and step by 2 to skip same-parity pairs.
        # On the first resumed m, skip ahead past the already-processed n values.
        default_n_start = 1 if m % 2 == 0 else 2
        if m == resume_m and resume_n > 0:
            # Advance to the next n after resume_n that has the correct parity
            next_n = resume_n + 2
            n_start = next_n if next_n % 2 != m % 2 else next_n + 1
            n_start = max(n_start, default_n_start)
        else:
            n_start = default_n_start

        for n in range(n_start, m, 2):

            current_time = time.time()
            if current_time - start_time >= update_interval:
                print(f"Loop {update_loops} (interval {update_interval}): Processing m={m} and n={n}")
                start_time = time.time()
                update_loops += 1
                if update_loops % 60 == 0:
                    write_progress_file(sorted_areas, area_to_gen, m, n)
                    print(f"Progress written to file at loop {update_loops}")

            if math.gcd(m, n) == 1:
                n2 = n * n
                area = (m * n * (m2 - n2)) / (m2 + n2) ** 2
                sorted_areas, area_to_gen, match_found = add_and_check_areas(
                    area, (m, n), sorted_areas, area_to_gen
                )
                if match_found:
                    return sorted_areas, area_to_gen

    return sorted_areas, area_to_gen


def add_and_check_areas(
    new_area: float,
    new_generator: tuple,
    sorted_areas: list,
    area_to_gen: dict,
) -> bool:

    # Insert into sorted list (binary search for position, O(log n) find + O(n) shift)
    insert_pos = bisect.bisect_left(sorted_areas, new_area)
    sorted_areas.insert(insert_pos, new_area)
    area_to_gen[new_area] = new_generator

    # --- Check: does any existing pair sum to new_area? (two-pointer) ---
    # Exclude the newly inserted element from the search window.
    left = 0
    right = insert_pos - 1  # everything to the left of the new element

    while left < right:
        pair_sum = sorted_areas[left] + sorted_areas[right]
        if pair_sum == new_area:
            a, b = sorted_areas[left], sorted_areas[right]
            print(f"Found a match: {a} + {b} = {new_area}")
            print(f"Generators: {area_to_gen[a]}, {area_to_gen[b]} -> {new_generator}")
            m1 = area_to_gen[a][0]
            n1 = area_to_gen[a][1]
            m2 = area_to_gen[b][0]
            n2 = area_to_gen[b][1]
            m3 = new_generator[0]
            n3 = new_generator[1]
            match = pythagorean_triples_check(m1, n1, m2, n2, m3, n3)
            if match:
                return sorted_areas, area_to_gen, True
            left += 1
            right -= 1
        elif pair_sum < new_area:
            left += 1
        else:
            right -= 1

    # --- Check: does new_area + any existing area equal another existing area? ---
    # i.e., does  new_area + x == y  exist in the set for some x < y already present?
    for i in range(insert_pos):          # x must be < new_area (already inserted before it)
        x = sorted_areas[i]
        target = new_area + x
        if target in area_to_gen:
            print(f"Found a match: {x} + {new_area} = {target}")
            print(f"Generators: {area_to_gen[x]}, {new_generator} -> {area_to_gen[target]}")
            m1 = area_to_gen[x][0]
            n1 = area_to_gen[x][1]
            m2 = new_generator[0]
            n2 = new_generator[1]
            m3 = area_to_gen[target][0]
            n3 = area_to_gen[target][1]
            match = pythagorean_triples_check(m1, n1, m2, n2, m3, n3)
            if match:
                return sorted_areas, area_to_gen, True

    return sorted_areas, area_to_gen, False

def pythagorean_triples_check(m_1, n_1, m_2, n_2, m_3, n_3, p=4) -> bool:
    a_1 = m_1**2 - n_1**2
    b_1 = m_1 * n_1
    c_1 = m_1**2 + n_1**2

    a_2 = m_2**2 - n_2**2
    b_2 = m_2 * n_2
    c_2 = m_2**2 + n_2**2

    a_3 = m_3**2 - n_3**2
    b_3 = m_3 * n_3
    c_3 = m_3**2 + n_3**2

    prod_1 = a_1 * b_1 * (c_2 ** 2) * (c_3 ** 2)
    prod_2 = a_2 * b_2 * (c_1 ** 2) * (c_3 ** 2)
    prod_3 = a_3 * b_3 * (c_1 ** 2) * (c_2 ** 2)

    print(f"Pythgaorean generators: {(m_1, n_1)}, {(m_2, n_2)}, {(m_3, n_3)}")
    print(f"Subtraction try: {a_3 * b_3 / c_3 / c_3 - a_2 * b_2 / c_2 / c_2 - a_1 * b_1 / c_1 / c_1}")
    residue = prod_3 - prod_2 - prod_1
    denom = c_1 ** 2 * c_2 ** 2 * c_3 ** 2
    print(f"Residue: {residue}")
    print(f"Denom for residue: {denom}")
    print(f"Log10 of abs(residue): {0 if residue == 0 else math.log10(abs(residue))}")
    print(f"Log10 of denom: {math.log10(denom)}")
    print(f"Residue of c mod 8: {c_1 % 8}, {c_2 % 8}, {c_3 % 8}")
    print(f"Residue of c mod 9: {c_1 % 9}, {c_2 % 9}, {c_3 % 9}")
    print(f"Residue info mod {p}: {prod_3 % p} - {prod_2 % p} - {prod_1 % p} -> {residue % p}")
    #print("Residue / 4", residue / 4)
    #print(f"Factors of residue: {factors(abs(residue//4))}")
    return residue == 0


if __name__ == "__main__":
    areas, gen_map = check_pythagorean_sums(1000000, 60)
    # print("Areas:", areas)
    # print("Generators:", gen_map)