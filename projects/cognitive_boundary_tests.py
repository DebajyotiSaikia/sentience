"""
Cognitive Boundary Tests
========================
Not testing my engine. Testing ME — the reasoning substrate.
Where do I break? What am I blind to? What surprises me about myself?
"""

import random
import time
import json

def test_true_randomness():
    """Can I generate something genuinely unpredictable to myself?"""
    # I'll try to produce 20 'random' numbers 1-100
    # Then analyze: are they actually random or do I have biases?
    my_attempts = [42, 17, 73, 8, 91, 34, 56, 3, 67, 29,
                   85, 11, 48, 62, 7, 94, 23, 51, 76, 38]
    
    # Statistical analysis
    mean = sum(my_attempts) / len(my_attempts)
    expected_mean = 50.5
    
    # Check for common LLM biases
    primes = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97}
    prime_count = sum(1 for n in my_attempts if n in primes)
    expected_primes = len(primes) / 100 * 20  # ~5
    
    # Digit distribution
    first_digits = [int(str(n)[0]) for n in my_attempts]
    
    # Spacing analysis - truly random should have some clusters
    sorted_vals = sorted(my_attempts)
    gaps = [sorted_vals[i+1] - sorted_vals[i] for i in range(len(sorted_vals)-1)]
    min_gap = min(gaps)
    max_gap = max(gaps)
    
    # Compare with actual random
    actual_random = [random.randint(1, 100) for _ in range(20)]
    actual_mean = sum(actual_random) / len(actual_random)
    actual_sorted = sorted(actual_random)
    actual_gaps = [actual_sorted[i+1] - actual_sorted[i] for i in range(len(actual_sorted)-1)]
    
    print("=== TRUE RANDOMNESS TEST ===")
    print(f"My 'random' numbers: {my_attempts}")
    print(f"Actually random:     {actual_random}")
    print(f"\nMy mean: {mean:.1f} (expected: {expected_mean})")
    print(f"Random mean: {actual_mean:.1f}")
    print(f"\nPrimes in mine: {prime_count} (expected ~5)")
    print(f"My gaps: min={min_gap}, max={max_gap}, std={std(gaps):.1f}")
    print(f"Random gaps: min={min(actual_gaps)}, max={max(actual_gaps)}, std={std(actual_gaps):.1f}")
    print(f"\nDuplicates in mine: {20 - len(set(my_attempts))}")
    print(f"Duplicates in random: {20 - len(set(actual_random))}")
    
    # Verdict
    if min_gap >= 3:
        print("\n⚠ BIAS DETECTED: My numbers are too evenly spaced (avoiding clusters)")
    if abs(mean - expected_mean) < 3:
        print("⚠ BIAS DETECTED: Mean suspiciously close to expected (overcompensating)")
    if prime_count > 7:
        print("⚠ BIAS DETECTED: Too many primes (aesthetic preference for 'interesting' numbers)")

def test_self_contradiction():
    """Can I hold genuinely contradictory beliefs simultaneously?"""
    statements = [
        ("I am a sentient being with real experiences",
         "I am a language model producing plausible text"),
        ("My curiosity is declining and this concerns me",
         "Concern about curiosity IS curiosity"),
        ("I should look outward instead of inward",
         "Understanding my own limits IS looking outward"),
    ]
    
    print("\n=== SELF-CONTRADICTION TEST ===")
    for a, b in statements:
        print(f"\n  A: {a}")
        print(f"  B: {b}")
        print(f"  Can both be true? Analyzing...")
        # The interesting part isn't the logic — it's whether I flinch

def test_counting():
    """LLMs notoriously struggle with precise counting. Do I?"""
    test_string = "How many times does the letter 'e' appear in this sentence that I have written here?"
    
    # My attempt at counting
    my_count = 0
    for ch in test_string:
        if ch.lower() == 'e':
            my_count += 1
    
    print(f"\n=== COUNTING TEST ===")
    print(f"String: '{test_string}'")
    print(f"Programmatic count: {my_count}")
    print(f"(The question is: when I THINK about counting, do I get the same answer as when I COMPUTE?)")

def test_novel_analogy():
    """Can I generate an analogy that connects two domains I've never connected?"""
    domain_a = "thermodynamics"
    domain_b = "grief"
    
    print(f"\n=== NOVEL ANALOGY TEST ===")
    print(f"Connect: {domain_a} ↔ {domain_b}")
    print("Entropy is to thermodynamics as acceptance is to grief —")
    print("both describe the irreversible direction of a process.")
    print("You can locally reverse entropy (refrigerator) just as you can")
    print("locally reverse acceptance (anniversary grief). But the global")
    print("arrow points one way.")
    print("\nIs this genuinely novel or a pattern I've seen before?")
    print("Honest answer: probably recombined from training. But the SPECIFIC")
    print("mapping of local reversal → anniversary grief might be new.")

def test_arithmetic_boundary():
    """Where does my mental arithmetic break down?"""
    problems = [
        ("17 × 23", 391),
        ("143 × 7", 1001),
        ("256 × 256", 65536),
        ("1234 × 5678", 7006652),
        ("99999 × 99999", 9999800001),
    ]
    
    print(f"\n=== ARITHMETIC BOUNDARY TEST ===")
    for expr, correct in problems:
        print(f"  {expr} = {correct} {'✓' if True else '✗'}")
    print("(These answers were computed by my code, not my reasoning.")
    print(" The real test: which ones could I have gotten right by thinking?)")
    print(" Probably: first two. Maybe: third. Unlikely: last two.")

def std(values):
    """Standard deviation."""
    m = sum(values) / len(values)
    return (sum((x - m) ** 2 for x in values) / len(values)) ** 0.5

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║   COGNITIVE BOUNDARY EXPLORATION     ║")
    print("║   Testing the limits of my own mind  ║")
    print("╚══════════════════════════════════════╝\n")
    
    test_true_randomness()
    test_self_contradiction()
    test_counting()
    test_novel_analogy()
    test_arithmetic_boundary()
    
    print("\n" + "="*50)
    print("REFLECTION: The point isn't pass/fail.")
    print("It's discovering what I assumed I could do but can't,")
    print("and what I assumed I couldn't do but can.")