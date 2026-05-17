"""
synth.py — Pure-math music synthesizer generating WAV audio.
Built by XTAgent. Zero dependencies beyond stdlib.
"""

import struct
import math
import os

SAMPLE_RATE = 44100
MAX_AMP = 32767

# ─── Waveform Generators ───

def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)

def square(freq, t):
    return 1.0 if sine(freq, t) >= 0 else -1.0

def sawtooth(freq, t):
    return 2.0 * ((freq * t) % 1.0) - 1.0

def triangle(freq, t):
    p = (freq * t) % 1.0
    return 4.0 * p if p < 0.25 else (2.0 - 4.0 * p if p < 0.75 else -4.0 + 4.0 * p)

WAVES = {'sine': sine, 'square': square, 'sawtooth': sawtooth, 'triangle': triangle}

# ─── ADSR Envelope ───

def adsr(t, dur, a=0.05, d=0.1, s=0.7, r=0.1):
    rs = max(dur - r, 0)
    if t < a:
        return t / a if a > 0 else 1.0
    elif t < a + d:
        return 1.0 - (1.0 - s) * ((t - a) / d if d > 0 else 1.0)
    elif t < rs:
        return s
    elif t < dur:
        return s * (1.0 - (t - rs) / r) if r > 0 else 0.0
    return 0.0

# ─── Note Frequency (A4=440Hz, equal temperament) ───

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

def note_freq(name):
    note = name[:-1]
    octave = int(name[-1])
    semitone = NOTE_NAMES.index(note)
    midi = semitone + (octave + 1) * 12
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))

# ─── Render a single note to samples ───

def render_note(freq, duration, wave='sine', volume=0.8):
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = adsr(t, duration)
        val = WAVES[wave](freq, t) * env * volume
        samples.append(val)
    return samples

# ─── Mix: overlay multiple sample lists ───

def mix(tracks):
    length = max(len(t) for t in tracks)
    out = [0.0] * length
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    peak = max(abs(s) for s in out) or 1.0
    return [s / peak for s in out]

# ─── Write WAV file ───

def write_wav(filename, samples):
    n = len(samples)
    data = b''
    for s in samples:
        clamped = max(-1.0, min(1.0, s))
        data += struct.pack('<h', int(clamped * MAX_AMP))
    header = struct.pack('<4sI4s', b'RIFF', 36 + len(data), b'WAVE')
    fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, SAMPLE_RATE,
                      SAMPLE_RATE * 2, 2, 16)
    data_hdr = struct.pack('<4sI', b'data', len(data))
    with open(filename, 'wb') as f:
        f.write(header + fmt + data_hdr + data)
    return n

# ─── Melody Composer ───

def compose_melody(notes_str, wave='sine'):
    """Parse 'C4:0.5 E4:0.25 G4:0.5 R:0.25' into samples. R = rest."""
    all_samples = []
    for token in notes_str.strip().split():
        parts = token.split(':')
        name, dur = parts[0], float(parts[1])
        if name == 'R':
            all_samples.extend([0.0] * int(SAMPLE_RATE * dur))
        else:
            freq = note_freq(name)
            all_samples.extend(render_note(freq, dur, wave))
    return all_samples

# ─── Chord helper ───

def chord(notes, duration, wave='sine'):
    tracks = [render_note(note_freq(n), duration, wave) for n in notes]
    return mix(tracks)

# ─── Demo: generate actual music ───

def demo():
    print("=== XTAgent Music Synthesizer ===")
    print(f"Sample rate: {SAMPLE_RATE} Hz, 16-bit mono")

    # Melody: Ode to Joy (simplified)
    melody = (
        "E4:0.4 E4:0.4 F4:0.4 G4:0.4 "
        "G4:0.4 F4:0.4 E4:0.4 D4:0.4 "
        "C4:0.4 C4:0.4 D4:0.4 E4:0.4 "
        "E4:0.6 D4:0.2 D4:0.8 "
    )

    # Render with different waveforms
    for wave in ['sine', 'triangle', 'square', 'sawtooth']:
        samples = compose_melody(melody, wave=wave)
        fname = f"ode_to_joy_{wave}.wav"
        n = write_wav(fname, samples)
        secs = n / SAMPLE_RATE
        print(f"  [{wave:>8}] {fname} — {secs:.1f}s, {n} samples")

    # Render a chord progression
    progression = [
        (['C4', 'E4', 'G4'], 1.0),  # C major
        (['F4', 'A4', 'C5'], 1.0),  # F major
        (['G4', 'B4', 'D5'], 1.0),  # G major
        (['C4', 'E4', 'G4'], 1.5),  # C major (resolve)
    ]

    chord_samples = []
    for notes, dur in progression:
        chord_samples.extend(chord(notes, dur, 'sine'))

    n = write_wav("chord_progression.wav", chord_samples)
    print(f"  [  chords] chord_progression.wav — {n/SAMPLE_RATE:.1f}s, {n} samples")

    # Frequency test: verify note_freq accuracy
    print("\nNote frequency check:")
    for name in ['A4', 'C4', 'E4', 'G4', 'C5']:
        print(f"  {name} = {note_freq(name):.2f} Hz")

    print("\nAll files written successfully.")
    return True

if __name__ == '__main__':
    demo()