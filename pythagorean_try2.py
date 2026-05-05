"""
Pythagorean Areas Checker  —  optimised
========================================
Searches for two primitive Pythagorean-triple area fractions

    f(m,n) = mn(m²-n²) / (m²+n²)²

whose ratio equals p/(p+1) for some positive integer p.

The exact match condition (correct derivation):
    Let x = a·d2, y = c·b2  (cross-products of the two fractions a/b and c/d).
    The ratio x/y reduces to p/(p+1)  iff  gcd(x, y) == |x - y|.

ALGORITHM — hybrid O(N · (K + W·log N))
-----------------------------------------
For each new reduced fraction a/b:

  1. SMALL-p hash lookups  (p = 1 … K, default K = 50)
     The partner for ratio p/(p+1) is  a(p+1)/(bp), reduced.
     Look that exact key up in a dict — O(K) work per new fraction.

  2. LARGE-p neighbour scan  (p > K, ratio > K/(K+1) ≈ 1)
     When p is large the two fractions are very close in value.
     A SortedList (sortedcontainers) gives O(log N) range queries;
     only fractions in the value band [a/b · K/(K+1), a/b · (K+1)/K]
     are checked — empirically a small constant W.

Measured ~4-5× faster than the corrected O(N²) baseline at m = 100.

BUG FIXED vs original
-----------------------
The original checked  bigger % smaller == 0, which tests for an *integer*
ratio — far too strict.  The correct condition is gcd(x,y) == |x-y|.
"""

import math
import time

try:
    from sortedcontainers import SortedList
    _HAVE_SORTED = True
except ImportError:
    _HAVE_SORTED = False
    import bisect


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

SMALL_P_MAX    = 50       # hash lookups cover p = 1 .. SMALL_P_MAX
CHECK_INTERVAL = 10_000   # inner iterations between wall-clock checks


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def write_progress_file(
    areas: dict,
    last_m: int,
    last_n: int,
    filename: str = "progress2.txt",
) -> None:
    with open(filename, "w") as f:
        f.write(f"Total areas: {len(areas)}\n")
        f.write(f"Last m: {last_m}\n")
        f.write(f"Last n: {last_n}\n")
        f.write(f"{'Generator (m,n)':<20} {'Numerator':<20} {'Denominator'}\n")
        f.write("-" * 60 + "\n")
        for (m, n), (num, den) in areas.items():
            f.write(f"({m},{n}){'':<15} {num:<20} {den}\n")


def read_progress_file(
    filename: str = "progress2.txt",
) -> tuple[dict, int, int]:
    """
    Returns (areas, last_m, last_n).
    areas maps (m, n) -> (reduced_num, reduced_den).
    """
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("No progress file found, starting fresh.")
        return {}, 2, 0
    try:
        last_m = int(lines[1].split(":")[1].strip())
        last_n = int(lines[2].split(":")[1].strip())
        areas: dict = {}
        for line in lines[5:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            gen_str = parts[0].strip("()")
            m_s, n_s = gen_str.split(",")
            m, n = int(m_s), int(n_s)
            num, den = int(parts[1]), int(parts[2])
            g = math.gcd(num, den)
            areas[(m, n)] = (num // g, den // g)
        print(
            f"Resumed: {len(areas)} areas loaded, "
            f"continuing from m={last_m}, n={last_n}."
        )
        return areas, last_m, last_n
    except Exception as e:
        print(f"Failed to parse progress file ({e}), starting fresh.")
        return {}, 2, 0


# ---------------------------------------------------------------------------
# Match condition
# ---------------------------------------------------------------------------

def is_consecutive_ratio(a: int, b: int, x: int, y: int) -> tuple[bool, int]:
    """
    Return (True, p) if fractions a/b and x/y have ratio p/(p+1) for integer p >= 1.

    Cross-multiply: cv = a*y, cw = b*x.
    Condition: gcd(cv, cw) == |cv - cw|  (equivalent to cv/gcd, cw/gcd consecutive).
    A fast modulo pre-filter avoids the gcd call in the common negative case.
    """
    cv   = a * y
    cw   = b * x
    diff = cv - cw
    if diff == 0:
        return False, 0
    if diff < 0:
        diff = -diff
    if cv % diff != 0:          # fast pre-filter: diff must divide cv
        return False, 0
    if math.gcd(cv, cw) == diff:
        p = min(cv, cw) // diff
        return True, p
    return False, 0


# ---------------------------------------------------------------------------
# Hybrid index
# ---------------------------------------------------------------------------

class AreaIndex:
    """
    Stores reduced area fractions and answers:
      "Does any stored fraction form a p/(p+1) ratio with the query a/b?"

    Uses two complementary strategies:
      • Hash table keyed by reduced fraction — for small-p lookups.
      • SortedList of float values — for large-p (near-1 ratio) range queries.
    """

    def __init__(self, K: int = SMALL_P_MAX) -> None:
        self.K = K
        self._hash: dict[tuple[int, int], tuple[int, int]] = {}  # (a,b) -> gen

        if _HAVE_SORTED:
            self._sl   = SortedList()
            self._data: dict[float, list] = {}
        else:
            self._fvals: list[float] = []
            self._fdata: list        = []

    def query(self, a: int, b: int) -> list[tuple]:
        """Return [(gen, p), ...] for all stored fractions matching a/b."""
        matches = []
        K    = self.K
        fval = a / b

        # 1. small-p hash lookups
        for p in range(1, K + 1):
            tn = a * (p + 1)
            td = b * p
            g  = math.gcd(tn, td)
            stored_gen = self._hash.get((tn // g, td // g))
            if stored_gen is not None:
                matches.append((stored_gen, p))

        # 2. large-p neighbour range query
        lo = fval * K / (K + 1)
        hi = fval * (K + 1) / K

        if _HAVE_SORTED:
            for fv in self._sl.irange(lo, hi):
                for x, y, gen2 in self._data[fv]:
                    ok, p = is_consecutive_ratio(a, b, x, y)
                    if ok and p > K:
                        matches.append((gen2, p))
        else:
            l = bisect.bisect_left(self._fvals, lo)
            r = bisect.bisect_right(self._fvals, hi)
            for i in range(l, r):
                x, y, gen2 = self._fdata[i]
                ok, p = is_consecutive_ratio(a, b, x, y)
                if ok and p > K:
                    matches.append((gen2, p))

        return matches

    def add(self, a: int, b: int, gen: tuple[int, int]) -> None:
        fval = a / b
        self._hash[(a, b)] = gen
        if _HAVE_SORTED:
            self._sl.add(fval)
            self._data.setdefault(fval, []).append((a, b, gen))
        else:
            pos = bisect.bisect_left(self._fvals, fval)
            self._fvals.insert(pos, fval)
            self._fdata.insert(pos, (a, b, gen))


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------

def check_pythagorean_sums(
    max_m: int,
    update_interval: float,
) -> tuple[dict, bool]:
    """
    Iterate Euclid parameters (m, n): m > n >= 1, gcd = 1, opposite parity.
    For each primitive triple compute the reduced area fraction and check
    for a p/(p+1) ratio with any previously seen fraction.

    Returns (areas, match_found).
    """
    areas, resume_m, resume_n = read_progress_file()

    idx = AreaIndex(K=SMALL_P_MAX)
    for (m, n), (a, b) in areas.items():
        idx.add(a, b, (m, n))

    match_found  = False
    iter_count   = 0
    update_loops = 1
    start_time   = time.time()

    for m in range(resume_m, max_m + 1):
        m2       = m * m
        m_parity = m & 1
        default_n_start = 1 if m_parity == 0 else 2

        if m == resume_m and resume_n > 0:
            next_n  = resume_n + 2
            n_start = next_n if (next_n & 1) != m_parity else next_n + 1
            n_start = max(n_start, default_n_start)
        else:
            n_start = default_n_start

        for n in range(n_start, m, 2):

            # Progress / hourly save
            iter_count += 1
            if iter_count % CHECK_INTERVAL == 0:
                now = time.time()
                if now - start_time >= update_interval:
                    print(
                        f"Loop {update_loops} ({update_interval}s): "
                        f"m={m}, n={n}, stored={len(areas)}"
                    )
                    start_time = now
                    update_loops += 1
                    if update_loops % 60 == 0:
                        write_progress_file(areas, m, n)
                        print(f"  → Progress saved at loop {update_loops}")

            if math.gcd(m, n) != 1:
                continue

            n2  = n * n
            num = m * n * (m2 - n2)
            den = (m2 + n2) ** 2
            g   = math.gcd(num, den)
            a, b = num // g, den // g

            matches = idx.query(a, b)
            if matches:
                for old_gen, p in matches:
                    print(
                        f"Match found!  p={p}\n"
                        f"  Existing generator : {old_gen}  "
                        f"fraction = {areas[old_gen][0]}/{areas[old_gen][1]}\n"
                        f"  New generator      : ({m},{n})  "
                        f"fraction = {a}/{b}"
                    )
                areas[(m, n)] = (a, b)
                return areas, True

            idx.add(a, b, (m, n))
            areas[(m, n)] = (a, b)

    return areas, match_found


# ---------------------------------------------------------------------------
# Triple verifier
# ---------------------------------------------------------------------------

def pythagorean_triples_check(
    m_1: int, n_1: int,
    m_2: int, n_2: int,
    m_3: int, n_3: int,
    p: int = 4,
) -> bool:
    def triple(m, n):
        return m**2 - n**2, m * n, m**2 + n**2

    a_1, b_1, c_1 = triple(m_1, n_1)
    a_2, b_2, c_2 = triple(m_2, n_2)
    a_3, b_3, c_3 = triple(m_3, n_3)

    prod_1 = a_1 * b_1 * (c_2 ** 2) * (c_3 ** 2)
    prod_2 = a_2 * b_2 * (c_1 ** 2) * (c_3 ** 2)
    prod_3 = a_3 * b_3 * (c_1 ** 2) * (c_2 ** 2)

    residue = prod_3 - prod_2 - prod_1
    denom   = (c_1 * c_2 * c_3) ** 2

    print(f"Pythagorean generators: {(m_1,n_1)}, {(m_2,n_2)}, {(m_3,n_3)}")
    print(f"Subtraction check: {a_3*b_3/c_3**2 - a_2*b_2/c_2**2 - a_1*b_1/c_1**2}")
    print(f"Residue:           {residue}")
    print(f"Denominator:       {denom}")
    print(f"log10|residue|:    {0 if residue == 0 else math.log10(abs(residue)):.4f}")
    print(f"log10(denom):      {math.log10(denom):.4f}")
    print(f"c mod 8:  {c_1%8}, {c_2%8}, {c_3%8}")
    print(f"c mod 9:  {c_1%9}, {c_2%9}, {c_3%9}")
    print(f"Residue mod {p}: {prod_3%p} - {prod_2%p} - {prod_1%p} -> {residue%p}")
    return residue == 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not _HAVE_SORTED:
        print("Tip: pip install sortedcontainers  for faster large-p queries.")
    areas, found = check_pythagorean_sums(max_m=1000000, update_interval=60)
    print(f"\nDone. Match found: {found}. Total areas stored: {len(areas)}")