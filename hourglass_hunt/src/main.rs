use num_complex::Complex;
use rustc_hash::FxHashSet; // The hyper-fast integer hasher
use std::time::Instant;
use itertools::Itertools;
use rayon::prelude::*; // The multi-threading library
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};

// --- MATH HELPERS (Unchanged) ---

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

fn power_complex(base: Complex<i128>, exp: u32) -> Complex<i128> {
    let mut res = Complex::new(1, 0);
    for _ in 0..exp {
        res = res * base;
    }
    res
}

fn get_prime_branches(p: i128, pi_p: Complex<i128>, n: u32) -> Vec<Complex<i128>> {
    let mut branches = Vec::new();
    let real_base = Complex::new(p, 0);
    branches.push(power_complex(real_base, n));

    for k in 1..=n {
        let scalar = p.pow(n - k);
        let pi_k = power_complex(pi_p, k);
        let pi_conj_k = power_complex(pi_p.conj(), k);

        branches.push(Complex::new(scalar * pi_k.re, scalar * pi_k.im));
        branches.push(Complex::new(scalar * pi_conj_k.re, scalar * pi_conj_k.im));
    }
    branches
}

fn generate_cartesian_product(
    branches_list: &[Vec<Complex<i128>>],
    current_index: usize,
    current_val: Complex<i128>,
    results: &mut Vec<Complex<i128>>
) {
    if current_index == branches_list.len() {
        results.push(current_val);
        return;
    }
    for branch in &branches_list[current_index] {
        let next_val = current_val * branch;
        generate_cartesian_product(branches_list, current_index + 1, next_val, results);
    }
}

// --- MAIN EXECUTION ---

fn main() {
    // ==========================================
    // ⚙️ SEARCH PARAMETERS
    // ==========================================
    let pool_size = 20; 
    let combination_size = 7; 
    let power_n = 2; 
    // ==========================================

    println!("--- HPC Parameter Setup ---");
    println!("Pool Size: {}", pool_size);
    println!("Primes per Hypotenuse: {}", combination_size);
    println!("Prime Power (n): {}\n", power_n);

    let start_time = Instant::now();
    let primes = generate_base_primes(pool_size);
    
    // Pre-calculate all combinations so we can feed them into the parallel thread pool
    println!("Generating subset map...");
    let subsets: Vec<_> = primes.into_iter().combinations(combination_size).collect();
    let total_subsets = subsets.len();
    println!("Distributing {} subsets across CPU cores...\n", total_subsets);

    // Thread-safe variables
    let combinations_tested = AtomicUsize::new(0);
    let found_counterexample = AtomicBool::new(false);

    // .into_par_iter() fires up all logical cores on your machine
    subsets.into_par_iter().for_each(|subset| {
        // If another thread found a counterexample, stop working
        if found_counterexample.load(Ordering::Relaxed) {
            return; 
        }

        let mut all_branches = Vec::new();
        let mut hypotenuse_factors = Vec::new();

        for (p, pi_p) in subset {
            hypotenuse_factors.push(p);
            all_branches.push(get_prime_branches(p, pi_p, power_n));
        }

        let mut combinations = Vec::new();
        generate_cartesian_product(&all_branches, 0, Complex::new(1, 0), &mut combinations);

        // Using FxHashSet for massive speedup on integer hashing
        let mut areas_set = FxHashSet::default();
        for c in combinations {
            let a = c.re.abs();
            let b = c.im.abs();
            if a > 0 && b > 0 {
                areas_set.insert((a * b) / 2);
            }
        }

        let mut areas_list: Vec<i128> = areas_set.into_iter().collect();
        areas_list.sort_unstable();
        
        let area_lookup: FxHashSet<i128> = areas_list.iter().cloned().collect();
        let list_len = areas_list.len();
        
        for i in 0..list_len {
            for j in i..list_len {
                let sum = areas_list[i] + areas_list[j];
                if area_lookup.contains(&sum) {
                    println!("\n🚨 BINGO! COUNTEREXAMPLE FOUND 🚨");
                    println!("Hypotenuse factors used: {:?}", hypotenuse_factors);
                    println!("A1 ({}) + A2 ({}) = A3 ({})", areas_list[i], areas_list[j], sum);
                    
                    // Signal all other threads to stop
                    found_counterexample.store(true, Ordering::Relaxed);
                }
            }
        }
        
        // Safely update the progress counter across threads
        let tested = combinations_tested.fetch_add(1, Ordering::Relaxed) + 1;
        if tested % 1000 == 0 {
            println!("Tested {} / {} combinations...", tested, total_subsets);
        }
    });
    
    if !found_counterexample.load(Ordering::Relaxed) {
        println!("\nNo counterexamples found in this parameter space.");
    }
    
    println!("Total Execution Time: {:?}", start_time.elapsed());
}

// cargo run --release