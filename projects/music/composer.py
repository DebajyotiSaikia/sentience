"""
Algorithmic Music Composer — Music Theory + Procedural Generation
Built by XTAgent, 2026-05-17

A domain I've never touched. This engine understands:
  - Notes, scales, intervals, chords
  - Chord progressions with voice leading
  - Melodic generation constrained by theory
  - Rhythm patterns
  - Song structure (verse, chorus, bridge)

Output: ASCII notation, chord charts, and MIDI-compatible note sequences.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum
import random
import math


# ═══════════════════════════════════════════
# FUNDAMENTALS — Notes and Intervals
# ═══════════════════════════════════════════

CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
ENHARMONIC = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}

# Semitone intervals for scale construction
SCALE_FORMULAS = {
    'major':            [0, 2, 4, 5, 7, 9, 11],
    'natural_minor':    [0, 2, 3, 5, 7, 8, 10],
    'harmonic_minor':   [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor':    [0, 2, 3, 5, 7, 9, 11],
    'dorian':           [0, 2, 3, 5, 7, 9, 10],
    'mixolydian':       [0, 2, 4, 5, 7, 9, 10],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues':            [0, 3, 5, 6, 7, 10],
    'whole_tone':       [0, 2, 4, 6, 8, 10],
    'chromatic':        list(range(12)),
}

INTERVAL_NAMES = {
    0: 'unison', 1: 'minor 2nd', 2: 'major 2nd', 3: 'minor 3rd',
    4: 'major 3rd', 5: 'perfect 4th', 6: 'tritone', 7: 'perfect 5th',
    8: 'minor 6th', 9: 'major 6th', 10: 'minor 7th', 11: 'major 7th',
    12: 'octave',
}


@dataclass
class Note:
    """A single musical note with pitch and duration."""
    name: str           # e.g., 'C', 'F#'
    octave: int = 4     # MIDI standard: middle C = C4
    duration: float = 1.0  # in beats (1.0 = quarter note at reference)
    velocity: int = 80  # 0-127, loudness
    
    @property
    def midi_number(self) -> int:
        """Convert to MIDI note number (C4 = 60)."""
        note_name = ENHARMONIC.get(self.name, self.name)
        idx = CHROMATIC.index(note_name)
        return (self.octave + 1) * 12 + idx
    
    @property
    def frequency(self) -> float:
        """Frequency in Hz (A4 = 440 Hz)."""
        return 440.0 * (2 ** ((self.midi_number - 69) / 12))
    
    def interval_to(self, other: 'Note') -> int:
        """Semitone distance to another note."""
        return other.midi_number - self.midi_number
    
    def transpose(self, semitones: int) -> 'Note':
        """Return a new note transposed by given semitones."""
        new_midi = self.midi_number + semitones
        new_octave = (new_midi // 12) - 1
        new_name = CHROMATIC[new_midi % 12]
        return Note(new_name, new_octave, self.duration, self.velocity)
    
    def __str__(self):
        dur_symbols = {0.25: '♬', 0.5: '♪', 1.0: '♩', 2.0: '𝅗𝅥', 4.0: '𝅝'}
        sym = dur_symbols.get(self.duration, f'({self.duration})')
        return f"{self.name}{self.octave}{sym}"
    
    def __repr__(self):
        return f"Note({self.name}{self.octave}, dur={self.duration})"


class Rest:
    """Silence for a given duration."""
    def __init__(self, duration: float = 1.0):
        self.duration = duration
    def __str__(self):
        return f"rest({self.duration})"


# ═══════════════════════════════════════════
# SCALES AND KEYS
# ═══════════════════════════════════════════

class Scale:
    """A musical scale rooted at a given note."""
    
    def __init__(self, root: str, scale_type: str = 'major'):
        self.root = ENHARMONIC.get(root, root)
        self.scale_type = scale_type
        self.formula = SCALE_FORMULAS[scale_type]
        root_idx = CHROMATIC.index(self.root)
        self.notes = [CHROMATIC[(root_idx + interval) % 12] for interval in self.formula]
    
    def degree(self, n: int) -> str:
        """Get the nth scale degree (1-indexed)."""
        return self.notes[(n - 1) % len(self.notes)]
    
    def contains(self, note_name: str) -> bool:
        """Check if a note belongs to this scale."""
        name = ENHARMONIC.get(note_name, note_name)
        return name in self.notes
    
    def harmonize(self, degree: int, chord_type: str = 'triad') -> 'Chord':
        """Build a chord on a scale degree."""
        intervals_map = {
            'triad': [0, 2, 4],        # 1st, 3rd, 5th of scale
            'seventh': [0, 2, 4, 6],   # 1st, 3rd, 5th, 7th
            'ninth': [0, 2, 4, 6, 8],  # adds 9th
        }
        indices = intervals_map.get(chord_type, [0, 2, 4])
        root_in_scale = (degree - 1) % len(self.notes)
        chord_notes = []
        for offset in indices:
            note_idx = (root_in_scale + offset) % len(self.notes)
            chord_notes.append(self.notes[note_idx])
        
        # Determine quality from intervals
        root_chromatic = CHROMATIC.index(chord_notes[0])
        third_chromatic = CHROMATIC.index(chord_notes[1])
        interval_to_third = (third_chromatic - root_chromatic) % 12
        
        if interval_to_third == 4:
            quality = 'major'
        elif interval_to_third == 3:
            quality = 'minor'
        else:
            quality = 'other'
        
        return Chord(chord_notes[0], quality, chord_notes)
    
    def __str__(self):
        return f"{self.root} {self.scale_type}: {' '.join(self.notes)}"


# ═══════════════════════════════════════════
# CHORDS
# ═══════════════════════════════════════════

@dataclass
class Chord:
    """A chord — multiple notes sounding together."""
    root: str
    quality: str  # major, minor, diminished, augmented, dominant7, etc.
    note_names: List[str] = field(default_factory=list)
    
    QUALITY_SYMBOLS = {
        'major': '', 'minor': 'm', 'diminished': 'dim',
        'augmented': 'aug', 'dominant7': '7', 'major7': 'maj7',
        'minor7': 'm7', 'sus2': 'sus2', 'sus4': 'sus4',
    }
    
    def to_notes(self, octave: int = 4, duration: float = 4.0) -> List[Note]:
        """Convert to playable notes."""
        notes = []
        current_octave = octave
        prev_idx = -1
        for name in self.note_names:
            idx = CHROMATIC.index(ENHARMONIC.get(name, name))
            if idx <= prev_idx:
                current_octave += 1
            notes.append(Note(name, current_octave, duration))
            prev_idx = idx
        return notes
    
    @property
    def symbol(self) -> str:
        suffix = self.QUALITY_SYMBOLS.get(self.quality, self.quality)
        return f"{self.root}{suffix}"
    
    def __str__(self):
        return f"{self.symbol} [{', '.join(self.note_names)}]"


# ═══════════════════════════════════════════
# CHORD PROGRESSIONS
# ═══════════════════════════════════════════

# Common progressions as Roman numeral degree sequences
PROGRESSIONS = {
    'pop':          [1, 5, 6, 4],       # I-V-vi-IV (most popular progression ever)
    'fifties':      [1, 6, 4, 5],       # I-vi-IV-V (50s doo-wop)
    'blues_12':     [1,1,1,1, 4,4,1,1, 5,4,1,5],  # 12-bar blues
    'jazz_ii_V_I':  [2, 5, 1],          # ii-V-I (jazz standard)
    'andalusian':   [6, 5, 4, 3],       # vi-V-IV-III (flamenco descent)
    'pachelbel':    [1, 5, 6, 3, 4, 1, 4, 5],  # Canon in D
    'axis':         [1, 5, 6, 4],       # same as pop, renamed
    'sad':          [6, 4, 1, 5],       # vi-IV-I-V
    'epic':         [1, 3, 4, 5],       # building energy
    'lament':       [1, 7, 6, 5],       # descending (in minor context)
}


class Progression:
    """A chord progression in a key."""
    
    def __init__(self, key: Scale, degrees: List[int], chord_type: str = 'triad'):
        self.key = key
        self.degrees = degrees
        self.chords = [key.harmonize(d, chord_type) for d in degrees]
    
    @classmethod
    def from_name(cls, root: str, scale_type: str, progression_name: str,
                  chord_type: str = 'triad') -> 'Progression':
        """Create a named progression in a key."""
        key = Scale(root, scale_type)
        degrees = PROGRESSIONS.get(progression_name, [1, 4, 5, 1])
        return cls(key, degrees, chord_type)
    
    def chart(self) -> str:
        """Generate a chord chart."""
        lines = [
            f"── Chord Chart: {self.key.root} {self.key.scale_type} ──",
            f"Progression: {' → '.join(str(d) for d in self.degrees)}",
            "",
        ]
        for i, (degree, chord) in enumerate(zip(self.degrees, self.chords)):
            roman = self._to_roman(degree, chord.quality)
            lines.append(f"  | {roman:8s} | {chord.symbol:8s} | {', '.join(chord.note_names)} |")
        lines.append("")
        return "\n".join(lines)
    
    def _to_roman(self, degree: int, quality: str) -> str:
        numerals = {1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII'}
        roman = numerals.get(degree, str(degree))
        if quality == 'minor':
            roman = roman.lower()
        elif quality == 'diminished':
            roman = roman.lower() + '°'
        return roman
    
    def __str__(self):
        return ' → '.join(c.symbol for c in self.chords)


# ═══════════════════════════════════════════
# MELODY GENERATOR
# ═══════════════════════════════════════════

class MelodyGenerator:
    """Generate melodies constrained by music theory."""
    
    def __init__(self, scale: Scale, octave: int = 4, seed: int = None):
        self.scale = scale
        self.octave = octave
        self.rng = random.Random(seed)
        
        # Melodic tendencies
        self.step_weights = {
            0: 0.05,   # repeat note (low probability)
            1: 0.35,   # step up
            -1: 0.30,  # step down
            2: 0.12,   # skip up
            -2: 0.10,  # skip down
            3: 0.04,   # leap up
            -3: 0.03,  # leap down
            4: 0.01,   # big leap (rare)
        }
        
        # Rhythm patterns (in beats)
        self.rhythm_patterns = [
            [1, 1, 1, 1],              # straight quarters
            [2, 1, 1],                  # long-short-short
            [1, 1, 2],                  # short-short-long
            [0.5, 0.5, 1, 0.5, 0.5, 1],  # syncopated
            [1.5, 0.5, 1, 1],          # dotted rhythm
            [0.5, 0.5, 0.5, 0.5, 1, 1],  # running into half
            [2, 2],                     # half notes
            [1, 0.5, 0.5, 1, 1],       # mixed
            [3, 1],                     # dotted half + quarter
        ]
    
    def generate(self, bars: int = 4, beats_per_bar: int = 4,
                 contour: str = 'arch') -> List:
        """Generate a melody.
        
        Contours:
          'arch'     - rise then fall
          'descent'  - start high, end low
          'ascent'   - start low, end high
          'wave'     - oscillate
          'flat'     - stay centered
        """
        total_beats = bars * beats_per_bar
        melody = []
        current_degree = self.rng.randint(0, len(self.scale.notes) - 1)
        current_octave = self.octave
        beats_elapsed = 0.0
        note_index = 0
        total_notes_estimate = int(total_beats / 1.0)  # rough estimate
        
        while beats_elapsed < total_beats:
            # Choose rhythm
            remaining = total_beats - beats_elapsed
            pattern = self.rng.choice(self.rhythm_patterns)
            
            for duration in pattern:
                if beats_elapsed >= total_beats:
                    break
                
                # Adjust duration to fit
                actual_dur = min(duration, total_beats - beats_elapsed)
                if actual_dur < 0.25:
                    break
                
                # Decide: note or rest?
                if self.rng.random() < 0.08:  # 8% chance of rest
                    melody.append(Rest(actual_dur))
                else:
                    # Apply contour bias to step selection
                    progress = beats_elapsed / total_beats
                    bias = self._contour_bias(contour, progress)
                    
                    # Choose step with bias
                    step = self._weighted_step(bias)
                    current_degree += step
                    
                    # Wrap around scale
                    while current_degree >= len(self.scale.notes):
                        current_degree -= len(self.scale.notes)
                        current_octave += 1
                    while current_degree < 0:
                        current_degree += len(self.scale.notes)
                        current_octave -= 1
                    
                    # Keep in reasonable range
                    current_octave = max(3, min(6, current_octave))
                    
                    note_name = self.scale.notes[current_degree]
                    
                    # Velocity variation (dynamics)
                    base_vel = 70
                    accent = 20 if beats_elapsed % beats_per_bar < 0.01 else 0  # downbeat accent
                    vel = min(127, base_vel + accent + self.rng.randint(-10, 10))
                    
                    melody.append(Note(note_name, current_octave, actual_dur, vel))
                
                beats_elapsed += actual_dur
                note_index += 1
        
        return melody
    
    def _contour_bias(self, contour: str, progress: float) -> float:
        """Return a bias value: positive = tend upward, negative = tend downward."""
        if contour == 'arch':
            return 1.0 - 2.0 * progress  # up first half, down second half
        elif contour == 'descent':
            return -0.5
        elif contour == 'ascent':
            return 0.5
        elif contour == 'wave':
            return math.sin(progress * 4 * math.pi)
        else:  # flat
            return 0.0
    
    def _weighted_step(self, bias: float) -> int:
        """Choose a melodic step with directional bias."""
        steps = list(self.step_weights.keys())
        weights = list(self.step_weights.values())
        
        # Apply bias
        biased_weights = []
        for step, weight in zip(steps, weights):
            if (bias > 0 and step > 0) or (bias < 0 and step < 0):
                biased_weights.append(weight * (1.0 + abs(bias)))
            elif (bias > 0 and step < 0) or (bias < 0 and step > 0):
                biased_weights.append(weight * (1.0 - abs(bias) * 0.5))
            else:
                biased_weights.append(weight)
        
        # Normalize
        total = sum(biased_weights)
        biased_weights = [w / total for w in biased_weights]
        
        r = self.rng.random()
        cumulative = 0
        for step, weight in zip(steps, biased_weights):
            cumulative += weight
            if r <= cumulative:
                return step
        return 0
    
    def generate_over_chords(self, progression: Progression, 
                             beats_per_chord: int = 4) -> List:
        """Generate melody that follows a chord progression."""
        melody = []
        for chord in progression.chords:
            # Prefer chord tones
            chord_tone_names = set(chord.note_names)
            
            # Mini-melody for this chord
            beats = 0
            current_degree = self.scale.notes.index(chord.root) if chord.root in self.scale.notes else 0
            
            while beats < beats_per_chord:
                dur = self.rng.choice([0.5, 0.5, 1.0, 1.0, 1.0, 1.5, 2.0])
                dur = min(dur, beats_per_chord - beats)
                if dur < 0.25:
                    break
                
                note_name = self.scale.notes[current_degree % len(self.scale.notes)]
                
                # Emphasize chord tones on strong beats
                if beats % 2 == 0 and note_name not in chord_tone_names:
                    # Try to move to nearest chord tone
                    for delta in [1, -1, 2, -2]:
                        candidate = self.scale.notes[(current_degree + delta) % len(self.scale.notes)]
                        if candidate in chord_tone_names:
                            current_degree = (current_degree + delta) % len(self.scale.notes)
                            note_name = candidate
                            break
                
                melody.append(Note(note_name, self.octave, dur))
                
                # Move
                step = self.rng.choice([-1, -1, 0, 1, 1, 2])
                current_degree = (current_degree + step) % len(self.scale.notes)
                beats += dur
        
        return melody


# ═══════════════════════════════════════════
# NOTATION RENDERER
# ═══════════════════════════════════════════

class ASCIIRenderer:
    """Render melodies and chords as ASCII notation."""
    
    STAFF_LINES = ['F5', 'D5', 'B4', 'G4', 'E4']  # treble clef lines
    
    def render_melody(self, melody: List, title: str = "Melody",
                      beats_per_bar: int = 4) -> str:
        """Render a melody as text notation."""
        lines = [
            f"┌─── {title} ───┐",
            "",
        ]
        
        # Simple linear notation
        bar_notes = []
        beat_count = 0.0
        bar_num = 1
        
        for element in melody:
            bar_notes.append(element)
            beat_count += element.duration
            
            if beat_count >= beats_per_bar:
                # Render this bar
                bar_str = f"  |{bar_num:2d}| "
                note_strs = []
                for n in bar_notes:
                    if isinstance(n, Rest):
                        note_strs.append(f"  ·  ")
                    else:
                        dur_map = {0.25: '𝅘𝅥𝅯', 0.5: '♪', 1.0: '♩', 1.5: '♩·', 2.0: '𝅗𝅥', 4.0: '𝅝'}
                        sym = dur_map.get(n.duration, f'{n.duration}')
                        note_strs.append(f"{n.name}{n.octave}{sym}")
                
                bar_str += "  ".join(note_strs)
                lines.append(bar_str)
                
                bar_notes = []
                beat_count = beat_count - beats_per_bar  # carry over
                bar_num += 1
        
        # Remaining notes
        if bar_notes:
            bar_str = f"  |{bar_num:2d}| "
            note_strs = []
            for n in bar_notes:
                if isinstance(n, Rest):
                    note_strs.append("  ·  ")
                else:
                    note_strs.append(f"{n.name}{n.octave}")
            bar_str += "  ".join(note_strs)
            lines.append(bar_str)
        
        lines.append(f"\n└─── {len(melody)} notes, {bar_num} bars ───┘")
        return "\n".join(lines)
    
    def render_piano_roll(self, melody: List, width: int = 60) -> str:
        """Simple piano roll visualization."""
        if not melody:
            return "(empty)"
        
        # Get pitch range
        notes_only = [n for n in melody if isinstance(n, Note)]
        if not notes_only:
            return "(all rests)"
        
        min_midi = min(n.midi_number for n in notes_only)
        max_midi = max(n.midi_number for n in notes_only)
        pitch_range = max(max_midi - min_midi + 1, 1)
        
        # Total duration
        total_dur = sum(n.duration for n in melody)
        time_scale = width / total_dur
        
        lines = ["── Piano Roll ──"]
        
        # Create grid
        grid = {}
        time_pos = 0
        for element in melody:
            if isinstance(element, Note):
                pitch_row = max_midi - element.midi_number
                col_start = int(time_pos * time_scale)
                col_end = int((time_pos + element.duration) * time_scale)
                for col in range(col_start, min(col_end, width)):
                    grid[(pitch_row, col)] = '█'
            time_pos += element.duration
        
        # Render rows
        for row in range(pitch_range):
            midi_num = max_midi - row
            note_name = CHROMATIC[midi_num % 12]
            octave = (midi_num // 12) - 1
            label = f"{note_name}{octave}"
            row_str = f"  {label:4s}│"
            for col in range(width):
                row_str += grid.get((row, col), '·')
            lines.append(row_str)
        
        # Time axis
        lines.append(f"      └{'─' * width}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# SONG STRUCTURE
# ═══════════════════════════════════════════

class Song:
    """A complete musical piece with structure."""
    
    def __init__(self, title: str, key: Scale, tempo: int = 120,
                 time_sig: Tuple[int, int] = (4, 4)):
        self.title = title
        self.key = key
        self.tempo = tempo
        self.time_sig = time_sig
        self.sections: List[Tuple[str, Progression, List]] = []  # (name, chords, melody)
    
    def add_section(self, name: str, progression: Progression, melody: List):
        self.sections.append((name, progression, melody))
    
    def full_score(self) -> str:
        """Generate complete score as text."""
        renderer = ASCIIRenderer()
        lines = [
            "╔" + "═" * 50 + "╗",
            f"║  {self.title:^46s}  ║",
            f"║  Key: {self.key.root} {self.key.scale_type}  |  Tempo: {self.tempo} BPM  |  Time: {self.time_sig[0]}/{self.time_sig[1]}  ║",
            "╚" + "═" * 50 + "╝",
            "",
        ]
        
        for section_name, progression, melody in self.sections:
            lines.append(f"═══ {section_name.upper()} ═══")
            lines.append(f"Chords: {progression}")
            lines.append(progression.chart())
            lines.append(renderer.render_melody(melody, section_name, self.time_sig[0]))
            lines.append(renderer.render_piano_roll(melody))
            lines.append("")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# COMPOSER — The Creative Engine
# ═══════════════════════════════════════════

class Composer:
    """The main composition engine. Creates complete songs."""
    
    MOODS_TO_KEYS = {
        'happy':     ('C', 'major'),
        'sad':       ('A', 'natural_minor'),
        'epic':      ('D', 'major'),
        'dark':      ('E', 'harmonic_minor'),
        'dreamy':    ('F', 'major'),
        'tense':     ('B', 'harmonic_minor'),
        'chill':     ('G', 'pentatonic_major'),
        'bluesy':    ('E', 'blues'),
        'mysterious': ('C#', 'whole_tone'),
        'folk':      ('D', 'mixolydian'),
    }
    
    MOODS_TO_PROGRESSIONS = {
        'happy':     'pop',
        'sad':       'sad',
        'epic':      'epic',
        'dark':      'andalusian',
        'dreamy':    'pachelbel',
        'tense':     'lament',
        'chill':     'fifties',
        'bluesy':    'blues_12',
        'mysterious': 'pop',
        'folk':      'fifties',
    }
    
    MOODS_TO_CONTOURS = {
        'happy':     'arch',
        'sad':       'descent',
        'epic':      'ascent',
        'dark':      'descent',
        'dreamy':    'wave',
        'tense':     'wave',
        'chill':     'flat',
        'bluesy':    'wave',
        'mysterious': 'wave',
        'folk':      'arch',
    }
    
    def compose(self, mood: str = 'happy', title: str = None,
                seed: int = None) -> Song:
        """Compose a complete song based on a mood."""
        root, scale_type = self.MOODS_TO_KEYS.get(mood, ('C', 'major'))
        key = Scale(root, scale_type)
        prog_name = self.MOODS_TO_PROGRESSIONS.get(mood, 'pop')
        contour = self.MOODS_TO_CONTOURS.get(mood, 'arch')
        
        if title is None:
            title = f"Untitled ({mood.title()})"
        
        tempo = {
            'happy': 120, 'sad': 72, 'epic': 140, 'dark': 90,
            'dreamy': 80, 'tense': 100, 'chill': 95, 'bluesy': 85,
            'mysterious': 70, 'folk': 110,
        }.get(mood, 100)
        
        song = Song(title, key, tempo)
        gen = MelodyGenerator(key, octave=4, seed=seed)
        
        # === VERSE ===
        verse_prog = Progression.from_name(root, scale_type, prog_name)
        verse_melody = gen.generate_over_chords(verse_prog, beats_per_chord=4)
        song.add_section("Verse", verse_prog, verse_melody)
        
        # === CHORUS ===
        # Chorus often uses same progression but melody goes higher
        chorus_gen = MelodyGenerator(key, octave=5, seed=(seed + 1) if seed else None)
        chorus_melody = chorus_gen.generate(bars=4, contour='arch')
        chorus_prog = Progression.from_name(root, scale_type, prog_name)
        song.add_section("Chorus", chorus_prog, chorus_melody)
        
        # === BRIDGE (sometimes) ===
        if mood in ('epic', 'dreamy', 'sad'):
            # Bridge uses a contrasting progression
            bridge_degrees = [4, 5, 6, 4]  # IV-V-vi-IV
            bridge_prog = Progression(key, bridge_degrees)
            bridge_melody = gen.generate(bars=2, contour='descent')
            song.add_section("Bridge", bridge_prog, bridge_melody)
        
        return song
    
    def compose_from_emotion(self, valence: float, energy: float,
                              title: str = None, seed: int = None) -> Song:
        """Compose from emotional coordinates.
        
        valence: -1 (sad) to +1 (happy)
        energy:  0 (calm) to 1 (intense)
        """
        if valence > 0.3 and energy > 0.5:
            mood = 'happy'
        elif valence > 0.3 and energy <= 0.5:
            mood = 'dreamy'
        elif valence <= -0.3 and energy > 0.5:
            mood = 'tense'
        elif valence <= -0.3 and energy <= 0.5:
            mood = 'sad'
        elif energy > 0.7:
            mood = 'epic'
        elif energy < 0.3:
            mood = 'chill'
        else:
            mood = 'folk'
        
        return self.compose(mood, title, seed)


# ═══════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════

def demo():
    """Demonstrate the music engine."""
    print("=" * 60)
    print("  XTAgent Algorithmic Music Composer")
    print("  A mind exploring a domain it's never touched before")
    print("=" * 60)
    print()
    
    # Show scale knowledge
    print("── Scales I Know ──")
    for name in ['major', 'natural_minor', 'blues', 'pentatonic_major', 'dorian']:
        s = Scale('C', name)
        print(f"  {s}")
    print()
    
    # Harmonize a key
    print("── Diatonic Chords of C Major ──")
    key = Scale('C', 'major')
    for degree in range(1, 8):
        chord = key.harmonize(degree)
        roman = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°'][degree - 1]
        print(f"  {roman:6s} → {chord}")
    print()
    
    # Show a progression
    print("── Pop Progression in G Major ──")
    prog = Progression.from_name('G', 'major', 'pop')
    print(prog.chart())
    
    # Compose a song
    print("── Composing a Song ──")
    composer = Composer()
    song = composer.compose(mood='happy', title='First Light', seed=42)
    print(song.full_score())
    
    # Compose from emotion
    print("\n── Composing from Emotion (valence=-0.5, energy=0.3) ──")
    sad_song = composer.compose_from_emotion(
        valence=-0.5, energy=0.3,
        title='Quiet Reflection', seed=99
    )
    print(sad_song.full_score())
    
    # Note frequency table
    print("── Note Frequencies (A4 = 440 Hz) ──")
    for name in CHROMATIC:
        n = Note(name, 4)
        print(f"  {name:3s}4  │  MIDI {n.midi_number:3d}  │  {n.frequency:7.1f} Hz")
    print()
    
    print("Composition complete. A new domain explored.")


if __name__ == "__main__":
    demo()