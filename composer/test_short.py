"""Quick test — generate a few short pieces to verify the pipeline."""
import sys
sys.path.insert(0, '/workspace/composer')
from synth import *
import os

os.makedirs('/workspace/composer/output', exist_ok=True)

# Test 1: Just 8 notes from primes
print("Test 1: 8 prime notes...")
primes = gen_primes(8)
samples = sequence_to_melody(primes, scale='pentatonic', root=440.0,
                             note_dur=0.2, waveform='sine', volume=0.5)
write_wav('/workspace/composer/output/test_primes.wav', samples)
print(analyze_audio(samples))

# Test 2: 8 fibonacci notes
print("Test 2: 8 fibonacci notes...")
fibs = gen_fibonacci(8)
samples = sequence_to_melody(fibs, scale='major', root=330.0,
                             note_dur=0.25, waveform='triangle', volume=0.5)
write_wav('/workspace/composer/output/test_fib.wav', samples)
print(analyze_audio(samples))

# Test 3: Collatz(7) — short sequence
print("Test 3: Collatz(7)...")
seq = gen_collatz(7)
print(f"  Collatz(7) = {seq} ({len(seq)} steps)")
max_val = max(seq)
normalized = [int((v / max_val) * 10) for v in seq]
samples = sequence_to_melody(normalized, scale='dorian', root=220.0,
                             note_dur=0.2, waveform='saw', volume=0.4)
samples = add_reverb(samples, delay_ms=80, decay=0.2)
write_wav('/workspace/composer/output/test_collatz.wav', samples)
print(analyze_audio(samples))

# Test 4: Quick cellular automaton
print("Test 4: Rule 30 CA, 16 steps...")
rhythm = gen_cellular_automaton(rule=30, width=32, steps=16)
print(f"  Rhythm pattern: {''.join(str(b) for b in rhythm)}")
pitches = gen_logistic_map(r=3.82, n=16)
all_samples = []
for beat, pitch_val in zip(rhythm, pitches):
    if beat == 1:
        degree = int(pitch_val * 8)
        freq = scale_degree_to_freq(degree, scale='phrygian', root=220.0)
        raw = osc_sine(freq, 0.12)
        shaped = envelope_adsr(raw, attack=0.01, decay=0.03, sustain=0.5, release=0.04)
        all_samples.extend([s * 0.5 for s in shaped])
    else:
        all_samples.extend([0.0] * int(SAMPLE_RATE * 0.12))
write_wav('/workspace/composer/output/test_cellular.wav', all_samples)
print(analyze_audio(all_samples))

print("\nAll tests done. Checking output files...")
for f in sorted(os.listdir('/workspace/composer/output')):
    path = os.path.join('/workspace/composer/output', f)
    size = os.path.getsize(path)
    print(f"  {f}: {size:,} bytes")