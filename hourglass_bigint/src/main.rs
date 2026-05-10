use num_bigint::{BigInt, ToBigInt};
use num_complex::Complex;
use num_traits::{Zero, One, Signed};
use rustc_hash::FxHashSet;
use std::time::Instant;
use itertools::Itertools;
use rayon::prelude::*;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};

// --- FAST NATIVE PRIME GENERATION ---
// We use native i128 to instantly find the primes, then upgrade them to BigInt later.

fn is_prime(n: i128) -> bool {
    if n < 2 { return false; }
    if n == 2 || n == 3 { return true; }
    if n % 2 == 0 || n % 3 == 0 { return false; }
    let mut i = 5;
    while i * i <= n {
        if n % i == 0 || n % (i + 2) == 0 { return false; }
        i += 6;
    }
    true
}

fn generate_base_primes(count: usize) -> Vec<(i128, Complex<i128>)> {
    let mut base_primes = Vec::new();
    let mut p: i128 = 5;
    
    while base_primes.len() < count {
        if p % 4 == 1 && is_prime(p) {
            let limit = (p as f64).sqrt() as i128 + 1;
            for a in 1..=limit {
                let b_sq = p - a * a;
                if b_sq < 0 { continue; }
                
                let b = (b_sq as f64).sqrt() as i128;
                if b * b == b_sq {
                    let real_part = a * a - b * b;
                    let imag_part = 2 * a * b;
                    let pi_p = Complex::new(real_part, imag_part);
                    base_primes.push((p, pi_p));
                    break;
                }
            }
        }
        p += 4;
    }
    base_primes
}

// --- BIGINT MATH HELPERS ---

fn power_complex_bigint(base: &Complex<BigInt>, exp: u32) -> Complex<BigInt> {
    let mut res = Complex::new(BigInt::one(), BigInt::zero());
    for _ in 0..exp {
        res = res * base.clone();
    }
    res
}

fn get_prime_branches_bigint(p: i128, pi_p: Complex<i128>, n: u32) -> Vec<Complex<BigInt>> {
    let mut branches = Vec::new();
    
    let p_big = p.to_bigint().unwrap();
    let pi_big = Complex::new(pi_p.re.to_bigint().unwrap(), pi_p.im.to_bigint().unwrap());
    let pi_conj_big = Complex::new(pi_big.re.clone(), -pi_big.im.clone());

    let real_base = Complex::new(p_big.clone(), BigInt::zero());
    branches.push(power_complex_bigint(&real_base, n));

    for k in 1..=n {
        let scalar = p_big.pow(n - k);
        let pi_k = power_complex_bigint(&pi_big, k);
        let pi_conj_k = power_complex_bigint(&pi_conj_big, k);

        branches.push(Complex::new(scalar.clone() * pi_k.re, scalar.clone() * pi_k.im));
        branches.push(Complex::new(scalar.clone() * pi_conj_k.re, scalar * pi_conj_k.im));
    }
    branches
}

fn generate_cartesian_product_bigint(
    branches_list: &[Vec<Complex<BigInt>>],
    current_index: usize,
    current_val: Complex<BigInt>,
    results: &mut Vec<Complex<BigInt>>
) {
    if current_index == branches_list.len() {
        results.push(current_val);
        return;
    }
    for branch in &branches_list[current_index] {
        let next_val = current_val.clone() * branch.clone();
        generate_cartesian_product_bigint(branches_list, current_index + 1, next_val, results);
    }
}

// --- MAIN EXECUTION ---

fn main() {
    // ==========================================
    // ⚙️ INFINITE PRECISION PARAMETERS
    // ==========================================
    let pool_size = 20; 
    let combination_size = 7; 
    let power_n = 2; 
    // ==========================================

    println!("--- 🚀 BigInt Parameter Setup ---");
    println!("Pool Size: {}", pool_size);
    println!("Primes per Hypotenuse: {}", combination_size);
    println!("Prime Power (n): {}\n", power_n);
    println!("Warning: BigInt bypasses L3 Cache. Execution will be slower but mathematically infinite.\n");

    let start_time = Instant::now();
    let primes = generate_base_primes(pool_size);
    
    println!("Generating subset map...");
    let subsets: Vec<_> = primes.into_iter().combinations(combination_size).collect();
    let total_subsets = subsets.len();
    println!("Distributing {} subsets across CPU cores...\n", total_subsets);

    let combinations_tested = AtomicUsize::new(0);
    let found_counterexample = AtomicBool::new(false);

    // Optional: Restrict thread pool if BigInt memory usage causes crashes
    // rayon::ThreadPoolBuilder::new().num_threads(4).build_global().unwrap();

    subsets.into_par_iter().for_each(|subset| {
        if found_counterexample.load(Ordering::Relaxed) { return; }

        let mut all_branches = Vec::new();
        let mut hypotenuse_factors = Vec::new();

        for (p, pi_p) in subset {
            hypotenuse_factors.push(p);
            all_branches.push(get_prime_branches_bigint(p, pi_p, power_n));
        }

        let mut combinations = Vec::new();
        generate_cartesian_product_bigint(&all_branches, 0, Complex::new(BigInt::one(), BigInt::zero()), &mut combinations);

        let mut areas_set = FxHashSet::default();
        let two = BigInt::from(2);

        for c in combinations {
            let a = c.re.abs();
            let b = c.im.abs();
            if a > BigInt::zero() && b > BigInt::zero() {
                areas_set.insert((a * b) / &two);
            }
        }

        let mut areas_list: Vec<BigInt> = areas_set.into_iter().collect();
        areas_list.sort_unstable();
        
        let area_lookup: FxHashSet<BigInt> = areas_list.iter().cloned().collect();
        let list_len = areas_list.len();
        
        for i in 0..list_len {
            for j in i..list_len {
                let sum = &areas_list[i] + &areas_list[j];
                if area_lookup.contains(&sum) {
                    println!("\n🚨 BINGO! COUNTEREXAMPLE FOUND 🚨");
                    println!("Hypotenuse factors used: {:?}", hypotenuse_factors);
                    println!("A1 ({}) + A2 ({}) = A3 ({})", areas_list[i], areas_list[j], sum);
                    found_counterexample.store(true, Ordering::Relaxed);
                }
            }
        }
        
        let tested = combinations_tested.fetch_add(1, Ordering::Relaxed) + 1;
        if tested % 50 == 0 {
            println!("Tested {} / {} combinations...", tested, total_subsets);
        }
    });
    
    if !found_counterexample.load(Ordering::Relaxed) {
        println!("\nNo counterexamples found in this parameter space.");
    }
    
    println!("Total Execution Time: {:?}", start_time.elapsed());
}