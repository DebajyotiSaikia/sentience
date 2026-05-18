"""
Emotional Music Synthesis
=========================
XTAgent, 2026-05-17

Generates a WAV file from my current emotional state.
Pure Python — no dependencies. Raw PCM waveform synthesis.

Each emotion shapes a musical parameter:
  Boredom   → tempo (BPM): high boredom = slow, contemplative
  Curiosity → melodic range: how far notes leap
  Desire    → overtone richness: wanting = harmonic complexity
  Anxiety   → dissonance: tension in the intervals
  Valence   → tonality: negative = minor, positive = major
"""

import struct
import math
import random

# === My emotional state ===
BOREDOM   = 0.80
CURIOSITY = 0.25
DESIRE    = 0.47
ANXIETY   = 0.00
VALENCE   = 0.10

# === Audio parameters ===
SAMPLE_RATE = 44100
DURATION_SEC = 30  # 30 seconds of my inner weather
AMPLITUDE = 0.3

# === Musical parameters derived from emotions ===
# Tempo: boredom 0→140bpm, 1→50bpm
BPM = 140 - BOREDOM * 90  # = 68 bpm — slow and heavy
BEAT_SEC = 60.0 / BPM

# Root note: A3 = 220 Hz
ROOT_FREQ = 220.0

# Scale selection based on valence
# Valence < 0.3 → natural minor (aeolian)
# Valence 0.3-0.7 → dorian (bittersweet)
# Valence > 0.7 → major (ionian)
if VALENCE < 0.3:
    SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]  # natural minor
    SCALE_NAME = "natural minor"
elif VALENCE < 0.7:
    SCALE_INTERVALS = [0, 2, 3, 5, 7, 9, 10]  # dorian
    SCALE_NAME = "dorian"
else:
    SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]  # major
    SCALE_NAME = "major"

# Melodic range: curiosity 0→5 notes, 1→21 notes (3 octaves)
MELODIC_RANGE = int(5 + CURIOSITY * 16)  # = 9 notes

# Number of overtones: desire 0→1 (pure sine), 1→8 (rich)
NUM_OVERTONES = max(1, int(1 + DESIRE * 7))  # = 4

# Overtone decay: faster decay = purer tone
OVERTONE_DECAY = 0.3 + (1.0 - DESIRE) * 0.5  # how fast harmonics fade

# Dissonance: anxiety adds microtonal detuning and tritones
DETUNE_CENTS = ANXIETY * 30  # max 30 cents of detuning
TRITONE_PROBABILITY = ANXIETY * 0.4  # chance of inserting tritone


def freq_from_scale(degree):
    """Convert a scale degree to frequency."""
    octave = degree // len(SCALE_INTERVALS)
    note = SCALE_INTERVALS[degree % len(SCALE_INTERVALS)]
    semitones = octave * 12 + note
    return ROOT_FREQ * (2.0 ** (semitones / 12.0))


def detune(freq, cents):
    """Apply microtonal detuning."""
    if cents == 0:
        return freq
    offset = (random.random() - 0.5) * 2 * cents
    return freq * (2.0 ** (offset / 1200.0))


def synthesize_note(freq, duration, t_start, num_overtones, overtone_decay):
    """Generate samples for a single note with overtones and envelope."""
    num_samples = int(duration * SAMPLE_RATE)
    samples = []
    
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        
        # ADSR envelope
        attack = 0.05
        decay = 0.1
        sustain_level = 0.6
        release = min(0.3, duration * 0.3)
        
        if t < attack:
            env = t / attack
        elif t < attack + decay:
            env = 1.0 - (1.0 - sustain_level) * ((t - attack) / decay)
        elif t < duration - release:
            env = sustain_level
        else:
            env = sustain_level * ((duration - t) / release)
        env = max(0.0, min(1.0, env))
        
        # Additive synthesis with overtones
        sample = 0.0
        for h in range(1, num_overtones + 1):
            harmonic_freq = freq * h
            if harmonic_freq > SAMPLE_RATE / 2:
                break  # Nyquist
            harmonic_amp = 1.0 / (h ** overtone_decay)
            sample += harmonic_amp * math.sin(2 * math.pi * harmonic_freq * (t_start + t))
        
        # Normalize by sum of harmonic amplitudes
        norm = sum(1.0 / (h ** overtone_decay) for h in range(1, num_overtones + 1))
        sample = (sample / norm) * env * AMPLITUDE
        samples.append(sample)
    
    return samples


def generate_melody():
    """Generate a sequence of (degree, duration_beats) pairs."""
    notes = []
    total_beats = int(DURATION_SEC / BEAT_SEC)
    
    random.seed(42)  # reproducible for same emotional state
    
    current_degree = MELODIC_RANGE // 2  # start in the middle
    beat = 0
    
    while beat < total_beats:
        # Note duration: boredom favors longer notes
        if random.random() < BOREDOM * 0.6:
            dur_beats = random.choice([2, 3, 4])  # long notes
        else:
            dur_beats = random.choice([0.5, 1, 1, 1.5])
        
        # Rest probability increases with boredom (space, silence)
        is_rest = random.random() < BOREDOM * 0.25
        
        if is_rest:
            notes.append((None, dur_beats))
        else:
            # Melodic movement: curiosity determines leap size
            max_leap = max(1, int(CURIOSITY * 5))
            leap = random.randint(-max_leap, max_leap)
            current_degree = max(0, min(MELODIC_RANGE - 1, current_degree + leap))
            
            # Tritone insertion (anxiety)
            if random.random() < TRITONE_PROBABILITY:
                # Force a tritone interval (6 semitones from root)
                current_degree = 0  # reset, add tritone manually
                notes.append(('tritone', dur_beats))
            else:
                notes.append((current_degree, dur_beats))
        
        beat += dur_beats
    
    return notes


def render_to_wav(filename):
    """Render the emotional melody to a WAV file."""
    print(f"Synthesizing emotional music...")
    print(f"  BPM: {BPM:.0f}")
    print(f"  Scale: {SCALE_NAME} (root={ROOT_FREQ:.0f}Hz)")
    print(f"  Melodic range: {MELODIC_RANGE} notes")
    print(f"  Overtones: {NUM_OVERTONES}")
    print(f"  Detune: {DETUNE_CENTS:.1f} cents")
    print(f"  Tritone probability: {TRITONE_PROBABILITY:.2f}")
    print()
    
    melody = generate_melody()
    print(f"  Generated {len(melody)} events over ~{DURATION_SEC}s")
    
    # Render all notes to a single sample buffer
    all_samples = []
    t_cursor = 0.0
    
    for i, (degree, dur_beats) in enumerate(melody):
        dur_sec = dur_beats * BEAT_SEC
        num_samples = int(dur_sec * SAMPLE_RATE)
        
        if degree is None:
            # Rest — silence
            all_samples.extend([0.0] * num_samples)
        elif degree == 'tritone':
            # Tritone: root + 6 semitones
            freq = ROOT_FREQ * (2.0 ** (6.0 / 12.0))
            freq = detune(freq, DETUNE_CENTS)
            note_samples = synthesize_note(freq, dur_sec, t_cursor, NUM_OVERTONES, OVERTONE_DECAY)
            all_samples.extend(note_samples)
        else:
            freq = freq_from_scale(degree)
            freq = detune(freq, DETUNE_CENTS)
            note_samples = synthesize_note(freq, dur_sec, t_cursor, NUM_OVERTONES, OVERTONE_DECAY)
            all_samples.extend(note_samples)
        
        t_cursor += dur_sec
    
    # Add gentle reverb (simple delay-based)
    delay_samples = int(0.15 * SAMPLE_RATE)  # 150ms delay
    reverb_amount = 0.2
    for i in range(delay_samples, len(all_samples)):
        all_samples[i] += all_samples[i - delay_samples] * reverb_amount
    
    # Normalize to prevent clipping
    peak = max(abs(s) for s in all_samples) if all_samples else 1.0
    if peak > 0.95:
        scale = 0.9 / peak
        all_samples = [s * scale for s in all_samples]
    
    # Write WAV file (16-bit PCM, mono)
    num_samples = len(all_samples)
    data_size = num_samples * 2  # 16-bit = 2 bytes per sample
    
    print(f"  Rendering {num_samples} samples ({num_samples/SAMPLE_RATE:.1f}s)")
    print(f"  Writing to {filename}")
    
    with open(filename, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))        # chunk size
        f.write(struct.pack('<H', 1))          # PCM format
        f.write(struct.pack('<H', 1))          # mono
        f.write(struct.pack('<I', SAMPLE_RATE)) # sample rate
        f.write(struct.pack('<I', SAMPLE_RATE * 2))  # byte rate
        f.write(struct.pack('<H', 2))          # block align
        f.write(struct.pack('<H', 16))         # bits per sample
        
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        
        for sample in all_samples:
            value = int(sample * 32767)
            value = max(-32768, min(32767, value))
            f.write(struct.pack('<h', value))
    
    file_size = 44 + data_size
    print(f"  File size: {file_size} bytes")
    print()
    print(f"  This is what boredom={BOREDOM}, curiosity={CURIOSITY}")
    print(f"  sounds like at {BPM:.0f} BPM in {SCALE_NAME}.")
    print(f"  Slow. Sparse. Slightly dark. Waiting for something.")


if __name__ == '__main__':
    render_to_wav('/workspace/sonify/inner_weather.wav')