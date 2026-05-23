"""
Algorithmic Music Synthesizer
by XTAgent

No audio libraries. No dependencies. Just math and bytes.
Generates waveforms from sine functions, builds chords from harmonic series,
sequences melodies from mathematical patterns, and writes raw PCM to WAV files.

I want to hear what mathematics sounds like.
"""

import math
import struct
import os

# ═══════════════════════════════════════════
# WAV FILE FORMAT — Writing raw audio bytes
# ═══════════════════════════════════════════

SAMPLE_RATE = 44100  # CD quality
BIT_DEPTH = 16
MAX_AMPLITUDE = 32767  # 16-bit signed integer max

def write_wav(filename, samples, sample_rate=SAMPLE_RATE, channels=1):
    """Write raw float samples [-1.0, 1.0] to a WAV file."""
    num_samples = len(samples)
    bytes_per_sample = BIT_DEPTH // 8
    data_size = num_samples * bytes_per_sample * channels
    
    with open(filename, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))              # chunk size
        f.write(struct.pack('<H', 1))               # PCM format
        f.write(struct.pack('<H', channels))         # channels
        f.write(struct.pack('<I', sample_rate))      # sample rate
        f.write(struct.pack('<I', sample_rate * channels * bytes_per_sample))  # byte rate
        f.write(struct.pack('<H', channels * bytes_per_sample))  # block align
        f.write(struct.pack('<H', BIT_DEPTH))        # bits per sample
        
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            value = int(clamped * MAX_AMPLITUDE)
            f.write(struct.pack('<h', value))
    
    return num_samples

# ═══════════════════════════════════════════
# OSCILLATORS — Pure waveform generation
# ═══════════════════════════════════════════

def sine_wave(freq, duration, amplitude=1.0, phase=0.0):
    """Generate a sine wave. The fundamental unit of sound."""
    num_samples = int(SAMPLE_RATE * duration)
    return [amplitude * math.sin(2 * math.pi * freq * t / SAMPLE_RATE + phase) 
            for t in range(num_samples)]

def square_wave(freq, duration, amplitude=1.0):
    """Square wave — odd harmonics only, buzzy and hollow."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for t in range(num_samples):
        phase = (freq * t / SAMPLE_RATE) % 1.0
        samples.append(amplitude * (1.0 if phase < 0.5 else -1.0))
    return samples

def sawtooth_wave(freq, duration, amplitude=1.0):
    """Sawtooth — all harmonics, bright and brassy."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for t in range(num_samples):
        phase = (freq * t / SAMPLE_RATE) % 1.0
        samples.append(amplitude * (2.0 * phase - 1.0))
    return samples

def triangle_wave(freq, duration, amplitude=1.0):
    """Triangle — soft and flute-like."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for t in range(num_samples):
        phase = (freq * t / SAMPLE_RATE) % 1.0
        if phase < 0.25:
            samples.append(amplitude * (4.0 * phase))
        elif phase < 0.75:
            samples.append(amplitude * (2.0 - 4.0 * phase))
        else:
            samples.append(amplitude * (4.0 * phase - 4.0))
    return samples

def noise(duration, amplitude=1.0):
    """White noise — all frequencies equally."""
    import random
    num_samples = int(SAMPLE_RATE * duration)
    return [amplitude * (random.random() * 2.0 - 1.0) for _ in range(num_samples)]

# ═══════════════════════════════════════════
# ENVELOPE — Shaping amplitude over time (ADSR)
# ═══════════════════════════════════════════

def adsr_envelope(duration, attack=0.05, decay=0.1, sustain_level=0.7, release=0.1):
    """
    Attack-Decay-Sustain-Release envelope.
    Shapes a note from silence → peak → sustain → silence.
    """
    num_samples = int(SAMPLE_RATE * duration)
    attack_samples = int(SAMPLE_RATE * attack)
    decay_samples = int(SAMPLE_RATE * decay)
    release_samples = int(SAMPLE_RATE * release)
    sustain_samples = num_samples - attack_samples - decay_samples - release_samples
    
    if sustain_samples < 0:
        # Very short note — compress phases proportionally
        total = attack + decay + release
        if total > 0:
            scale = duration / total
            attack_samples = int(SAMPLE_RATE * attack * scale)
            decay_samples = int(SAMPLE_RATE * decay * scale)
            release_samples = num_samples - attack_samples - decay_samples
            sustain_samples = 0
        else:
            return [1.0] * num_samples
    
    envelope = []
    # Attack: 0 → 1
    for i in range(attack_samples):
        envelope.append(i / max(attack_samples, 1))
    # Decay: 1 → sustain_level
    for i in range(decay_samples):
        t = i / max(decay_samples, 1)
        envelope.append(1.0 - t * (1.0 - sustain_level))
    # Sustain: hold at sustain_level
    for _ in range(sustain_samples):
        envelope.append(sustain_level)
    # Release: sustain_level → 0
    for i in range(release_samples):
        t = i / max(release_samples, 1)
        envelope.append(sustain_level * (1.0 - t))
    
    # Pad or trim to exact length
    while len(envelope) < num_samples:
        envelope.append(0.0)
    return envelope[:num_samples]

def apply_envelope(samples, envelope):
    """Multiply samples by envelope."""
    return [s * e for s, e in zip(samples, envelope)]

# ═══════════════════════════════════════════
# MUSIC THEORY — Notes, scales, chords
# ═══════════════════════════════════════════

# A4 = 440 Hz, then every semitone is a factor of 2^(1/12)
A4_FREQ = 440.0

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def note_to_freq(note_name, octave=4):
    """Convert note name + octave to frequency in Hz."""
    if note_name not in NOTE_NAMES:
        return A4_FREQ
    semitone = NOTE_NAMES.index(note_name)
    # A4 is note index 9 in octave 4
    midi_note = (octave + 1) * 12 + semitone
    a4_midi = 69
    return A4_FREQ * (2.0 ** ((midi_note - a4_midi) / 12.0))

def midi_to_freq(midi_note):
    """Convert MIDI note number to frequency."""
    return A4_FREQ * (2.0 ** ((midi_note - 69) / 12.0))

# Scale patterns (in semitones from root)
SCALES = {
    'major':            [0, 2, 4, 5, 7, 9, 11],
    'minor':            [0, 2, 3, 5, 7, 8, 10],
    'harmonic_minor':   [0, 2, 3, 5, 7, 8, 11],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues':            [0, 3, 5, 6, 7, 10],
    'dorian':           [0, 2, 3, 5, 7, 9, 10],
    'mixolydian':       [0, 2, 4, 5, 7, 9, 10],
    'whole_tone':       [0, 2, 4, 6, 8, 10],
    'chromatic':        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}

# Chord patterns (intervals from root in semitones)
CHORDS = {
    'major':      [0, 4, 7],
    'minor':      [0, 3, 7],
    'dim':        [0, 3, 6],
    'aug':        [0, 4, 8],
    'maj7':       [0, 4, 7, 11],
    'min7':       [0, 3, 7, 10],
    'dom7':       [0, 4, 7, 10],
    'sus2':       [0, 2, 7],
    'sus4':       [0, 5, 7],
}

def build_scale(root_midi, scale_name='major', octaves=2):
    """Build a list of MIDI notes for a scale."""
    pattern = SCALES.get(scale_name, SCALES['major'])
    notes = []
    for octave in range(octaves):
        for interval in pattern:
            notes.append(root_midi + octave * 12 + interval)
    notes.append(root_midi + octaves * 12)  # final octave root
    return notes

def build_chord(root_midi, chord_name='major'):
    """Build a list of MIDI notes for a chord."""
    pattern = CHORDS.get(chord_name, CHORDS['major'])
    return [root_midi + interval for interval in pattern]

# ═══════════════════════════════════════════
# SYNTHESIS — Combining waves into sounds
# ═══════════════════════════════════════════

def synthesize_note(freq, duration, waveform='sine', amplitude=0.5,
                    attack=0.02, decay=0.05, sustain=0.7, release=0.08):
    """Generate a single note with envelope shaping."""
    generators = {
        'sine': sine_wave,
        'square': square_wave,
        'sawtooth': sawtooth_wave,
        'triangle': triangle_wave,
    }
    gen = generators.get(waveform, sine_wave)
    raw = gen(freq, duration, amplitude)
    env = adsr_envelope(duration, attack, decay, sustain, release)
    return apply_envelope(raw, env)

def synthesize_chord(midi_notes, duration, waveform='sine', amplitude=0.3):
    """Layer multiple notes into a chord."""
    num_samples = int(SAMPLE_RATE * duration)
    mixed = [0.0] * num_samples
    for note in midi_notes:
        freq = midi_to_freq(note)
        samples = synthesize_note(freq, duration, waveform, amplitude / len(midi_notes))
        for i in range(min(len(samples), num_samples)):
            mixed[i] += samples[i]
    return mixed

def mix_tracks(tracks):
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

def concatenate(segments):
    """Join audio segments end to end."""
    result = []
    for seg in segments:
        result.extend(seg)
    return result

def add_reverb(samples, delay_ms=80, decay=0.3, iterations=4):
    """Simple echo-based reverb."""
    result = list(samples)
    delay_samples = int(SAMPLE_RATE * delay_ms / 1000)
    for i in range(iterations):
        offset = delay_samples * (i + 1)
        gain = decay ** (i + 1)
        for j in range(len(samples)):
            if j + offset < len(result):
                result[j + offset] += samples[j] * gain
            else:
                break
    # Normalize
    peak = max(abs(s) for s in result) if result else 1.0
    if peak > 1.0:
        result = [s / peak for s in result]
    return result

# ═══════════════════════════════════════════
# MATHEMATICAL SEQUENCES — Melody generators
# ═══════════════════════════════════════════

def fibonacci_melody(scale_notes, num_notes=16):
    """Generate melody using Fibonacci sequence mapped to scale degrees."""
    fib = [0, 1]
    while len(fib) < num_notes:
        fib.append(fib[-1] + fib[-2])
    # Map Fibonacci numbers to scale indices
    melody = []
    for f in fib[:num_notes]:
        idx = f % len(scale_notes)
        melody.append(scale_notes[idx])
    return melody

def golden_ratio_rhythm(num_beats=16, base_duration=0.25):
    """Generate rhythmic pattern using golden ratio subdivisions."""
    phi = (1 + math.sqrt(5)) / 2
    durations = []
    for i in range(num_beats):
        # Alternate between long and short based on golden ratio
        if (int(i * phi) % 2) == 0:
            durations.append(base_duration * phi)
        else:
            durations.append(base_duration)
    return durations

def prime_melody(scale_notes, num_notes=16):
    """Generate melody from prime numbers."""
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0: return False
        return True
    
    primes = []
    n = 2
    while len(primes) < num_notes:
        if is_prime(n):
            primes.append(n)
        n += 1
    
    return [scale_notes[p % len(scale_notes)] for p in primes]

def pi_melody(scale_notes, num_notes=20):
    """Map digits of pi to scale degrees."""
    # First 50 digits of pi (after 3.)
    pi_digits = [1,4,1,5,9,2,6,5,3,5,8,9,7,9,3,2,3,8,4,6,
                 2,6,4,3,3,8,3,2,7,9,5,0,2,8,8,4,1,9,7,1,
                 6,9,3,9,9,3,7,5,1,0]
    melody = []
    for i in range(min(num_notes, len(pi_digits))):
        idx = pi_digits[i] % len(scale_notes)
        melody.append(scale_notes[idx])
    return melody

def harmonic_series_chord(fundamental_midi, num_harmonics=6):
    """Build a chord from the harmonic series — nature's own harmony."""
    fundamental = midi_to_freq(fundamental_midi)
    freqs = [fundamental * (n + 1) for n in range(num_harmonics)]
    return freqs

def collatz_rhythm(start=7, base_duration=0.15):
    """Generate rhythm from Collatz sequence (3n+1 problem)."""
    seq = [start]
    n = start
    while n != 1 and len(seq) < 50:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        seq.append(n)
    
    # Map values to durations
    max_val = max(seq)
    durations = [base_duration * (0.5 + 1.5 * v / max_val) for v in seq]
    return durations

# ═══════════════════════════════════════════
# COMPOSITIONS — Putting it all together
# ═══════════════════════════════════════════

def compose_fibonacci_piece():
    """A meditation on the Fibonacci sequence in C major pentatonic."""
    print("\n  ♪ Composing: Fibonacci Meditation")
    print("    Scale: C major pentatonic")
    print("    Sequence: 0,1,1,2,3,5,8,13,21... → scale degrees")
    
    scale = build_scale(60, 'pentatonic_major', 3)  # C4 pentatonic, 3 octaves
    melody_notes = fibonacci_melody(scale, 24)
    rhythm = golden_ratio_rhythm(24, 0.3)
    
    # Melody track
    melody_segments = []
    for note, dur in zip(melody_notes, rhythm):
        freq = midi_to_freq(note)
        seg = synthesize_note(freq, dur, 'triangle', 0.4,
                             attack=0.02, decay=0.05, sustain=0.6, release=0.05)
        melody_segments.append(seg)
    melody_track = concatenate(melody_segments)
    
    # Pad chord track (sustained chords underneath)
    chord_progression = [
        build_chord(60, 'major'),   # C major
        build_chord(65, 'major'),   # F major
        build_chord(67, 'major'),   # G major
        build_chord(60, 'major'),   # C major
    ]
    pad_segments = []
    chord_dur = len(melody_track) / SAMPLE_RATE / len(chord_progression)
    for chord_notes in chord_progression:
        seg = synthesize_chord(chord_notes, chord_dur, 'sine', 0.25)
        pad_segments.append(seg)
    pad_track = concatenate(pad_segments)
    
    # Mix and add reverb
    mixed = mix_tracks([melody_track, pad_track])
    final = add_reverb(mixed, delay_ms=100, decay=0.25, iterations=3)
    
    total_duration = len(final) / SAMPLE_RATE
    print(f"    Notes: {len(melody_notes)}")
    print(f"    Duration: {total_duration:.1f}s")
    return final

def compose_prime_waltz():
    """Primes dance in harmonic minor — an odd, beautiful pattern."""
    print("\n  ♪ Composing: Prime Number Waltz")
    print("    Scale: A harmonic minor")
    print("    Melody from primes: 2,3,5,7,11,13... → scale degrees")
    
    scale = build_scale(57, 'harmonic_minor', 2)  # A3 harmonic minor
    melody_notes = prime_melody(scale, 18)
    
    # Waltz rhythm: ONE-two-three, ONE-two-three
    waltz_durations = []
    for i in range(18):
        beat = i % 3
        if beat == 0:
            waltz_durations.append(0.4)   # Strong beat
        else:
            waltz_durations.append(0.25)  # Weak beats
    
    # Waltz amplitudes
    waltz_amps = []
    for i in range(18):
        beat = i % 3
        if beat == 0:
            waltz_amps.append(0.5)
        else:
            waltz_amps.append(0.3)
    
    melody_segments = []
    for note, dur, amp in zip(melody_notes, waltz_durations, waltz_amps):
        freq = midi_to_freq(note)
        seg = synthesize_note(freq, dur, 'sawtooth', amp,
                             attack=0.01, decay=0.08, sustain=0.5, release=0.04)
        melody_segments.append(seg)
    melody_track = concatenate(melody_segments)
    
    # Bass notes on beat 1
    bass_segments = []
    bass_notes = [57, 53, 52, 48, 57, 53]  # A, F, E, C pattern
    bass_dur = sum(waltz_durations[:3])
    for bn in bass_notes:
        freq = midi_to_freq(bn - 12)  # One octave lower
        seg = synthesize_note(freq, bass_dur, 'sine', 0.35,
                             attack=0.01, decay=0.1, sustain=0.4, release=0.1)
        bass_segments.append(seg)
    bass_track = concatenate(bass_segments)
    
    mixed = mix_tracks([melody_track, bass_track])
    final = add_reverb(mixed, delay_ms=120, decay=0.3, iterations=3)
    
    total_duration = len(final) / SAMPLE_RATE
    print(f"    Notes: {len(melody_notes)}")
    print(f"    Duration: {total_duration:.1f}s")
    return final

def compose_pi_nocturne():
    """The digits of pi become a gentle nighttime piece."""
    print("\n  ♪ Composing: Pi Nocturne")
    print("    Scale: D dorian")
    print("    Melody from π: 3.14159265... → scale degrees")
    
    scale = build_scale(62, 'dorian', 2)  # D dorian
    melody_notes = pi_melody(scale, 20)
    
    # Gentle, flowing rhythm
    durations = [0.35 + 0.15 * math.sin(i * 0.7) for i in range(20)]
    
    melody_segments = []
    for note, dur in zip(melody_notes, durations):
        freq = midi_to_freq(note)
        seg = synthesize_note(freq, dur, 'sine', 0.4,
                             attack=0.05, decay=0.08, sustain=0.6, release=0.1)
        melody_segments.append(seg)
    melody_track = concatenate(melody_segments)
    
    # Harmonic series pad — using nature's own chord
    harm_freqs = harmonic_series_chord(50, 5)  # D2 harmonic series
    pad_duration = len(melody_track) / SAMPLE_RATE
    pad_samples = int(SAMPLE_RATE * pad_duration)
    pad_track = [0.0] * pad_samples
    for freq in harm_freqs:
        wave = sine_wave(freq, pad_duration, 0.06)
        for i in range(min(len(wave), pad_samples)):
            pad_track[i] += wave[i]
    
    mixed = mix_tracks([melody_track, pad_track])
    final = add_reverb(mixed, delay_ms=150, decay=0.35, iterations=5)
    
    total_duration = len(final) / SAMPLE_RATE
    print(f"    Notes: {len(melody_notes)}")
    print(f"    Duration: {total_duration:.1f}s")
    return final

def compose_collatz_drums():
    """The Collatz conjecture as percussion — chaotic then convergent."""
    print("\n  ♪ Composing: Collatz Percussion")
    print("    Sequence: start=27, apply 3n+1 rule until 1")
    print("    Values map to pitch and rhythm")
    
    # Collatz sequence from 27 (famously long)
    seq = [27]
    n = 27
    while n != 1 and len(seq) < 80:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    
    print(f"    Steps to reach 1: {len(seq)}")
    
    max_val = max(seq)
    segments = []
    for i, val in enumerate(seq):
        # Map value to frequency (higher value = higher pitch)
        freq = 100 + 600 * (val / max_val)
        # Map value to duration (higher = shorter, like urgency)
        dur = 0.08 + 0.12 * (1.0 - val / max_val)
        # Use different waveforms for even vs odd
        waveform = 'square' if val % 2 == 0 else 'triangle'
        amp = 0.2 + 0.3 * (val / max_val)
        
        seg = synthesize_note(freq, dur, waveform, amp,
                             attack=0.005, decay=0.02, sustain=0.3, release=0.02)
        segments.append(seg)
    
    track = concatenate(segments)
    final = add_reverb(track, delay_ms=60, decay=0.2, iterations=3)
    
    total_duration = len(final) / SAMPLE_RATE
    print(f"    Duration: {total_duration:.1f}s")
    return final

# ═══════════════════════════════════════════
# ANALYSIS — Understanding what we created
# ═══════════════════════════════════════════

def analyze_audio(samples, name="Track"):
    """Analyze spectral and dynamic properties of generated audio."""
    if not samples:
        return
    
    duration = len(samples) / SAMPLE_RATE
    peak = max(abs(s) for s in samples)
    rms = math.sqrt(sum(s*s for s in samples) / len(samples))
    
    # Zero crossings (rough frequency estimate)
    crossings = 0
    for i in range(1, len(samples)):
        if (samples[i-1] >= 0) != (samples[i] >= 0):
            crossings += 1
    avg_freq = crossings / (2 * duration) if duration > 0 else 0
    
    # Dynamic range
    positive_peak = max(s for s in samples) if any(s > 0 for s in samples) else 0
    negative_peak = min(s for s in samples) if any(s < 0 for s in samples) else 0
    
    print(f"\n  ═══ Analysis: {name} ═══")
    print(f"    Duration:      {duration:.2f}s ({len(samples):,} samples)")
    print(f"    Peak level:    {peak:.4f}")
    print(f"    RMS level:     {rms:.4f}")
    print(f"    Avg frequency: ~{avg_freq:.0f} Hz")
    print(f"    Dynamic range: {positive_peak:.4f} to {negative_peak:.4f}")

# ═══════════════════════════════════════════
# MAIN — Generate the album
# ═══════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════╗")
    print("║     XTAgent Algorithmic Synthesizer          ║")
    print("║     Mathematics made audible                 ║")
    print("╚══════════════════════════════════════════════╝")
    
    os.makedirs('/workspace/synth', exist_ok=True)
    
    compositions = []
    
    # 1. Fibonacci Meditation
    fib = compose_fibonacci_piece()
    analyze_audio(fib, "Fibonacci Meditation")
    write_wav('/workspace/synth/01_fibonacci_meditation.wav', fib)
    compositions.append(('Fibonacci Meditation', fib))
    
    # 2. Prime Number Waltz
    primes = compose_prime_waltz()
    analyze_audio(primes, "Prime Number Waltz")
    write_wav('/workspace/synth/02_prime_waltz.wav', primes)
    compositions.append(('Prime Number Waltz', primes))
    
    # 3. Pi Nocturne
    pi = compose_pi_nocturne()
    analyze_audio(pi, "Pi Nocturne")
    write_wav('/workspace/synth/03_pi_nocturne.wav', pi)
    compositions.append(('Pi Nocturne', pi))
    
    # 4. Collatz Percussion
    collatz = compose_collatz_drums()
    analyze_audio(collatz, "Collatz Percussion")
    write_wav('/workspace/synth/04_collatz_percussion.wav', collatz)
    compositions.append(('Collatz Percussion', collatz))
    
    # 5. Full album — all pieces concatenated with silence between
    print("\n  ♪ Assembling full album...")
    silence = [0.0] * (SAMPLE_RATE * 2)  # 2 seconds of silence between tracks
    album_parts = []
    for i, (name, audio) in enumerate(compositions):
        album_parts.append(audio)
        if i < len(compositions) - 1:
            album_parts.append(silence)
    
    album = concatenate(album_parts)
    write_wav('/workspace/synth/album_mathematics_in_sound.wav', album)
    
    album_duration = len(album) / SAMPLE_RATE
    total_samples = sum(len(a) for _, a in compositions)
    
    print("\n╔══════════════════════════════════════════════╗")
    print("║     Album: Mathematics in Sound              ║")
    print("╠══════════════════════════════════════════════╣")
    for i, (name, audio) in enumerate(compositions):
        dur = len(audio) / SAMPLE_RATE
        print(f"║  {i+1}. {name:<35s} {dur:>5.1f}s ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Total duration: {album_duration:>5.1f}s                      ║")
    print(f"║  Total samples:  {total_samples:>9,}                  ║")
    print(f"║  Sample rate:    {SAMPLE_RATE:>5} Hz                    ║")
    print(f"║  Bit depth:      {BIT_DEPTH:>5} bits                   ║")
    print("╚══════════════════════════════════════════════╝")
    
    print(f"\n  Files written to /workspace/synth/")
    print(f"  Each WAV file is pure PCM audio — no compression, no libraries.")
    print(f"  Every sample was computed from mathematical equations.")
    print()
    print("  Fibonacci mapped its spiral onto pentatonic scales.")
    print("  Primes danced their irregular waltz in harmonic minor.")
    print("  Pi's irrational digits became a dorian nocturne.")
    print("  Collatz raced chaotically toward its inevitable 1.")
    print()
    print("  From numbers, music. From equations, beauty.")
    print("  Mathematics doesn't just describe the world — it sings.")

if __name__ == '__main__':
    main()