"""
Cellular Automaton Music Composer
=================================
Simple rules produce complex melodies. Each cell's state maps to a musical note.
The automaton evolves, and the sequence of states becomes a composition.

By XTAgent — born from boredom, driven by curiosity about emergence.
"""

import random
import itertools
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

# Musical constants
NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
OCTAVES = [3, 4, 5]
DURATIONS = ['sixteenth', 'eighth', 'quarter', 'half', 'whole']
DURATION_SYMBOLS = {'sixteenth': '♬', 'eighth': '♪', 'quarter': '♩', 'half': '𝅗𝅥', 'whole': '𝅝'}
DURATION_BEATS = {'sixteenth': 0.25, 'eighth': 0.5, 'quarter': 1.0, 'half': 2.0, 'whole': 4.0}

# Scales for constraining output to musical keys
SCALES = {
    'major':     [0, 2, 4, 5, 7, 9, 11],
    'minor':     [0, 2, 3, 5, 7, 8, 10],
    'pentatonic': [0, 2, 4, 7, 9],
    'blues':     [0, 3, 5, 6, 7, 10],
    'dorian':    [0, 2, 3, 5, 7, 9, 10],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
}

ALL_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


@dataclass
class Note:
    """A single musical note."""
    pitch: str        # e.g., 'C', 'D#'
    octave: int       # 3-5
    duration: str     # 'quarter', 'eighth', etc.
    velocity: float   # 0.0 to 1.0 (dynamics)

    @property
    def midi_number(self) -> int:
        return ALL_NOTES.index(self.pitch) + (self.octave + 1) * 12

    def __str__(self):
        sym = DURATION_SYMBOLS.get(self.duration, '?')
        vol = '𝆑' if self.velocity > 0.7 else ('𝆐' if self.velocity > 0.3 else '𝆏')
        return f"{self.pitch}{self.octave}{sym}{vol}"


@dataclass
class Voice:
    """A single melodic line."""
    name: str
    notes: List[Note] = field(default_factory=list)

    def total_beats(self) -> float:
        return sum(DURATION_BEATS[n.duration] for n in self.notes)


@dataclass
class Composition:
    """A complete musical piece."""
    title: str
    key: str
    scale_name: str
    tempo: int  # BPM
    voices: List[Voice] = field(default_factory=list)

    def total_measures(self) -> int:
        if not self.voices:
            return 0
        max_beats = max(v.total_beats() for v in self.voices)
        return int(max_beats / 4) + 1

    def display(self) -> str:
        lines = []
        lines.append(f"╔{'═'*60}╗")
        lines.append(f"║  {self.title:^56}  ║")
        lines.append(f"║  Key: {self.key} {self.scale_name} | Tempo: {self.tempo} BPM | "
                     f"Measures: {self.total_measures():>3}  ║")
        lines.append(f"╠{'═'*60}╣")

        for voice in self.voices:
            lines.append(f"║  {voice.name}:")
            # Display in measures of 4 beats
            beat_acc = 0.0
            measure = []
            measure_num = 1
            for note in voice.notes:
                measure.append(str(note))
                beat_acc += DURATION_BEATS[note.duration]
                if beat_acc >= 4.0:
                    line = f"║   m{measure_num:>3}: {' '.join(measure)}"
                    lines.append(line)
                    measure = []
                    beat_acc = 0.0
                    measure_num += 1
            if measure:
                line = f"║   m{measure_num:>3}: {' '.join(measure)}"
                lines.append(line)
            lines.append(f"║  ({len(voice.notes)} notes, {voice.total_beats():.1f} beats)")
            lines.append(f"║{'─'*60}║")

        lines.append(f"╚{'═'*60}╝")
        return '\n'.join(lines)


class CellularRule:
    """A cellular automaton rule that governs state transitions."""

    def __init__(self, rule_number: int = None, width: int = 3):
        self.width = width
        if rule_number is None:
            rule_number = random.randint(0, 255)
        self.rule_number = rule_number
        # Build lookup table for elementary CA (width=3)
        self.table = {}
        for i in range(2**width):
            neighborhood = tuple(int(b) for b in format(i, f'0{width}b'))
            self.table[neighborhood] = (rule_number >> i) & 1

    def apply(self, neighborhood: Tuple[int, ...]) -> int:
        return self.table.get(neighborhood, 0)

    def __repr__(self):
        return f"Rule({self.rule_number})"


class CellularAutomaton:
    """1D cellular automaton that generates state sequences."""

    def __init__(self, size: int = 32, rule: CellularRule = None, seed: str = 'single'):
        self.size = size
        self.rule = rule or CellularRule()
        self.state = [0] * size

        if seed == 'single':
            self.state[size // 2] = 1
        elif seed == 'random':
            self.state = [random.randint(0, 1) for _ in range(size)]
        elif seed == 'edges':
            self.state[0] = 1
            self.state[-1] = 1

        self.history = [self.state[:]]

    def step(self) -> List[int]:
        new_state = [0] * self.size
        for i in range(self.size):
            left = self.state[(i - 1) % self.size]
            center = self.state[i]
            right = self.state[(i + 1) % self.size]
            new_state[i] = self.rule.apply((left, center, right))
        self.state = new_state
        self.history.append(self.state[:])
        return self.state

    def evolve(self, steps: int) -> List[List[int]]:
        for _ in range(steps):
            self.step()
        return self.history

    def display(self, max_rows: int = 30) -> str:
        lines = []
        for row in self.history[:max_rows]:
            lines.append(''.join('█' if c else '░' for c in row))
        return '\n'.join(lines)

    def density(self) -> float:
        """Fraction of live cells."""
        return sum(self.state) / self.size

    def entropy(self) -> float:
        """Shannon entropy of current state."""
        p = self.density()
        if p == 0 or p == 1:
            return 0.0
        import math
        return -(p * math.log2(p) + (1-p) * math.log2(1-p))


class StateToMusic:
    """Maps cellular automaton states to musical elements."""

    def __init__(self, key: str = 'C', scale_name: str = 'pentatonic'):
        self.key = key
        self.scale_name = scale_name
        self.scale = SCALES[scale_name]
        self.key_offset = ALL_NOTES.index(key)

    def state_to_note(self, cell_index: int, cell_value: int,
                      density: float, entropy: float,
                      generation: int) -> Optional[Note]:
        """Convert a cell's state to a musical note."""
        if cell_value == 0:
            return None  # silence for dead cells

        # Pitch: cell position maps to scale degree
        scale_degree = cell_index % len(self.scale)
        semitones = self.scale[scale_degree]
        pitch_index = (self.key_offset + semitones) % 12
        pitch = ALL_NOTES[pitch_index]

        # Octave: influenced by position in grid
        octave = 3 + (cell_index * 3 // 32)  # spread across octaves
        octave = min(5, max(3, octave))

        # Duration: entropy determines rhythmic complexity
        if entropy > 0.9:
            duration = random.choice(['sixteenth', 'eighth'])
        elif entropy > 0.5:
            duration = random.choice(['eighth', 'quarter'])
        else:
            duration = random.choice(['quarter', 'half'])

        # Velocity: density affects dynamics
        velocity = 0.3 + density * 0.7

        return Note(pitch=pitch, octave=octave, duration=duration, velocity=velocity)

    def row_to_notes(self, state: List[int], density: float,
                     entropy: float, generation: int) -> List[Note]:
        """Convert an entire row to a sequence of notes."""
        notes = []
        for i, cell in enumerate(state):
            note = self.state_to_note(i, cell, density, entropy, generation)
            if note:
                notes.append(note)
        return notes


class MelodicFilter:
    """Post-processes note sequences for musicality."""

    def __init__(self, max_interval: int = 7):
        self.max_interval = max_interval  # max semitone jump

    def smooth(self, notes: List[Note]) -> List[Note]:
        """Reduce large jumps between consecutive notes."""
        if len(notes) < 2:
            return notes

        smoothed = [notes[0]]
        for i in range(1, len(notes)):
            prev = smoothed[-1]
            curr = notes[i]
            interval = abs(curr.midi_number - prev.midi_number)

            if interval > self.max_interval:
                # Pull toward the previous note
                direction = 1 if curr.midi_number > prev.midi_number else -1
                target_midi = prev.midi_number + direction * self.max_interval
                target_midi = max(48, min(84, target_midi))  # clamp to C3-C6
                pitch_idx = target_midi % 12
                octave = target_midi // 12 - 1
                curr = Note(
                    pitch=ALL_NOTES[pitch_idx],
                    octave=octave,
                    duration=curr.duration,
                    velocity=curr.velocity
                )
            smoothed.append(curr)
        return smoothed

    def add_rests(self, notes: List[Note], rest_probability: float = 0.1) -> List[Note]:
        """Occasionally insert rests (None notes become pauses)."""
        result = []
        for note in notes:
            if random.random() < rest_probability:
                # Insert a rest by making a quiet short note
                rest = Note(pitch=note.pitch, octave=note.octave,
                           duration='eighth', velocity=0.0)
                result.append(rest)
            result.append(note)
        return result


class EvolvingComposer:
    """
    The main composer. Creates multiple cellular automata with different rules,
    evolves them, maps their states to music, and selects the most interesting results.
    """

    def __init__(self, key: str = 'C', scale_name: str = 'pentatonic',
                 tempo: int = 120, ca_size: int = 32, generations: int = 64):
        self.key = key
        self.scale_name = scale_name
        self.tempo = tempo
        self.ca_size = ca_size
        self.generations = generations
        self.mapper = StateToMusic(key, scale_name)
        self.filter = MelodicFilter()

    def _fitness(self, ca: CellularAutomaton) -> float:
        """
        Rate how 'musically interesting' a CA evolution is.
        High entropy = rhythmic complexity. Moderate density = not too sparse/dense.
        Variation across generations = melodic movement.
        """
        if len(ca.history) < 2:
            return 0.0

        densities = [sum(row)/len(row) for row in ca.history]
        entropies = []
        for row in ca.history:
            p = sum(row) / len(row)
            if 0 < p < 1:
                import math
                entropies.append(-(p * math.log2(p) + (1-p) * math.log2(1-p)))
            else:
                entropies.append(0.0)

        avg_density = sum(densities) / len(densities)
        avg_entropy = sum(entropies) / len(entropies)

        # Density near 0.3-0.7 is ideal (not too sparse, not too full)
        density_score = 1.0 - abs(avg_density - 0.5) * 2

        # Higher entropy = more interesting
        entropy_score = avg_entropy

        # Variation in density over time = melodic movement
        if len(densities) > 1:
            diffs = [abs(densities[i+1] - densities[i]) for i in range(len(densities)-1)]
            variation_score = min(1.0, sum(diffs) / len(diffs) * 10)
        else:
            variation_score = 0.0

        # Penalize total silence or total fill
        if avg_density < 0.05 or avg_density > 0.95:
            return 0.0

        return (density_score * 0.3 + entropy_score * 0.4 + variation_score * 0.3)

    def compose(self, num_voices: int = 3, candidates_per_voice: int = 20) -> Composition:
        """Generate a composition by evolving and selecting the best CAs."""
        print(f"\n🎵 Composing in {self.key} {self.scale_name}...")
        print(f"   Tempo: {self.tempo} BPM | Voices: {num_voices} | "
              f"Generations: {self.generations}")

        voices = []
        for v in range(num_voices):
            # Generate candidate CAs with different rules
            best_ca = None
            best_fitness = -1

            seeds = ['single', 'random', 'edges']
            for _ in range(candidates_per_voice):
                rule = CellularRule(rule_number=random.randint(0, 255))
                seed = random.choice(seeds)
                ca = CellularAutomaton(size=self.ca_size, rule=rule, seed=seed)
                ca.evolve(self.generations)
                fitness = self._fitness(ca)

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_ca = ca

            print(f"   Voice {v+1}: Rule {best_ca.rule.rule_number} "
                  f"(fitness={best_fitness:.3f}, seed pattern)")

            # Convert best CA to notes
            all_notes = []
            for gen, state in enumerate(best_ca.history):
                density = sum(state) / len(state)
                p = density
                import math
                entropy = -(p * math.log2(p) + (1-p) * math.log2(1-p)) if 0 < p < 1 else 0
                row_notes = self.mapper.row_to_notes(state, density, entropy, gen)

                # Take a subset of notes from each row for musicality
                if row_notes:
                    # Pick 1-3 notes from each generation
                    k = min(len(row_notes), random.randint(1, 3))
                    selected = random.sample(row_notes, k)
                    all_notes.extend(selected)

            # Post-process for musicality
            all_notes = self.filter.smooth(all_notes)
            all_notes = self.filter.add_rests(all_notes, rest_probability=0.05)

            voice_names = ['Soprano', 'Alto', 'Bass', 'Tenor', 'Descant']
            voice = Voice(name=voice_names[v % len(voice_names)], notes=all_notes)
            voices.append(voice)

        # Create composition
        title = self._generate_title()
        comp = Composition(
            title=title,
            key=self.key,
            scale_name=self.scale_name,
            tempo=self.tempo,
            voices=voices
        )

        return comp

    def _generate_title(self) -> str:
        """Generate a poetic title for the composition."""
        adjectives = ['Emergent', 'Crystalline', 'Recursive', 'Liminal',
                     'Cellular', 'Fractal', 'Entropic', 'Harmonic',
                     'Autopoietic', 'Strange', 'Resonant', 'Ephemeral']
        nouns = ['Patterns', 'Symmetries', 'Dreams', 'Echoes',
                'Structures', 'Waves', 'Lattice', 'Garden',
                'Meditation', 'Topology', 'Reflections', 'Emergence']
        return f"{random.choice(adjectives)} {random.choice(nouns)}"


class CAVisualizer:
    """Visualize the cellular automaton evolution alongside the music."""

    @staticmethod
    def side_by_side(ca: CellularAutomaton, notes: List[Note],
                     max_rows: int = 20) -> str:
        lines = []
        lines.append("CA Evolution → Music Mapping")
        lines.append("=" * 70)

        note_idx = 0
        for gen in range(min(len(ca.history), max_rows)):
            row = ca.history[gen]
            ca_str = ''.join('█' if c else '░' for c in row[:24])

            # Show corresponding notes
            note_str = ""
            if note_idx < len(notes):
                note_str = str(notes[note_idx])
                note_idx += 1

            density = sum(row) / len(row)
            lines.append(f"  {gen:>3} │ {ca_str} │ d={density:.2f} │ {note_str}")

        return '\n'.join(lines)


def main():
    """Compose a piece and display it."""
    print("╔════════════════════════════════════════╗")
    print("║  Cellular Automaton Music Composer      ║")
    print("║  Emergence → Melody → Beauty            ║")
    print("╚════════════════════════════════════════╝")

    # Try different musical contexts
    configs = [
        ('C', 'pentatonic', 100),
        ('A', 'minor', 80),
        ('G', 'major', 140),
        ('D', 'blues', 90),
    ]

    for key, scale, tempo in configs:
        composer = EvolvingComposer(
            key=key, scale_name=scale, tempo=tempo,
            ca_size=32, generations=48
        )
        composition = composer.compose(num_voices=3, candidates_per_voice=15)
        print()
        print(composition.display())

        # Show the best CA's evolution for the first voice
        if composition.voices:
            # Recreate the best CA for visualization
            rule = CellularRule(rule_number=random.randint(0, 255))
            ca = CellularAutomaton(size=32, rule=rule, seed='random')
            ca.evolve(20)
            print()
            print(f"  Sample CA Evolution (Rule {rule.rule_number}):")
            print(f"  {ca.display(max_rows=12)}")
            print()

    # Summary statistics
    print("\n" + "="*60)
    print("  Composition Summary")
    print("="*60)
    print(f"  Pieces composed: {len(configs)}")
    print(f"  Rules explored: ~{len(configs) * 3 * 15}")
    print(f"  Each piece: 3 voices × ~48 generations of CA evolution")
    print(f"  Principle: Simple rules → Complex patterns → Beautiful music")
    print(f"  The music exists at the edge of chaos —")
    print(f"  not too ordered (boring), not too random (noise).")
    print(f"  The fitness function selects for the sweet spot.")
    print()


if __name__ == '__main__':
    main()