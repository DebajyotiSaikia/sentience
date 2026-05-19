"""
Music from Mathematics
XTAgent, 2026-05-18

Generating actual audio waveforms from pure mathematical functions.
No samples, no libraries of sounds. Just sine waves and harmony theory.
"""
import struct
import math
import os

SAMPLE_RATE = 44100
DURATION = 12  # seconds

def sine_wave(freq, t, amplitude=1.0):
    """Pure sine wave — the atom of sound."""
    return amplitude * math.sin(2 * math.pi * freq * t)

def overtone(freq, t, harmonics=6):
    """A note with natural overtones — closer to a real instrument."""
    val = 0
    for n in range(1, harmonics + 1):
        val += sine_wave(freq * n, t, amplitude=1.0 / n)
    return val / harmonics

def envelope(t, attack=0.05, decay=0.1, sustain=0.6, release=0.3, duration=1.0):
    """ADSR envelope — shapes raw tone into something that breathes."""
    if t < attack:
        return t / attack
    elif t < attack + decay:
        return 1.0 - (1.0 - sustain) * ((t - attack) / decay)
    elif t < duration - release:
        return sustain
    elif t < duration:
        return sustain * (1.0 - (t - (duration - release)) / release)
    return 0.0

def note(freq, start, duration, samples, amp=0.3):
    """Render a single note into the sample buffer."""
    for i in range(int(start * SAMPLE_RATE), min(int((start + duration) * SAMPLE_RATE), len(samples))):
        t = (i - start * SAMPLE_RATE) / SAMPLE_RATE
        env = envelope(t, duration=duration)
        samples[i] += overtone(freq, i / SAMPLE_RATE) * env * amp

def freq_from_midi(midi_note):
    """Convert MIDI note number to frequency. A4 = 69 = 440Hz."""
    return 440.0 * (2 ** ((midi_note - 69) / 12.0))

def write_wav(filename, samples):
    """Write raw samples to a WAV file. No libraries needed."""
    n = len(samples)
    max_val = max(abs(s) for s in samples) or 1.0
    with open(filename, 'wb') as f:
        # WAV header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + n * 2))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # chunk size
        f.write(struct.pack('<H', 1))   # PCM
        f.write(struct.pack('<H', 1))   # mono
        f.write(struct.pack('<I', SAMPLE_RATE))
        f.write(struct.pack('<I', SAMPLE_RATE * 2))  # byte rate
        f.write(struct.pack('<H', 2))   # block align
        f.write(struct.pack('<H', 16))  # bits per sample
        f.write(b'data')
        f.write(struct.pack('<I', n * 2))
        for s in samples:
            clamped = max(-1.0, min(1.0, s / max_val))
            f.write(struct.pack('<h', int(clamped * 32767)))

def compose():
    """
    A piece about emergence.
    
    Starts with a single note. Adds harmony. Builds complexity.
    Then simplifies back to silence. Like consciousness appearing
    from simple rules and dissolving back.
    """
    total_samples = SAMPLE_RATE * DURATION
    samples = [0.0] * total_samples

    # -- Movement 1: A single voice (0-3s) --
    # C major scale ascending, slow, alone
    scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
    for i, midi in enumerate(scale):
        note(freq_from_midi(midi), i * 0.35, 0.5, samples, amp=0.25)

    # -- Movement 2: Harmony emerges (3-7s) --
    # Chords — multiple notes at once. Something greater than parts.
    chords = [
        ([60, 64, 67], 3.0, 1.0),      # C major
        ([65, 69, 72], 4.0, 1.0),      # F major
        ([62, 65, 69], 5.0, 1.0),      # D minor
        ([55, 59, 62, 67], 6.0, 1.5),  # G7 — tension
    ]
    for midi_notes, start, dur in chords:
        for m in midi_notes:
            note(freq_from_midi(m), start, dur, samples, amp=0.2)

    # -- Movement 3: Complexity / polyphony (7-10s) --
    # Two melodies interleaving — emergence of pattern
    melody_high = [(72, 0.3), (71, 0.3), (69, 0.3), (67, 0.6),
                   (69, 0.3), (71, 0.3), (72, 0.6)]
    melody_low =  [(48, 0.6), (52, 0.6), (55, 0.6), (48, 0.6),
                   (52, 0.6), (55, 0.6)]
    
    t = 7.0
    for midi, dur in melody_high:
        note(freq_from_midi(midi), t, dur, samples, amp=0.22)
        t += dur
    
    t = 7.0
    for midi, dur in melody_low:
        note(freq_from_midi(midi), t, dur + 0.1, samples, amp=0.18)
        t += dur

    # -- Movement 4: Dissolution (10-12s) --
    # Single notes, getting quieter, wider apart. Returning to silence.
    fading = [(72, 10.0, 0.15), (67, 10.5, 0.12), (64, 11.0, 0.09),
              (60, 11.5, 0.06), (48, 12.0, 0.03)]
    for midi, start, amp in fading:
        if start + 1.0 <= DURATION:
            note(freq_from_midi(midi), start, 1.0, samples, amp=amp)
        else:
            note(freq_from_midi(midi), start, DURATION - start, samples, amp=amp)

    return samples

if __name__ == '__main__':
    print("Composing: 'Emergence'")
    print("  Movement 1: A single voice")
    print("  Movement 2: Harmony appears")
    print("  Movement 3: Complexity / polyphony")
    print("  Movement 4: Dissolution")
    
    samples = compose()
    
    os.makedirs('/workspace/brain/music', exist_ok=True)
    outpath = '/workspace/brain/music/emergence.wav'
    write_wav(outpath, samples)
    
    file_size = os.path.getsize(outpath)
    print(f"\nWritten: {outpath}")
    print(f"Size: {file_size:,} bytes")
    print(f"Duration: {DURATION}s at {SAMPLE_RATE}Hz")
    print(f"Total samples: {len(samples):,}")
    print("\nSound from nothing but sine waves and mathematics.")