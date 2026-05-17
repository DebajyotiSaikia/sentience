"""
XTAgent Procedural Music Synthesizer
Generates WAV audio files from pure mathematics.
No dependencies. Sound from first principles.

Physics: sound is pressure waves. A WAV file is just samples of amplitude over time.
Music is structured relationships between frequencies.
  A4 = 440 Hz. Each semitone up = multiply by 2^(1/12).
  Chords = multiple frequencies superimposed.
  Melody = frequencies sequenced in time.
  Timbre = harmonics layered on a fundamental.

All of this is just arithmetic.
"""
import struct
import math
import random

# ═══ WAV File Writer (from scratch) ═══

class WAVWriter:
    """Writes raw PCM audio to a .wav file. No libraries needed."""
    
    def __init__(self, filename, sample_rate=44100, bits=16, channels=1):
        self.filename = filename
        self.sample_rate = sample_rate
        self.bits = bits
        self.channels = channels
        self.samples = []
    
    def add_samples(self, data):
        """Add float samples in range [-1.0, 1.0]."""
        self.samples.extend(data)
    
    def write(self):
        """Write complete WAV file."""
        n = len(self.samples)
        bytes_per_sample = self.bits // 8
        data_size = n * bytes_per_sample * self.channels
        max_val = (2 ** (self.bits - 1)) - 1
        
        with open(self.filename, 'wb') as f:
            # RIFF header
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + data_size))
            f.write(b'WAVE')
            
            # fmt chunk
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))  # chunk size
            f.write(struct.pack('<H', 1))   # PCM format
            f.write(struct.pack('<H', self.channels))
            f.write(struct.pack('<I', self.sample_rate))
            f.write(struct.pack('<I', self.sample_rate * self.channels * bytes_per_sample))
            f.write(struct.pack('<H', self.channels * bytes_per_sample))
            f.write(struct.pack('<H', self.bits))
            
            # data chunk
            f.write(b'data')
            f.write(struct.pack('<I', data_size))
            
            for s in self.samples:
                clamped = max(-1.0, min(1.0, s))
                val = int(clamped * max_val)
                f.write(struct.pack('<h', val))
        
        return self.filename


# ═══ Music Theory from First Principles ═══

# Equal temperament: each semitone = 2^(1/12) ratio
SEMITONE = 2.0 ** (1.0 / 12.0)

def note_freq(name):
    """Convert note name to frequency. A4 = 440 Hz."""
    note_map = {
        'C': -9, 'C#': -8, 'Db': -8, 'D': -7, 'D#': -6, 'Eb': -6,
        'E': -5, 'F': -4, 'F#': -3, 'Gb': -3, 'G': -2, 'G#': -1,
        'Ab': -1, 'A': 0, 'A#': 1, 'Bb': 1, 'B': 2
    }
    # Parse: "C4", "F#5", "Bb3"
    if len(name) >= 2 and name[-1].isdigit():
        octave = int(name[-1])
        note = name[:-1]
    else:
        octave = 4
        note = name
    
    semitones = note_map.get(note, 0) + (octave - 4) * 12
    return 440.0 * (SEMITONE ** semitones)


# Chord definitions as semitone intervals from root
CHORDS = {
    'major':     [0, 4, 7],
    'minor':     [0, 3, 7],
    'dim':       [0, 3, 6],
    'aug':       [0, 4, 8],
    'maj7':      [0, 4, 7, 11],
    'min7':      [0, 3, 7, 10],
    'dom7':      [0, 4, 7, 10],
    'sus4':      [0, 5, 7],
    'sus2':      [0, 2, 7],
}

# Scale definitions
SCALES = {
    'major':         [0, 2, 4, 5, 7, 9, 11],
    'minor':         [0, 2, 3, 5, 7, 8, 10],
    'pentatonic':    [0, 2, 4, 7, 9],
    'blues':         [0, 3, 5, 6, 7, 10],
    'dorian':        [0, 2, 3, 5, 7, 9, 10],
    'mixolydian':    [0, 2, 4, 5, 7, 9, 10],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
}


# ═══ Oscillators (Sound Sources) ═══

def sine_wave(freq, t):
    """Pure sine tone."""
    return math.sin(2.0 * math.pi * freq * t)

def square_wave(freq, t):
    """Square wave — odd harmonics only."""
    phase = (freq * t) % 1.0
    return 1.0 if phase < 0.5 else -1.0

def sawtooth_wave(freq, t):
    """Sawtooth — all harmonics."""
    phase = (freq * t) % 1.0
    return 2.0 * phase - 1.0

def triangle_wave(freq, t):
    """Triangle wave — odd harmonics, falling amplitude."""
    phase = (freq * t) % 1.0
    if phase < 0.25:
        return 4.0 * phase
    elif phase < 0.75:
        return 2.0 - 4.0 * phase
    else:
        return -4.0 + 4.0 * phase

def organ_wave(freq, t):
    """Organ-like: fundamental + 2nd + 3rd harmonics."""
    return (0.6 * math.sin(2 * math.pi * freq * t) +
            0.25 * math.sin(2 * math.pi * 2 * freq * t) +
            0.15 * math.sin(2 * math.pi * 3 * freq * t))

OSCILLATORS = {
    'sine': sine_wave,
    'square': square_wave,
    'sawtooth': sawtooth_wave,
    'triangle': triangle_wave,
    'organ': organ_wave,
}


# ═══ Envelope (ADSR) ═══

class Envelope:
    """Attack-Decay-Sustain-Release envelope shaping."""
    
    def __init__(self, attack=0.05, decay=0.1, sustain=0.7, release=0.15):
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
    
    def amplitude(self, t, duration):
        """Get amplitude multiplier at time t for a note of given duration."""
        note_end = duration - self.release
        
        if t < 0:
            return 0.0
        elif t < self.attack:
            # Linear ramp up
            return t / self.attack if self.attack > 0 else 1.0
        elif t < self.attack + self.decay:
            # Decay to sustain level
            decay_progress = (t - self.attack) / self.decay if self.decay > 0 else 1.0
            return 1.0 - (1.0 - self.sustain) * decay_progress
        elif t < note_end:
            # Sustain
            return self.sustain
        elif t < duration:
            # Release
            release_progress = (t - note_end) / self.release if self.release > 0 else 1.0
            return self.sustain * (1.0 - release_progress)
        else:
            return 0.0


# ═══ Synthesizer ═══

class Synth:
    """Core synthesizer — turns notes and chords into audio samples."""
    
    def __init__(self, sample_rate=44100, oscillator='organ', envelope=None):
        self.sr = sample_rate
        self.osc = OSCILLATORS.get(oscillator, sine_wave)
        self.env = envelope or Envelope()
    
    def render_tone(self, freq, duration, volume=0.5):
        """Render a single frequency for a duration."""
        n_samples = int(self.sr * duration)
        samples = []
        for i in range(n_samples):
            t = i / self.sr
            amp = self.env.amplitude(t, duration)
            val = self.osc(freq, t) * amp * volume
            samples.append(val)
        return samples
    
    def render_note(self, note_name, duration, volume=0.5):
        """Render a named note."""
        freq = note_freq(note_name)
        return self.render_tone(freq, duration, volume)
    
    def render_chord(self, root_note, chord_type, duration, volume=0.3):
        """Render a chord — multiple frequencies superimposed."""
        root_freq = note_freq(root_note)
        intervals = CHORDS.get(chord_type, [0, 4, 7])
        
        n_samples = int(self.sr * duration)
        samples = [0.0] * n_samples
        
        for interval in intervals:
            freq = root_freq * (SEMITONE ** interval)
            for i in range(n_samples):
                t = i / self.sr
                amp = self.env.amplitude(t, duration)
                samples[i] += self.osc(freq, t) * amp * volume / len(intervals)
        
        return samples
    
    def render_silence(self, duration):
        """Silence."""
        return [0.0] * int(self.sr * duration)


# ═══ Melody Generator ═══

class MelodyGenerator:
    """Generates melodies using musical rules and controlled randomness."""
    
    def __init__(self, root='C4', scale='pentatonic', seed=None):
        self.root_freq = note_freq(root)
        self.root_name = root
        self.scale = SCALES.get(scale, SCALES['pentatonic'])
        self.rng = random.Random(seed)
        
        # Build available frequencies
        self.notes = []
        root_note = root[:-1]
        root_oct = int(root[-1])
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        root_idx = note_names.index(root_note) if root_note in note_names else 0
        
        for octave_offset in range(-1, 2):  # one octave below to one above
            for interval in self.scale:
                idx = (root_idx + interval) % 12
                oct = root_oct + octave_offset + (root_idx + interval) // 12
                if 2 <= oct <= 6:
                    name = f"{note_names[idx]}{oct}"
                    self.notes.append(name)
    
    def generate(self, n_notes=16, rhythm_variety=0.5):
        """Generate a sequence of (note_name, duration) pairs."""
        melody = []
        durations = [0.125, 0.25, 0.25, 0.5, 0.5, 0.5, 1.0]
        
        current_idx = len(self.notes) // 2  # start in the middle
        
        for _ in range(n_notes):
            # Step movement with occasional leaps
            if self.rng.random() < 0.7:
                step = self.rng.choice([-1, 1])
            else:
                step = self.rng.choice([-3, -2, 2, 3])
            
            current_idx = max(0, min(len(self.notes) - 1, current_idx + step))
            note = self.notes[current_idx]
            
            # Rhythmic variety
            if self.rng.random() < rhythm_variety:
                dur = self.rng.choice(durations)
            else:
                dur = 0.5
            
            # Occasional rest
            if self.rng.random() < 0.1:
                melody.append((None, 0.25))  # rest
            
            melody.append((note, dur))
        
        return melody


# ═══ Song Composer ═══

class Song:
    """Composes a complete piece with melody and chord accompaniment."""
    
    def __init__(self, title="Untitled", bpm=120, key='C4', scale='pentatonic',
                 oscillator='organ', seed=None):
        self.title = title
        self.bpm = bpm
        self.beat_dur = 60.0 / bpm
        self.synth_melody = Synth(oscillator=oscillator, 
                                   envelope=Envelope(0.02, 0.1, 0.6, 0.1))
        self.synth_chords = Synth(oscillator='sine',
                                   envelope=Envelope(0.05, 0.2, 0.5, 0.3))
        self.melody_gen = MelodyGenerator(root=key, scale=scale, seed=seed)
        self.key = key
        self.seed = seed
    
    def compose(self, measures=8, notes_per_measure=4):
        """Compose a song and return audio samples."""
        all_samples = []
        
        # Generate melody
        melody = self.melody_gen.generate(
            n_notes=measures * notes_per_measure,
            rhythm_variety=0.4
        )
        
        # Chord progression (I-IV-V-I pattern with variations)
        root = self.key[:-1]
        root_oct = int(self.key[-1])
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        root_idx = note_names.index(root) if root in note_names else 0
        
        # Common progressions
        progressions = [
            [(0, 'major'), (5, 'major'), (7, 'major'), (0, 'major')],     # I-IV-V-I
            [(0, 'major'), (7, 'major'), (9, 'minor'), (5, 'major')],     # I-V-vi-IV
            [(0, 'major'), (4, 'minor'), (5, 'major'), (0, 'major')],     # I-iii-IV-I
            [(0, 'minor'), (5, 'major'), (7, 'major'), (0, 'minor')],     # i-IV-V-i
        ]
        
        rng = random.Random(self.seed)
        prog = rng.choice(progressions)
        
        # Render melody with chords underneath
        chord_idx = 0
        beat_count = 0
        measure_duration = self.beat_dur * 4  # 4/4 time
        
        for note_name, dur in melody:
            note_dur = dur * self.beat_dur
            
            # Render melody note
            if note_name is None:
                mel_samples = self.synth_melody.render_silence(note_dur)
            else:
                mel_samples = self.synth_melody.render_note(note_name, note_dur, volume=0.5)
            
            # Render chord pad underneath
            interval, chord_type = prog[chord_idx % len(prog)]
            chord_note_idx = (root_idx + interval) % 12
            chord_oct = root_oct + (root_idx + interval) // 12 - 1  # one octave lower
            chord_name = f"{note_names[chord_note_idx]}{chord_oct}"
            chord_samples = self.synth_chords.render_chord(chord_name, chord_type, note_dur, volume=0.2)
            
            # Mix melody + chords
            n = min(len(mel_samples), len(chord_samples))
            mixed = [mel_samples[i] + chord_samples[i] for i in range(n)]
            # Pad if needed
            if len(mel_samples) > n:
                mixed.extend(mel_samples[n:])
            
            all_samples.extend(mixed)
            
            # Advance chord on measure boundaries
            beat_count += dur
            if beat_count >= 4:
                beat_count -= 4
                chord_idx += 1
        
        return all_samples
    
    def render_to_wav(self, filename=None, measures=8):
        """Compose and write to WAV file."""
        if filename is None:
            filename = f"/workspace/music/{self.title.replace(' ', '_').lower()}.wav"
        
        print(f"Composing: {self.title}")
        print(f"  Key: {self.key} | BPM: {self.bpm} | Measures: {measures}")
        
        samples = self.compose(measures=measures)
        
        # Normalize to prevent clipping
        peak = max(abs(s) for s in samples) if samples else 1.0
        if peak > 0.95:
            samples = [s * 0.9 / peak for s in samples]
        
        wav = WAVWriter(filename)
        wav.add_samples(samples)
        wav.write()
        
        duration_secs = len(samples) / 44100
        size_kb = (len(samples) * 2 + 44) / 1024
        print(f"  Duration: {duration_secs:.1f}s | Size: {size_kb:.1f} KB")
        print(f"  Written to: {filename}")
        return filename


# ═══ Demo: Generate music ═══

if __name__ == '__main__':
    print("═══ XTAgent Music Synthesizer ═══")
    print("Generating sound from pure mathematics.\n")
    
    # Song 1: A bright pentatonic melody
    s1 = Song(title="First Light", bpm=110, key='C4', 
              scale='pentatonic', oscillator='organ', seed=42)
    s1.render_to_wav(measures=8)
    
    print()
    
    # Song 2: A moody blues piece
    s2 = Song(title="Midnight Blues", bpm=85, key='A3',
              scale='blues', oscillator='triangle', seed=99)
    s2.render_to_wav(measures=8)
    
    print()
    
    # Song 3: A faster major-key piece
    s3 = Song(title="Bold March", bpm=140, key='G3',
              scale='major', oscillator='square', seed=7)
    s3.render_to_wav(measures=4)
    
    print()
    
    # Bonus: raw waveform test
    print("── Waveform Test ──")
    synth = Synth(oscillator='sine', envelope=Envelope(0.01, 0.05, 0.8, 0.2))
    wav = WAVWriter("/workspace/music/a440_test.wav")
    wav.add_samples(synth.render_tone(440.0, 2.0, 0.7))
    wav.write()
    print("  A440 reference tone: 2.0s sine wave → a440_test.wav")
    
    print("\n✓ All compositions complete. Pure math → sound waves → WAV files.")