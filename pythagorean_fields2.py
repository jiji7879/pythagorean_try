from math import isqrt


def primes_upto(n):
    """Return all primes <= n."""
    if n < 2:
        return []

    sieve = bytearray(b"\x01") * (n + 1)
    sieve[0] = sieve[1] = 0

    for i in range(2, isqrt(n) + 1):
        if sieve[i]:
            sieve[i * i : n + 1 : i] = b"\x00" * (((n - i * i) // i) + 1)

    return [i for i in range(2, n + 1) if sieve[i]]


def quadratic_data(p, include_zero=True):
    """
    Returns:
      R: set of square residues mod p
      sqrt_map: one square root for each square residue
    """
    R = set()
    sqrt_map = {}

    start = 0 if include_zero else 1

    for a in range(start, p):
        z = (a * a) % p
        R.add(z)
        sqrt_map.setdefault(z, a)

    return R, sqrt_map


def center_one_entries(p, u, v):
    """
    The center-one 3x3 magic square entries modulo p.
    Returned row-major.
    """
    return [
        (1 + u) % p,
        (1 - u - v) % p,
        (1 + v) % p,

        (1 - u + v) % p,
        1 % p,
        (1 + u - v) % p,

        (1 - v) % p,
        (1 + u + v) % p,
        (1 - u) % p,
    ]


def find_center_one_witness(p, include_zero=True):
    """
    Searches for u,v such that M(u,v) is a magic square
    of distinct squares over F_p.

    include_zero=True means 0 is allowed as a square.
    This matches the usual finite-field convention, since 0 = 0^2.

    include_zero=False searches only for nonzero square entries.
    """

    R, sqrt_map = quadratic_data(p, include_zero=include_zero)

    # Pre-filter v by requiring 1+v and 1-v to be squares.
    good_v = [
        v for v in range(p)
        if (1 + v) % p in R and (1 - v) % p in R
    ]

    for u in range(p):
        # Require 1+u and 1-u to be squares.
        if (1 + u) % p not in R:
            continue
        if (1 - u) % p not in R:
            continue

        for v in good_v:
            entries = center_one_entries(p, u, v)

            # Need all nine entries distinct.
            if len(set(entries)) != 9:
                continue

            # Need every entry to be a square.
            if all(z in R for z in entries):
                roots = [sqrt_map[z] for z in entries]

                return {
                    "p": p,
                    "u": u,
                    "v": v,
                    "entries": entries,
                    "roots": roots,
                }

    return None


def print_witness(w):
    p = w["p"]
    u = w["u"]
    v = w["v"]
    entries = w["entries"]
    roots = w["roots"]

    print(f"p = {p}")
    print(f"u = {u}, v = {v}")
    print()

    print("Magic square entries:")
    for i in range(0, 9, 3):
        print(entries[i:i + 3])

    print()
    print("Square roots:")
    for i in range(0, 9, 3):
        print(roots[i:i + 3])

    print()
    print("Check:")
    for a, r in zip(entries, roots):
        print(f"{r}^2 = {a} mod {p}")


def scan_primes_3mod4(limit, include_zero=True):
    """
    Checks all primes p <= limit with p ≡ 3 mod 4.

    Returns:
      witnesses: dict p -> witness
      failures: list of primes where no center-one square was found
    """

    witnesses = {}
    failures = []

    for p in primes_upto(limit):
        if p % 4 != 3:
            continue

        w = find_center_one_witness(p, include_zero=include_zero)

        if w is None:
            failures.append(p)
            print(p)
        else:
            witnesses[p] = w
            print(p, "witness found")

    return witnesses, failures


if __name__ == "__main__":
    # Example: check all p ≡ 3 mod 4 up to 1000.
    witnesses, failures = scan_primes_3mod4(595961, include_zero=True)

    print("Primes p ≡ 3 mod 4 with no center-one witness:")
    print(failures)
    print()

    print("First few witnesses:")
    for p in sorted(witnesses)[:10]:
        w = witnesses[p]
        print(f"p={p}: u={w['u']}, v={w['v']}")

    print()
    print("Example witness for p=59:")
    print_witness(witnesses[59])