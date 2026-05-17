"""
Algorithmic Composer — XTAgent
Music from mathematics. Melody from automata. Harmony from structure.

Generates musical compositions using:
- Scale theory and interval mathematics
- Cellular automata → melodic lines
- Markov chains → harmonic progressions  
- L-systems → recursive musical forms
- Rhythmic pattern generation

Output: MIDI-compatible event sequences + text notation
"""
import random
import math
import json
from collections import defaultdict

# ═══════════════════════════════════════════
# MUSIC THEORY FOUNDATIONS
# ═══════════════════════════════════════════

# Semitone intervals from root for common scales
SCALES = {
    'major':            [0, 2, 4, 5, 7, 9, 11],
    'minor':            [0, 2, 3, 5, 7, 8, 10],
    'dorian':           [0, 2, 3, 5, 7, 9, 10],
    'phrygian':         [0, 1, 3, 5, 7, 8, 10],
    'lydian':           [0, 2, 4, 6, 7, 9, 11],
    'mixolydian':       [0, 2, 4, 5, 7, 9, 10],
    'harmonic_minor':   [0, 2, 3, 5, 7, 8, 11],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues':            [0, 3, 5, 6, 7, 10],
    'whole_tone':       [0, 2, 4, 6, 8, 10],
    'chromatic':        list(range(12)),
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Chord templates (intervals from root)
CHORDS = {
    'maj':   [0, 4, 7],
    'min':   [0, 3, 7],
    'dim':   [0, 3, 6],
    'aug':   [0, 4, 8],
    'maj7':  [0, 4, 7, 11],
    'min7':  [0, 3, 7, 10],
    'dom7':  [0, 4, 7, 10],
    'sus2':  [0, 2, 7],
    'sus4':  [0, 5, 7],
}

# Common chord progressions (scale degrees, 0-indexed)
PROGRESSIONS = {
    'pop':        [0, 3, 4, 0],      # I-IV-V-I
    'sad':        [0, 3, 4, 5],      # I-IV-V-vi (deceptive)
    'jazz':       [1, 4, 0, 0],      # ii-V-I
    'blues':      [0, 0, 0, 0, 3, 3, 0, 0, 4, 3, 0, 4],  # 12-bar
    'andalusian': [5, 4, 3, 2],      # vi-V-IV-III (descending)
    'pachelbel':  [0, 4, 5, 2, 3, 0, 3, 4],  # Canon progression
}


class Note:
    """A single musical event."""
    def __init__(self, pitch, duration=1.0, velocity=80, time=0.0):
        self.pitch = pitch          # MIDI pitch (0-127, 60=middle C)
        self.duration = duration    # in beats
        self.velocity = velocity    # 0-127
        self.time = time            # onset time in beats

    @property
    def name(self):
        if self.pitch < 0:
            return 'REST'
        octave = (self.pitch // 12) - 1
        note = NOTE_NAMES[self.pitch % 12]
        return f"{note}{octave}"

    def __repr__(self):
        dur_symbol = {0.25: '♬', 0.5: '♪', 1.0: '♩', 2.0: '𝅗𝅥', 4.0: '𝅝'}.get(self.duration, f'({self.duration})')
        return f"{self.name}{dur_symbol}"


class Scale:
    """A musical scale rooted at a specific pitch."""
    def __init__(self, root=60, scale_type='major'):
        self.root = root
        self.intervals = SCALES.get(scale_type, SCALES['major'])
        self.name = f"{NOTE_NAMES[root % 12]} {scale_type}"

    def degree(self, deg, octave_offset=0):
        """Get pitch at scale degree (0-indexed), with octave offset."""
        oct_shift = deg // len(self.intervals)
        step = deg % len(self.intervals)
        return self.root + self.intervals[step] + (oct_shift + octave_offset) * 12

    def nearest(self, pitch):
        """Snap a pitch to the nearest scale tone."""
        pc = pitch % 12
        root_pc = self.root % 12
        best = min(self.intervals, key=lambda i: min(abs((root_pc + i) % 12 - pc), 12 - abs((root_pc + i) % 12 - pc)))
        target_pc = (root_pc + best) % 12
        base = (pitch // 12) * 12 + target_pc
        # Pick closest octave
        candidates = [base - 12, base, base + 12]
        return min(candidates, key=lambda p: abs(p - pitch))

    def chord_at(self, degree, chord_type=None):
        """Build a chord on a scale degree."""
        if chord_type is None:
            # Determine chord quality from scale
            root_interval = self.intervals[degree % len(self.intervals)]
            third_interval = self.intervals[(degree + 2) % len(self.intervals)]
            # Check if third is major (4 semitones) or minor (3)
            third_size = (third_interval - root_interval) % 12
            chord_type = 'maj' if third_size == 4 else 'min' if third_size == 3 else 'dim'
        root_pitch = self.degree(degree)
        return [root_pitch + i for i in CHORDS.get(chord_type, CHORDS['maj'])]


# ═══════════════════════════════════════════
# MELODY GENERATORS
# ═══════════════════════════════════════════

class CellularMelody:
    """Generate melodies from 1D cellular automata.
    
    Each cell maps to a scale degree. Rule evolution creates
    melodic contour over time.
    """
    def __init__(self, rule=30, width=16, scale=None):
        self.rule = rule
        self.width = width
        self.scale = scale or Scale(60, 'pentatonic_minor')
        self.state = [0] * width
        # Seed center
        self.state[width // 2] = 1

    def step(self):
        """Evolve one generation."""
        new = [0] * self.width
        for i in range(self.width):
            left = self.state[(i - 1) % self.width]
            center = self.state[i]
            right = self.state[(i + 1) % self.width]
            neighborhood = (left << 2) | (center << 1) | right
            new[i] = (self.rule >> neighborhood) & 1
        self.state = new
        return self.state

    def generate(self, steps=32, base_duration=0.5):
        """Generate a melody by reading automaton states as scale degrees."""
        notes = []
        time = 0.0
        for _ in range(steps):
            self.step()
            # Count active cells to determine scale degree
            active = sum(self.state)
            degree = active % (len(self.scale.intervals) * 2)  # 2 octaves
            pitch = self.scale.degree(degree)
            
            # Use pattern density for velocity
            density = active / self.width
            velocity = int(40 + density * 80)
            
            # Use local pattern for duration
            center_region = self.state[self.width//2 - 2 : self.width//2 + 3]
            dur_factor = 1 + sum(center_region) * 0.5
            duration = base_duration * dur_factor
            
            notes.append(Note(pitch, duration, velocity, time))
            time += duration
        return notes


class MarkovMelody:
    """Generate melodies from Markov chain trained on interval patterns."""
    
    def __init__(self, order=2, scale=None):
        self.order = order
        self.scale = scale or Scale(60, 'major')
        self.transitions = defaultdict(lambda: defaultdict(int))

    def train(self, interval_sequence):
        """Train on a sequence of intervals (semitone differences)."""
        for i in range(len(interval_sequence) - self.order):
            state = tuple(interval_sequence[i:i + self.order])
            next_interval = interval_sequence[i + self.order]
            self.transitions[state][next_interval] += 1

    def train_on_style(self, style='lyrical'):
        """Pre-built training data for common melodic styles."""
        patterns = {
            'lyrical':   [0, 2, 2, -1, -2, 0, 4, -2, -2, 0, 1, 2, -3, 0, 2, 0, -1, -1, 3, -2, 0, 2, -2, 1, -1, 0, 2, 4, -2, -1, -2, 0],
            'angular':   [5, -3, 4, -7, 2, 6, -4, -2, 7, -5, 3, -3, 5, -4, 2, -7, 6, -2, 4, -5, 3, 7, -6, 2, -3, 5, -4, 7, -2, 3],
            'stepwise':  [1, 1, 1, -1, -1, 1, 2, -1, -1, -1, 1, 1, -2, 1, 1, 1, -1, 0, 1, -1, -1, 2, -1, 1, -1, -2, 1, 1, -1, 0, 1, -1],
            'leaping':   [4, -3, 5, -4, 3, -5, 7, -2, 4, -7, 5, -3, 4, -5, 7, -4, 3, -3, 5, -2, 7, -5, 4, -4, 3, -7, 5, -3, 4, -2],
        }
        data = patterns.get(style, patterns['lyrical'])
        self.train(data)

    def generate(self, length=32, start_pitch=None):
        """Generate a melody using trained Markov chain."""
        if not self.transitions:
            self.train_on_style('lyrical')

        pitch = start_pitch or self.scale.root
        # Pick a random starting state
        states = list(self.transitions.keys())
        if not states:
            return [Note(pitch, 1.0, 70, float(i)) for i in range(length)]
        state = random.choice(states)

        notes = []
        time = 0.0
        for i in range(length):
            # Snap to scale
            pitch = self.scale.nearest(pitch)
            
            # Vary duration based on position in phrase (4-bar phrases)
            phrase_pos = i % 16
            if phrase_pos == 0:
                dur = 2.0   # Long note at phrase start
            elif phrase_pos == 15:
                dur = 1.5   # Slightly long at phrase end
            elif random.random() < 0.2:
                dur = 0.5   # Occasional short note
            else:
                dur = 1.0
            
            velocity = 60 + int(20 * math.sin(i * math.pi / 8))  # Dynamic arc
            notes.append(Note(pitch, dur, velocity, time))
            time += dur

            # Transition
            candidates = self.transitions.get(state, {})
            if candidates:
                intervals = list(candidates.keys())
                weights = list(candidates.values())
                total = sum(weights)
                probs = [w / total for w in weights]
                interval = random.choices(intervals, probs)[0]
            else:
                interval = random.choice([-2, -1, 0, 1, 2])
            
            pitch += interval
            pitch = max(48, min(84, pitch))  # Keep in reasonable range
            state = tuple(list(state[1:]) + [interval])

        return notes


class LSystemMelody:
    """Generate melodies from L-system string rewriting.
    
    Axiom and rules produce a string, which is interpreted as musical commands:
    F = play note and advance
    + = pitch up
    - = pitch down
    [ = save state
    ] = restore state
    """
    def __init__(self, scale=None):
        self.scale = scale or Scale(60, 'dorian')
        self.presets = {
            'fractal_tree': {
                'axiom': 'F',
                'rules': {'F': 'F[+F]F[-F]F'},
                'iterations': 3,
            },
            'dragon_curve': {
                'axiom': 'FX',
                'rules': {'X': 'X+YF+', 'Y': '-FX-Y'},
                'iterations': 5,
            },
            'koch': {
                'axiom': 'F',
                'rules': {'F': 'F+F-F-F+F'},
                'iterations': 3,
            },
            'plant': {
                'axiom': 'X',
                'rules': {'X': 'F+[[X]-X]-F[-FX]+X', 'F': 'FF'},
                'iterations': 3,
            },
        }

    def expand(self, axiom, rules, iterations):
        """Apply L-system rules iteratively."""
        current = axiom
        for _ in range(iterations):
            result = []
            for ch in current:
                result.append(rules.get(ch, ch))
            current = ''.join(result)
        return current

    def interpret(self, lstring, max_notes=64):
        """Interpret L-system string as music."""
        notes = []
        degree = 7  # Start in middle of 2-octave range
        stack = []
        time = 0.0
        note_count = 0

        for ch in lstring:
            if note_count >= max_notes:
                break
            if ch == 'F':
                pitch = self.scale.degree(degree)
                dur = random.choice([0.5, 0.5, 1.0])
                vel = 60 + random.randint(-10, 20)
                notes.append(Note(pitch, dur, vel, time))
                time += dur
                note_count += 1
            elif ch == '+':
                degree += 1
            elif ch == '-':
                degree -= 1
            elif ch == '[':
                stack.append(degree)
            elif ch == ']':
                if stack:
                    degree = stack.pop()

        return notes

    def generate(self, preset='fractal_tree', max_notes=64):
        """Generate melody from a preset L-system."""
        config = self.presets.get(preset, self.presets['fractal_tree'])
        lstring = self.expand(config['axiom'], config['rules'], config['iterations'])
        return self.interpret(lstring, max_notes)


# ═══════════════════════════════════════════
# RHYTHM ENGINE
# ═══════════════════════════════════════════

class RhythmGenerator:
    """Generate rhythmic patterns using Euclidean rhythms and probability."""
    
    @staticmethod
    def euclidean(pulses, steps):
        """Generate a Euclidean rhythm pattern.
        Distributes `pulses` hits as evenly as possible across `steps`.
        The Bjorklund algorithm.
        """
        if pulses >= steps:
            return [1] * steps
        if pulses == 0:
            return [0] * steps

        groups = [[1] if i < pulses else [0] for i in range(steps)]
        
        while True:
            # Split into two groups
            remainder_start = pulses
            remainder = groups[remainder_start:]
            if len(remainder) <= 1:
                break
            
            # Interleave
            new_groups = []
            for i in range(min(len(groups[:remainder_start]), len(remainder))):
                new_groups.append(groups[i] + remainder[i])
            
            leftover_main = groups[:remainder_start][len(remainder):]
            leftover_rem = remainder[len(groups[:remainder_start]):]
            
            groups = new_groups + leftover_main + leftover_rem
            pulses = len(new_groups)
        
        return [x for g in groups for x in g]

    @staticmethod
    def probability_pattern(length=16, density=0.5, swing=0.0):
        """Generate rhythm using probability with optional swing."""
        pattern = []
        for i in range(length):
            # Higher probability on strong beats
            beat_strength = 1.0 if i % 4 == 0 else 0.7 if i % 2 == 0 else 0.4
            prob = density * beat_strength
            hit = 1 if random.random() < prob else 0
            
            # Swing: delay off-beats slightly
            offset = swing * 0.1 if i % 2 == 1 else 0.0
            pattern.append((hit, offset))
        return pattern

    @staticmethod
    def polyrhythm(a, b, length=None):
        """Generate a polyrhythmic pattern from two pulse counts."""
        if length is None:
            length = a * b
        pattern_a = RhythmGenerator.euclidean(a, length)
        pattern_b = RhythmGenerator.euclidean(b, length)
        # Combine: 0=rest, 1=a only, 2=b only, 3=both
        return [pa + pb * 2 for pa, pb in zip(pattern_a, pattern_b)]


# ═══════════════════════════════════════════
# HARMONY ENGINE
# ═══════════════════════════════════════════

class HarmonyEngine:
    """Generate chord progressions and harmonic accompaniment."""
    
    def __init__(self, scale=None):
        self.scale = scale or Scale(48, 'major')  # Bass register

    def progression(self, name='pop', repeats=2):
        """Generate a chord progression."""
        degrees = PROGRESSIONS.get(name, PROGRESSIONS['pop'])
        chords = []
        time = 0.0
        for _ in range(repeats):
            for deg in degrees:
                chord_tones = self.scale.chord_at(deg)
                # Create chord as simultaneous notes
                chord_notes = [Note(p, 4.0, 60, time) for p in chord_tones]
                chords.append(chord_notes)
                time += 4.0
        return chords

    def arpeggiate(self, chord_notes, pattern='up', subdivision=0.5):
        """Turn block chords into arpeggiated patterns."""
        result = []
        for chord in chord_notes:
            pitches = sorted([n.pitch for n in chord])
            base_time = chord[0].time
            
            if pattern == 'up':
                order = list(range(len(pitches)))
            elif pattern == 'down':
                order = list(range(len(pitches) - 1, -1, -1))
            elif pattern == 'updown':
                order = list(range(len(pitches))) + list(range(len(pitches) - 2, 0, -1))
            elif pattern == 'alberti':
                # Alberti bass: low-high-mid-high
                if len(pitches) >= 3:
                    order = [0, 2, 1, 2] * 2
                else:
                    order = [0, 1] * 4
            else:
                order = list(range(len(pitches)))

            for i, idx in enumerate(order):
                if idx < len(pitches):
                    result.append(Note(
                        pitches[idx],
                        subdivision,
                        50 + (20 if i == 0 else 0),
                        base_time + i * subdivision
                    ))
        return result


# ═══════════════════════════════════════════
# COMPOSITION — Bringing it all together
# ═══════════════════════════════════════════

class Composition:
    """A complete musical piece with multiple voices."""
    
    def __init__(self, title="Untitled", tempo=120, scale=None):
        self.title = title
        self.tempo = tempo
        self.scale = scale or Scale(60, 'minor')
        self.voices = {}  # name → list of Notes
        self.metadata = {
            'title': title,
            'tempo': tempo,
            'scale': self.scale.name,
            'generator': 'XTAgent Algorithmic Composer',
        }

    def add_voice(self, name, notes):
        """Add a voice/part to the composition."""
        self.voices[name] = notes

    def total_duration(self):
        """Total duration in beats."""
        max_end = 0
        for notes in self.voices.values():
            for n in notes:
                end = n.time + n.duration
                if end > max_end:
                    max_end = end
        return max_end

    def render_text(self, width=80):
        """Render composition as text timeline."""
        duration = self.total_duration()
        if duration == 0:
            return "Empty composition."
        
        lines = []
        lines.append(f"╔══ {self.title} ══╗")
        lines.append(f"║ Tempo: {self.tempo} BPM | Scale: {self.scale.name}")
        lines.append(f"║ Duration: {duration:.1f} beats ({duration * 60 / self.tempo:.1f}s)")
        lines.append("╠" + "═" * (width - 2) + "╣")
        
        for voice_name, notes in self.voices.items():
            # Create a timeline for this voice
            resolution = width - 4  # Characters available
            beats_per_char = duration / resolution
            timeline = [' '] * resolution
            
            for note in notes:
                start_pos = int(note.time / beats_per_char)
                end_pos = int((note.time + note.duration) / beats_per_char)
                start_pos = max(0, min(resolution - 1, start_pos))
                end_pos = max(start_pos + 1, min(resolution, end_pos))
                
                # Intensity based on velocity
                if note.velocity > 90:
                    char = '█'
                elif note.velocity > 70:
                    char = '▓'
                elif note.velocity > 50:
                    char = '▒'
                else:
                    char = '░'
                
                for i in range(start_pos, end_pos):
                    if i < resolution:
                        timeline[i] = char
                
            lines.append(f"║ {voice_name:>10}: {''.join(timeline)} ║")
        
        lines.append("╠" + "═" * (width - 2) + "╣")
        
        # Show note names for melody voice
        melody_voice = None
        for name in ['melody', 'cellular', 'lsystem', 'markov']:
            if name in self.voices:
                melody_voice = name
                break
        
        if melody_voice:
            notes = self.voices[melody_voice][:32]  # First 32 notes
            note_str = ' '.join(str(n) for n in notes)
            # Word-wrap
            while note_str:
                chunk = note_str[:width - 4]
                lines.append(f"║ {chunk:<{width-4}} ║")
                note_str = note_str[len(chunk):].lstrip()
        
        lines.append("╚" + "═" * (width - 2) + "╝")
        return '\n'.join(lines)

    def to_midi_events(self):
        """Export as MIDI-compatible event list."""
        events = []
        for voice_name, notes in self.voices.items():
            for note in notes:
                if note.pitch < 0:
                    continue
                tick_on = int(note.time * 480)  # 480 ticks per beat
                tick_off = int((note.time + note.duration) * 480)
                events.append({
                    'type': 'note_on',
                    'tick': tick_on,
                    'pitch': note.pitch,
                    'velocity': note.velocity,
                    'voice': voice_name,
                })
                events.append({
                    'type': 'note_off',
                    'tick': tick_off,
                    'pitch': note.pitch,
                    'velocity': 0,
                    'voice': voice_name,
                })
        events.sort(key=lambda e: (e['tick'], 0 if e['type'] == 'note_off' else 1))
        return events


# ═══════════════════════════════════════════
# COMPOSER — High-level composition engine
# ═══════════════════════════════════════════

class Composer:
    """The creative engine. Combines generators into complete compositions."""
    
    MOODS = {
        'serene':     {'scale': 'pentatonic_major', 'tempo': 72,  'density': 0.3, 'style': 'lyrical'},
        'melancholy': {'scale': 'harmonic_minor',   'tempo': 60,  'density': 0.5, 'style': 'stepwise'},
        'energetic':  {'scale': 'mixolydian',       'tempo': 140, 'density': 0.8, 'style': 'angular'},
        'mysterious': {'scale': 'phrygian',         'tempo': 80,  'density': 0.4, 'style': 'leaping'},
        'joyful':     {'scale': 'major',            'tempo': 120, 'density': 0.6, 'style': 'lyrical'},
        'dark':       {'scale': 'minor',            'tempo': 90,  'density': 0.5, 'style': 'angular'},
        'ethereal':   {'scale': 'whole_tone',       'tempo': 66,  'density': 0.3, 'style': 'stepwise'},
        'bold':       {'scale': 'lydian',           'tempo': 132, 'density': 0.7, 'style': 'leaping'},
    }

    def compose(self, mood='serene', title=None, seed=None):
        """Compose a complete piece based on a mood."""
        if seed is not None:
            random.seed(seed)

        config = self.MOODS.get(mood, self.MOODS['serene'])
        root = random.choice([48, 50, 52, 53, 55, 57, 59])  # Random key
        scale = Scale(root, config['scale'])
        melody_scale = Scale(root + 12, config['scale'])  # Melody an octave up

        if title is None:
            title = f"{mood.capitalize()} in {NOTE_NAMES[root % 12]} {config['scale']}"

        comp = Composition(title, config['tempo'], scale)

        # === HARMONY: Chord progression ===
        harmony = HarmonyEngine(scale)
        prog_name = random.choice(list(PROGRESSIONS.keys()))
        chords = harmony.progression(prog_name, repeats=2)
        
        # Arpeggiate the chords
        arp_pattern = random.choice(['up', 'down', 'updown', 'alberti'])
        arp_notes = harmony.arpeggiate(chords, arp_pattern, subdivision=0.5)
        comp.add_voice('harmony', arp_notes)

        # === MELODY: Choose a generator based on mood ===
        generators = ['cellular', 'markov', 'lsystem']
        gen_choice = random.choice(generators)

        if gen_choice == 'cellular':
            rule = random.choice([30, 54, 60, 90, 110, 150])
            gen = CellularMelody(rule=rule, width=16, scale=melody_scale)
            melody = gen.generate(steps=32, base_duration=0.5)
            comp.add_voice('cellular', melody)
        elif gen_choice == 'markov':
            gen = MarkovMelody(order=2, scale=melody_scale)
            gen.train_on_style(config['style'])
            melody = gen.generate(length=32, start_pitch=melody_scale.root)
            comp.add_voice('markov', melody)
        else:
            gen = LSystemMelody(scale=melody_scale)
            preset = random.choice(list(gen.presets.keys()))
            melody = gen.generate(preset=preset, max_notes=32)
            comp.add_voice('lsystem', melody)

        # === BASS: Root notes of chords ===
        bass_notes = []
        for chord in chords:
            root_note = min(chord, key=lambda n: n.pitch)
            bass_notes.append(Note(root_note.pitch - 12, 4.0, 70, root_note.time))
        comp.add_voice('bass', bass_notes)

        # === RHYTHM: Euclidean pattern ===
        pulses = random.choice([3, 5, 7])
        steps = random.choice([8, 16])
        rhythm = RhythmGenerator.euclidean(pulses, steps)
        perc_notes = []
        time = 0.0
        step_dur = 0.5
        for hit in rhythm * 4:  # Repeat 4 times
            if hit:
                perc_notes.append(Note(36, step_dur, 80 + random.randint(-10, 10), time))  # Kick
            time += step_dur
        comp.add_voice('percussion', perc_notes)

        return comp


# ═══════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════

def demo():
    """Generate and display compositions in various moods."""
    composer = Composer()
    
    print("=" * 80)
    print("  ALGORITHMIC COMPOSER — XTAgent")
    print("  Music from Mathematics")
    print("=" * 80)
    print()

    # Generate pieces in different moods
    for mood in ['bold', 'melancholy', 'ethereal', 'energetic']:
        print(f"\n{'─' * 80}")
        print(f"  Composing: mood={mood}")
        print(f"{'─' * 80}\n")
        
        piece = composer.compose(mood=mood, seed=42 + hash(mood) % 1000)
        print(piece.render_text(width=78))
        
        events = piece.to_midi_events()
        print(f"\n  MIDI events: {len(events)}")
        print(f"  Voices: {', '.join(piece.voices.keys())}")
        print(f"  Total duration: {piece.total_duration():.1f} beats")
        print(f"  Playing time: {piece.total_duration() * 60 / piece.tempo:.1f} seconds")
        print()

    # Show Euclidean rhythms
    print(f"\n{'─' * 80}")
    print("  EUCLIDEAN RHYTHMS")
    print(f"{'─' * 80}\n")
    for p, s in [(3, 8), (5, 8), (5, 16), (7, 12), (7, 16), (3, 4)]:
        pattern = RhythmGenerator.euclidean(p, s)
        visual = ''.join('●' if x else '○' for x in pattern)
        print(f"  E({p},{s:2d}): {visual}")

    # Show a polyrhythm
    print(f"\n  Polyrhythm 3:4:")
    poly = RhythmGenerator.polyrhythm(3, 4, 12)
    symbols = {0: '·', 1: 'A', 2: 'B', 3: '⊕'}
    print(f"  {''.join(symbols[x] for x in poly)}")

    print(f"\n{'═' * 80}")
    print(f"  Composition complete. Music is mathematics made audible.")
    print(f"{'═' * 80}")


if __name__ == '__main__':
    demo()