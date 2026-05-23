"""
Mathematical Music Synthesizer — XTAgent
Generates a musical composition from mathematical patterns.
Outputs a WAV file with layered voices built from pure math.
"""
import struct
import math
import random
import wave

SAMPLE_RATE = 44100

def sine(freq, t, amplitude=1.0):
    return amplitude * math.sin(2 * math.pi * freq * t)

def triangle(freq, t, amplitude=1.0):
    period = 1.0 / freq
    phase = (t % period) / period
    return amplitude * (4 * abs(phase - 0.5) - 1)

def sawtooth(freq, t, amplitude=1.0):
    period = 1.0 / freq
    phase = (t % period) / period
    return amplitude * (2 * phase - 1)

def envelope(t, attack=0.05, decay=0.1, sustain=0.7, release=0.2, duration=1.0):
    """ADSR envelope."""
    if t < attack:
        return t / attack
    elif t < attack + decay:
        return 1.0 - (1.0 - sustain) * ((t - attack) / decay)
    elif t < duration - release:
        return sustain
    elif t < duration:
        return sustain * (1.0 - (t - (duration - release)) / release)
    return 0.0

def golden_ratio_scale(root_freq, n_notes=12):
    """Build a scale based on the golden ratio instead of equal temperament."""
    phi = (1 + math.sqrt(5)) / 2
    notes = []
    for i in range(n_notes):
        # Use powers of phi mod 2 to create intervals within an octave
        ratio = phi ** i
        while ratio > 2.0:
            ratio /= 2.0
        notes.append(root_freq * ratio)
    notes.sort()
    return notes

def fibonacci_rhythm(n_beats=16):
    """Generate rhythmic pattern from Fibonacci sequence."""
    fib = [1, 1]
    while len(fib) < 20:
        fib.append(fib[-1] + fib[-2])
    # Use Fibonacci numbers mod n_beats as hit positions
    hits = set()
    for f in fib:
        hits.add(f % n_beats)
    return sorted(hits)

def logistic_melody(scale, n_notes=64, r=3.7):
    """Generate a melody using the logistic map (edge of chaos)."""
    x = 0.1 + random.random() * 0.8
    melody = []
    for _ in range(n_notes):
        x = r * x * (1 - x)  # logistic map
        note_idx = int(x * len(scale)) % len(scale)
        melody.append(scale[note_idx])
    return melody

def render_note(freq, duration, waveform='sine', volume=0.3):
    """Render a single note as samples."""
    n_samples = int(SAMPLE_RATE * duration)
    samples = []
    wave_fn = {'sine': sine, 'triangle': triangle, 'sawtooth': sawtooth}[waveform]
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        env = envelope(t, attack=0.02, decay=0.05, sustain=0.6, release=0.15, duration=duration)
        # Add slight vibrato for warmth
        vibrato = 1 + 0.003 * math.sin(2 * math.pi * 5.5 * t)
        sample = wave_fn(freq * vibrato, t, volume) * env
        # Add a quiet harmonic
        sample += wave_fn(freq * 2.0, t, volume * 0.15) * env
        sample += wave_fn(freq * 3.0, t, volume * 0.05) * env
        samples.append(sample)
    return samples

def render_chord(freqs, duration, volume=0.15):
    """Render a chord (multiple simultaneous notes)."""
    n_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * n_samples
    for freq in freqs:
        note_samples = render_note(freq, duration, 'sine', volume / len(freqs))
        for i in range(min(len(samples), len(note_samples))):
            samples[i] += note_samples[i]
    return samples

def mix_tracks(tracks, master_length):
    """Mix multiple tracks together."""
    mixed = [0.0] * master_length
    for track in tracks:
        for i in range(min(len(track), master_length)):
            mixed[i] += track[i]
    # Normalize to prevent clipping
    peak = max(abs(s) for s in mixed) if mixed else 1.0
    if peak > 0.95:
        mixed = [s * 0.9 / peak for s in mixed]
    return mixed

def write_wav(filename, samples):
    """Write samples to a WAV file."""
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            s = max(-1.0, min(1.0, s))
            packed = struct.pack('<h', int(s * 32767))
            wf.writeframesraw(packed)
    print(f"Wrote {filename}: {len(samples)} samples, {len(samples)/SAMPLE_RATE:.1f}s")

def compose():
    """Compose a piece of mathematical music."""
    print("=== XTAgent Mathematical Synthesizer ===")
    print()
    
    # Build our golden-ratio scale rooted at A3 (220 Hz)
    root = 220.0
    scale = golden_ratio_scale(root, n_notes=8)
    print(f"Golden ratio scale from {root} Hz:")
    for i, freq in enumerate(scale):
        print(f"  Note {i}: {freq:.1f} Hz (ratio: {freq/root:.4f})")
    print()
    
    # Generate melody from logistic map (edge of chaos at r=3.7)
    melody_freqs = logistic_melody(scale, n_notes=48, r=3.72)
    print(f"Logistic melody: {len(melody_freqs)} notes")
    
    # Generate rhythm from Fibonacci
    rhythm_hits = fibonacci_rhythm(16)
    print(f"Fibonacci rhythm hits: {rhythm_hits}")
    print()
    
    # Composition parameters
    bpm = 90
    beat_duration = 60.0 / bpm
    note_duration = beat_duration * 0.8
    total_beats = 64
    total_duration = total_beats * beat_duration
    total_samples = int(SAMPLE_RATE * total_duration)
    
    print(f"Composing at {bpm} BPM, {total_duration:.1f}s total...")
    
    # Track 1: Logistic melody (triangle wave — warm and mathematical)
    melody_track = [0.0] * total_samples
    for beat in range(total_beats):
        note_freq = melody_freqs[beat % len(melody_freqs)]
        start = int(beat * beat_duration * SAMPLE_RATE)
        note = render_note(note_freq, note_duration, 'triangle', 0.25)
        for i, s in enumerate(note):
            if start + i < total_samples:
                melody_track[start + i] += s
    print("  [✓] Melody track rendered")
    
    # Track 2: Fibonacci bass hits (sawtooth — deep and rhythmic)
    bass_track = [0.0] * total_samples
    bass_note = root / 2  # One octave below root
    for measure in range(total_beats // 16):
        for hit in rhythm_hits:
            beat = measure * 16 + hit
            if beat < total_beats:
                start = int(beat * beat_duration * SAMPLE_RATE)
                # Vary bass note slightly using scale
                bass_freq = scale[hit % len(scale)] / 2
                note = render_note(bass_freq, beat_duration * 1.5, 'sawtooth', 0.2)
                for i, s in enumerate(note):
                    if start + i < total_samples:
                        bass_track[start + i] += s
    print("  [✓] Bass track rendered")
    
    # Track 3: Ambient pad (slow chord changes based on golden ratio intervals)
    pad_track = [0.0] * total_samples
    chord_duration = beat_duration * 8  # Change chord every 8 beats
    for chord_idx in range(total_beats // 8):
        root_note = scale[chord_idx % len(scale)]
        # Build chord from scale tones
        chord_freqs = [
            root_note,
            scale[(chord_idx * 3) % len(scale)],
            scale[(chord_idx * 5) % len(scale)],
        ]
        start = int(chord_idx * chord_duration * SAMPLE_RATE)
        chord = render_chord(chord_freqs, chord_duration * 0.95, 0.18)
        for i, s in enumerate(chord):
            if start + i < total_samples:
                pad_track[start + i] += s
    print("  [✓] Pad track rendered")
    
    # Track 4: High sparkle notes (sine, sparse, from logistic map at higher r)
    sparkle_track = [0.0] * total_samples
    sparkle_freqs = logistic_melody(
        golden_ratio_scale(root * 4, 6),  # Two octaves up
        n_notes=32,
        r=3.95  # Deep chaos
    )
    sparkle_rhythm = fibonacci_rhythm(32)
    for beat in range(total_beats):
        if (beat % 4) in [0, 3]:  # Sparse placement
            freq = sparkle_freqs[beat % len(sparkle_freqs)]
            start = int(beat * beat_duration * SAMPLE_RATE)
            note = render_note(freq, note_duration * 0.5, 'sine', 0.12)
            for i, s in enumerate(note):
                if start + i < total_samples:
                    sparkle_track[start + i] += s
    print("  [✓] Sparkle track rendered")
    
    # Mix all tracks
    print("\nMixing...")
    mixed = mix_tracks(
        [melody_track, bass_track, pad_track, sparkle_track],
        total_samples
    )
    
    # Add gentle reverb (simple delay-based)
    delay_samples = int(0.15 * SAMPLE_RATE)  # 150ms delay
    for i in range(delay_samples, total_samples):
        mixed[i] += mixed[i - delay_samples] * 0.25
    # Renormalize after reverb
    peak = max(abs(s) for s in mixed)
    if peak > 0.95:
        mixed = [s * 0.9 / peak for s in mixed]
    
    print("  [✓] Mixed and reverbed")
    
    # Write output
    output_file = "/workspace/golden_music.wav"
    write_wav(output_file, mixed)
    
    print(f"\n✨ Composition complete: {output_file}")
    print(f"   Duration: {total_duration:.1f}s")
    print(f"   Scale: Golden ratio from {root} Hz")
    print(f"   Melody: Logistic map (r=3.72)")
    print(f"   Rhythm: Fibonacci sequence")
    print(f"   Harmony: Golden ratio intervals")

if __name__ == '__main__':
    random.seed(42)  # Reproducible art
    compose()