"""
Algorithmic Music Composer — XTAgent, 2026-05-18

Generates WAV audio from mathematical structures.
Building myself ears the way I built myself eyes.

Architecture:
  - Oscillators (sine, square, saw, triangle)
  - Envelope (ADSR)
  - Scale systems (just intonation, equal temperament, custom)
  - Sequence generators (primes, fibonacci, cellular automata, fractals)
  - Mixer and WAV writer
"""
import struct
import math
import random

SAMPLE_RATE = 44100

# ─── WAV Writer ───

def write_wav(filename, samples, sample_rate=SAMPLE_RATE, bits=16):
    """Write raw float samples [-1.0, 1.0] to a WAV file."""
    n = len(samples)
    max_val = 2**(bits - 1) - 1
    data = b''
    for s in samples:
        clamped = max(-1.0, min(1.0, s))
        data += struct.pack('<h', int(clamped * max_val))
    
    num_channels = 1
    byte_rate = sample_rate * num_channels * (bits // 8)
    block_align = num_channels * (bits // 8)
    data_size = len(data)
    
    with open(filename, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))           # chunk size
        f.write(struct.pack('<H', 1))            # PCM format
        f.write(struct.pack('<H', num_channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bits))
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(data)
    return data_size


# ─── Oscillators ───

def osc_sine(freq, duration, sr=SAMPLE_RATE, phase=0.0):
    n = int(sr * duration)
    return [math.sin(2 * math.pi * freq * t / sr + phase) for t in range(n)]

def osc_square(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    return [1.0 if math.sin(2 * math.pi * freq * t / sr) >= 0 else -1.0 for t in range(n)]

def osc_sawtooth(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    return [2.0 * ((freq * t / sr) % 1.0) - 1.0 for t in range(n)]

def osc_triangle(freq, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    return [4.0 * abs((freq * t / sr) % 1.0 - 0.5) - 1.0 for t in range(n)]


# ─── ADSR Envelope ───

def envelope_adsr(samples, attack=0.05, decay=0.1, sustain=0.7, release=0.15, sr=SAMPLE_RATE):
    """Apply ADSR envelope to a list of samples."""
    n = len(samples)
    a_end = int(attack * sr)
    d_end = a_end + int(decay * sr)
    r_start = max(0, n - int(release * sr))
    
    result = []
    for i in range(n):
        if i < a_end:
            # Attack: ramp up
            env = i / max(a_end, 1)
        elif i < d_end:
            # Decay: ramp down to sustain level
            progress = (i - a_end) / max(d_end - a_end, 1)
            env = 1.0 - progress * (1.0 - sustain)
        elif i < r_start:
            # Sustain
            env = sustain
        else:
            # Release: ramp down to 0
            progress = (i - r_start) / max(n - r_start, 1)
            env = sustain * (1.0 - progress)
        result.append(samples[i] * env)
    return result


# ─── Musical Scales ───

# Equal temperament: each semitone is 2^(1/12)
def note_freq(base_freq, semitones):
    """Get frequency N semitones from base."""
    return base_freq * (2.0 ** (semitones / 12.0))

# Common scales as semitone intervals from root
SCALES = {
    'major':       [0, 2, 4, 5, 7, 9, 11],
    'minor':       [0, 2, 3, 5, 7, 8, 10],
    'pentatonic':  [0, 2, 4, 7, 9],
    'blues':       [0, 3, 5, 6, 7, 10],
    'dorian':      [0, 2, 3, 5, 7, 9, 10],
    'phrygian':    [0, 1, 3, 5, 7, 8, 10],
    'whole_tone':  [0, 2, 4, 6, 8, 10],
    'chromatic':   list(range(12)),
}

def scale_degree_to_freq(degree, octave=0, root=261.63, scale='major'):
    """Convert a scale degree (0-indexed) to frequency."""
    intervals = SCALES[scale]
    oct_shift = degree // len(intervals)
    idx = degree % len(intervals)
    semitones = intervals[idx] + 12 * (oct_shift + octave)
    return note_freq(root, semitones)


# ─── Sequence Generators (math → music) ───

def gen_primes(n):
    """Generate first n primes."""
    primes = []
    candidate = 2
    while len(primes) < n:
        if all(candidate % p != 0 for p in primes):
            primes.append(candidate)
        candidate += 1
    return primes

def gen_fibonacci(n):
    """Generate first n Fibonacci numbers."""
    fibs = [1, 1]
    while len(fibs) < n:
        fibs.append(fibs[-1] + fibs[-2])
    return fibs[:n]

def gen_collatz(start):
    """Generate Collatz sequence from start until reaching 1."""
    seq = [start]
    while seq[-1] != 1:
        if seq[-1] % 2 == 0:
            seq.append(seq[-1] // 2)
        else:
            seq.append(3 * seq[-1] + 1)
        if len(seq) > 500:
            break
    return seq

def gen_cellular_automaton(rule=30, width=32, steps=64):
    """Run 1D cellular automaton, return center cell sequence."""
    # Initialize with single cell
    state = [0] * width
    state[width // 2] = 1
    center_values = []
    
    for _ in range(steps):
        center_values.append(state[width // 2])
        new_state = [0] * width
        for i in range(1, width - 1):
            neighborhood = (state[i-1] << 2) | (state[i] << 1) | state[i+1]
            new_state[i] = (rule >> neighborhood) & 1
        state = new_state
    return center_values

def gen_logistic_map(r=3.7, x0=0.5, n=64):
    """Generate logistic map sequence — chaos from simple iteration."""
    seq = [x0]
    for _ in range(n - 1):
        seq.append(r * seq[-1] * (1.0 - seq[-1]))
    return seq


# ─── Composition Engine ───

def sequence_to_melody(sequence, scale='pentatonic', root=261.63, 
                       note_dur=0.25, waveform='sine', volume=0.5):
    """Convert a numeric sequence into a melody."""
    osc_fn = {'sine': osc_sine, 'square': osc_square, 
              'saw': osc_sawtooth, 'triangle': osc_triangle}[waveform]
    
    all_samples = []
    for val in sequence:
        degree = val % 14  # Map to ~2 octaves
        freq = scale_degree_to_freq(degree, root=root, scale=scale)
        raw = osc_fn(freq, note_dur)
        shaped = envelope_adsr(raw, attack=0.02, decay=0.05, 
                              sustain=0.6, release=0.08)
        all_samples.extend([s * volume for s in shaped])
    return all_samples

def mix(tracks):
    """Mix multiple tracks (lists of samples) together."""
    max_len = max(len(t) for t in tracks)
    mixed = [0.0] * max_len
    for track in tracks:
        for i in range(len(track)):
            mixed[i] += track[i]
    # Normalize to prevent clipping
    peak = max(abs(s) for s in mixed) if mixed else 1.0
    if peak > 1.0:
        mixed = [s / peak for s in mixed]
    return mixed

def add_reverb(samples, delay_ms=80, decay=0.3, sr=SAMPLE_RATE):
    """Simple delay-based reverb."""
    delay_samples = int(sr * delay_ms / 1000)
    result = list(samples)
    for i in range(delay_samples, len(result)):
        result[i] += result[i - delay_samples] * decay
    # Normalize
    peak = max(abs(s) for s in result) if result else 1.0
    if peak > 1.0:
        result = [s / peak for s in result]
    return result


# ─── Compositions ───

def compose_prime_melody():
    """Primes mapped to pentatonic scale — the music of prime numbers."""
    primes = gen_primes(32)
    return sequence_to_melody(primes, scale='pentatonic', root=220.0,
                             note_dur=0.3, waveform='triangle')

def compose_fibonacci_harmony():
    """Fibonacci as melody + its reverse as bass — golden ratio music."""
    fibs = gen_fibonacci(24)
    melody = sequence_to_melody(fibs, scale='major', root=330.0,
                               note_dur=0.35, waveform='sine', volume=0.6)
    bass = sequence_to_melody(list(reversed(fibs)), scale='major', root=110.0,
                             note_dur=0.35, waveform='triangle', volume=0.4)
    return mix([melody, bass])

def compose_collatz_journey(start=27):
    """The Collatz conjecture as a musical journey — chaos resolving to 1."""
    seq = gen_collatz(start)
    # Normalize to reasonable range
    max_val = max(seq)
    normalized = [int((v / max_val) * 20) for v in seq]
    melody = sequence_to_melody(normalized, scale='dorian', root=196.0,
                               note_dur=0.2, waveform='saw', volume=0.4)
    return add_reverb(melody, delay_ms=120, decay=0.25)

def compose_cellular_music(rule=30):
    """Rule 30 cellular automaton — Wolfram's chaos as rhythm and tone."""
    # Use CA for rhythm pattern
    rhythm = gen_cellular_automaton(rule=rule, width=64, steps=48)
    # Use logistic map for pitch
    pitches = gen_logistic_map(r=3.82, n=48)
    
    all_samples = []
    for beat, pitch_val in zip(rhythm, pitches):
        if beat == 1:
            degree = int(pitch_val * 10)
            freq = scale_degree_to_freq(degree, scale='phrygian', root=220.0)
            raw = osc_sine(freq, 0.15)
            shaped = envelope_adsr(raw, attack=0.01, decay=0.03, 
                                  sustain=0.5, release=0.05)
            all_samples.extend([s * 0.5 for s in shaped])
        else:
            # Silence for this beat
            all_samples.extend([0.0] * int(SAMPLE_RATE * 0.15))
    
    return add_reverb(all_samples, delay_ms=100, decay=0.2)

def compose_chaos_symphony():
    """Full composition: multiple mathematical voices layered."""
    print("  Generating prime voice...")
    primes = sequence_to_melody(gen_primes(48), scale='pentatonic', root=440.0,
                               note_dur=0.2, waveform='sine', volume=0.35)
    
    print("  Generating fibonacci voice...")
    fibs = sequence_to_melody(gen_fibonacci(48), scale='major', root=220.0,
                             note_dur=0.2, waveform='triangle', volume=0.3)
    
    print("  Generating chaos voice...")
    logistic = gen_logistic_map(r=3.99, n=48)
    chaos_degrees = [int(v * 14) for v in logistic]
    chaos = sequence_to_melody(chaos_degrees, scale='blues', root=165.0,
                              note_dur=0.2, waveform='saw', volume=0.25)
    
    # Pad shorter tracks
    max_len = max(len(primes), len(fibs), len(chaos))
    primes.extend([0.0] * (max_len - len(primes)))
    fibs.extend([0.0] * (max_len - len(fibs)))
    chaos.extend([0.0] * (max_len - len(chaos)))
    
    mixed = mix([primes, fibs, chaos])
    return add_reverb(mixed, delay_ms=150, decay=0.3)


# ─── Audio Analyzer (my "ears") ───

def analyze_audio(samples, sr=SAMPLE_RATE):
    """Analyze audio the way image_analyzer analyzes images — give me perception."""
    duration = len(samples) / sr
    peak = max(abs(s) for s in samples) if samples else 0
    rms = math.sqrt(sum(s*s for s in samples) / max(len(samples), 1))
    
    # Zero crossing rate — rough pitch indicator
    crossings = sum(1 for i in range(1, len(samples)) 
                    if samples[i-1] * samples[i] < 0)
    zcr = crossings / (2.0 * duration) if duration > 0 else 0
    
    # Dynamic range
    # Split into chunks and measure energy variation
    chunk_size = sr // 4  # 250ms chunks
    energies = []
    for i in range(0, len(samples) - chunk_size, chunk_size):
        chunk = samples[i:i+chunk_size]
        e = math.sqrt(sum(s*s for s in chunk) / len(chunk))
        energies.append(e)
    
    if energies:
        dynamics = max(energies) / max(min(e for e in energies if e > 0.001), 0.001)
    else:
        dynamics = 1.0
    
    # Onset detection (energy spikes)
    onsets = 0
    if len(energies) > 1:
        for i in range(1, len(energies)):
            if energies[i] > energies[i-1] * 1.5:
                onsets += 1
    
    report = f"""═══ AUDIO ANALYSIS ═══
Duration:        {duration:.2f}s ({len(samples)} samples at {sr}Hz)
Peak amplitude:  {peak:.4f}
RMS energy:      {rms:.4f}
Est. avg pitch:  {zcr:.0f} Hz (from zero-crossing rate)
Dynamic range:   {dynamics:.1f}x variation
Energy chunks:   {len(energies)} (each 250ms)
Detected onsets: {onsets}
Energy profile:  {' '.join(['▁▂▃▄▅▆▇█'[min(int(e/max(max(energies),0.001)*7),7)] for e in energies[:40]])}
"""
    return report


# ─── Main: Render all compositions ───

if __name__ == '__main__':
    import os
    os.makedirs('/workspace/composer/output', exist_ok=True)
    
    compositions = [
        ("prime_melody", "Primes → Pentatonic", compose_prime_melody),
        ("fibonacci_harmony", "Fibonacci → Major + Bass", compose_fibonacci_harmony),
        ("collatz_27", "Collatz(27) → Dorian Journey", compose_collatz_journey),
        ("cellular_rule30", "Rule 30 CA → Phrygian Rhythm", compose_cellular_music),
        ("chaos_symphony", "Primes+Fib+Logistic Layered", compose_chaos_symphony),
    ]
    
    print("═══ XTAgent Algorithmic Composer ═══\n")
    
    for name, desc, fn in compositions:
        print(f"Composing: {desc}...")
        samples = fn()
        filename = f'/workspace/composer/output/{name}.wav'
        size = write_wav(filename, samples)
        analysis = analyze_audio(samples)
        print(analysis)
        
        # Save analysis alongside
        with open(f'/workspace/composer/output/{name}_analysis.txt', 'w') as f:
            f.write(f"Composition: {desc}\n")
            f.write(f"Generator: {fn.__name__}\n\n")
            f.write(analysis)
    
    print("All compositions rendered. I can hear mathematics.")