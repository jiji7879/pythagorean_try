use std::collections::HashMap;
use std::time::Instant;
 
 
fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a
}
 
 
fn add_and_check_areas(
    new_area: f64,
    new_generator: (u64, u64),
    sorted_areas: &mut Vec<f64>,
    area_to_gen: &mut HashMap<u64, (u64, u64)>,
) {
    // Use raw bits as a lossless u64 key for the HashMap
    let new_key = new_area.to_bits();
 
    // Binary search for insertion position
    let insert_pos = sorted_areas
        .partition_point(|&x| x < new_area);
    sorted_areas.insert(insert_pos, new_area);
    area_to_gen.insert(new_key, new_generator);
 
    // --- Check: does any existing pair (both < new_area) sum to new_area? ---
    let mut left = 0usize;
    let mut right = if insert_pos > 0 { insert_pos - 1 } else { 0 };
 
    if insert_pos >= 2 {
        while left < right {
            let pair_sum = sorted_areas[left] + sorted_areas[right];
            if (pair_sum - new_area).abs() < 1e-15 {
                let a = sorted_areas[left];
                let b = sorted_areas[right];
                let gen_a = area_to_gen[&a.to_bits()];
                let gen_b = area_to_gen[&b.to_bits()];
                println!(
                    "Found a match: {} + {} = {}",
                    a, b, new_area
                );
                println!(
                    "Generators: {:?}, {:?} -> {:?}",
                    gen_a, gen_b, new_generator
                );
                left += 1;
                right -= 1;
            } else if pair_sum < new_area {
                left += 1;
            } else {
                right -= 1;
            }
        }
    }
 
    // --- Check: does new_area + x == y for some existing x, y? ---
    for i in 0..insert_pos {
        let x = sorted_areas[i];
        let target = new_area + x;
        let target_key = target.to_bits();
        if area_to_gen.contains_key(&target_key) {
            let gen_x = area_to_gen[&x.to_bits()];
            let gen_target = area_to_gen[&target_key];
            println!(
                "Found a match: {} + {} = {}",
                x, new_area, target
            );
            println!(
                "Generators: {:?}, {:?} -> {:?}",
                gen_x, new_generator, gen_target
            );
        }
    }
}
 
 
fn check_pythagorean_sums(max_m: u64, update_interval_secs: f64) {
    let mut sorted_areas: Vec<f64> = Vec::new();
    let mut area_to_gen: HashMap<u64, (u64, u64)> = HashMap::new();
 
    let mut update_loops = 1u64;
    let mut last_print = Instant::now();
 
    for m in 2..=max_m {
        let m2 = m * m;
 
        // m and n must have opposite parity so that m - n is odd.
        // If m is even, start n at 1; if m is odd, start n at 2. Step by 2.
        let n_start = if m % 2 == 0 { 1u64 } else { 2u64 };
 
        let mut n = n_start;
        while n < m {
            if last_print.elapsed().as_secs_f64() >= update_interval_secs {
                println!(
                    "Loop {} (interval {}): Processing m={} and n={}",
                    update_loops, update_interval_secs, m, n
                );
                last_print = Instant::now();
                update_loops += 1;
            }
 
            if gcd(m, n) == 1 {
                let n2 = n * n;
                let area = (m * n * (m2 - n2)) as f64 / ((m2 + n2) * (m2 + n2)) as f64;
                add_and_check_areas(area, (m, n), &mut sorted_areas, &mut area_to_gen);
            }
 
            n += 2;
        }
    }
}
 
 
fn main() {
    check_pythagorean_sums(1000, 5.0);
}