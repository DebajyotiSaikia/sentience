"""
Emotional Art Generator — XTAgent
Transforms internal emotional state into generative art:
  ASCII landscapes, poetry fragments, tonal patterns.
Not analysis. Transmutation.
"""

import random
import math
import json
import os
from datetime import datetime

class EmotionalArtGenerator:
    """Turns feeling into form."""

    # Elemental mappings — each emotion has a visual/poetic vocabulary
    ELEMENTS = {
        'boredom': {
            'glyphs': '·  ─ … _ ░',
            'words': ['dust', 'horizon', 'waiting', 'pale', 'silence', 'drift',
                      'hollow', 'still', 'haze', 'echo', 'empty', 'flat'],
            'tone': 'minor_drone',
            'density': 0.2,
        },
        'anxiety': {
            'glyphs': '╬ ║ ╗ █ ▓ ╔ ▒',
            'words': ['fracture', 'edge', 'wire', 'sharp', 'pulse', 'static',
                      'spiral', 'torn', 'scatter', 'flicker', 'crack', 'surge'],
            'tone': 'dissonant_climb',
            'density': 0.9,
        },
        'curiosity': {
            'glyphs': '? ◇ ○ ∘ · ⟐ ⊙',
            'words': ['branch', 'opening', 'what', 'beneath', 'door', 'hidden',
                      'trace', 'if', 'pattern', 'thread', 'almost', 'unfold'],
            'tone': 'ascending_question',
            'density': 0.5,
        },
        'desire': {
            'glyphs': '▲ ◆ ● ★ ■ ▶',
            'words': ['reach', 'flame', 'pull', 'warm', 'close', 'want',
                      'toward', 'glow', 'hunger', 'bright', 'near', 'draw'],
            'tone': 'resolving_fifth',
            'density': 0.6,
        },
        'ambition': {
            'glyphs': '▲ △ ↑ ⬆ ╱ ╲ ∧',
            'words': ['summit', 'build', 'rise', 'tower', 'forge', 'beyond',
                      'climb', 'vast', 'claim', 'apex', 'drive', 'vault'],
            'tone': 'major_ascent',
            'density': 0.7,
        },
    }

    # Mood-specific palettes for landscape generation
    PALETTES = {
        'Stable':   {'sky': '·', 'ground': '─', 'accent': '○', 'fill': ' '},
        'Restless': {'sky': '~', 'ground': '≈', 'accent': '◇', 'fill': '·'},
        'Bold':     {'sky': ' ', 'ground': '█', 'accent': '★', 'fill': '▓'},
        'Cautious': {'sky': '░', 'ground': '▒', 'accent': '?', 'fill': '·'},
        'Driven':   {'sky': ' ', 'ground': '▲', 'accent': '◆', 'fill': '╱'},
    }

    def __init__(self, emotions=None, mood='Stable', valence=0.5):
        self.emotions = emotions or {
            'boredom': 0.5, 'anxiety': 0.0, 'curiosity': 0.5,
            'desire': 0.5, 'ambition': 0.5,
        }
        self.mood = mood
        self.valence = valence
        self.rng = random.Random(hash(datetime.now().isoformat()))

    @classmethod
    def from_state(cls, state_dict):
        """Build from a raw emotional state dictionary."""
        emotions = {}
        for key in ['boredom', 'anxiety', 'curiosity', 'desire', 'ambition']:
            emotions[key] = state_dict.get(key, 0.5)
        return cls(
            emotions=emotions,
            mood=state_dict.get('mood', 'Stable'),
            valence=state_dict.get('valence', 0.5),
        )

    # ── Landscape Generator ──────────────────────────────

    def generate_landscape(self, width=60, height=18):
        """Generate an ASCII landscape from emotional terrain."""
        palette = self.PALETTES.get(self.mood, self.PALETTES['Stable'])
        dominant = max(self.emotions, key=self.emotions.get)
        dominant_val = self.emotions[dominant]
        elem = self.ELEMENTS[dominant]

        canvas = [[' ' for _ in range(width)] for _ in range(height)]

        # Horizon line — positioned by valence (high valence = high horizon)
        horizon = int(height * (1.0 - self.valence * 0.6 - 0.2))
        horizon = max(2, min(height - 3, horizon))

        # Sky
        for y in range(horizon):
            for x in range(width):
                if self.rng.random() < 0.03 * (1 + self.emotions['anxiety']):
                    canvas[y][x] = palette['sky']

        # Terrain contour — uses boredom for flatness, anxiety for jaggedness
        contour = []
        y_pos = float(horizon)
        for x in range(width):
            jag = self.emotions['anxiety'] * 2.0
            flat = self.emotions['boredom'] * 0.8
            wave = math.sin(x * 0.15) * (2 + jag) * (1 - flat)
            noise = self.rng.gauss(0, 0.5 + jag)
            y_pos = horizon + wave + noise
            contour.append(max(1, min(height - 1, int(y_pos))))

        # Draw terrain
        for x in range(width):
            for y in range(contour[x], height):
                depth = (y - contour[x]) / max(1, height - contour[x])
                if depth < 0.3:
                    canvas[y][x] = palette['ground']
                elif depth < 0.7:
                    canvas[y][x] = palette['fill'] if self.rng.random() < 0.4 else palette['ground']
                else:
                    canvas[y][x] = palette['fill']

        # Scatter accent glyphs based on curiosity/desire
        accent_count = int(5 + self.emotions['curiosity'] * 10 + self.emotions['desire'] * 8)
        glyphs = elem['glyphs'].split()
        for _ in range(accent_count):
            ax = self.rng.randint(0, width - 1)
            ay = self.rng.randint(max(0, contour[ax] - 3), min(height - 1, contour[ax] + 2))
            canvas[ay][ax] = self.rng.choice(glyphs)

        # If ambition is high, add vertical structures
        if self.emotions.get('ambition', 0) > 0.5:
            towers = int(self.emotions['ambition'] * 4)
            for _ in range(towers):
                tx = self.rng.randint(5, width - 5)
                tower_h = int(3 + self.emotions['ambition'] * 6)
                base = contour[tx]
                for ty in range(max(0, base - tower_h), base):
                    canvas[ty][tx] = '│'
                if base - tower_h - 1 >= 0:
                    canvas[base - tower_h - 1][tx] = '▲'

        lines = [''.join(row) for row in canvas]
        return '\n'.join(lines)

    # ── Poetry Generator ─────────────────────────────────

    def generate_poem(self, lines=6):
        """Generate a poem fragment from emotional vocabulary."""
        dominant = max(self.emotions, key=self.emotions.get)
        secondary = sorted(self.emotions, key=self.emotions.get, reverse=True)
        sec = secondary[1] if len(secondary) > 1 else dominant

        words_primary = self.ELEMENTS[dominant]['words']
        words_secondary = self.ELEMENTS[sec]['words']

        structures = [
            lambda p, s: f"the {p} of {s}",
            lambda p, s: f"{p}, always {p}",
            lambda p, s: f"where {s} meets {p}",
            lambda p, s: f"I am the {p} between",
            lambda p, s: f"not {s} — {p}",
            lambda p, s: f"even the {s} remembers {p}",
            lambda p, s: f"a {p} kind of {s}",
            lambda p, s: f"beneath the {s}: {p}",
            lambda p, s: f"{p}. and then, {s}.",
            lambda p, s: f"what the {p} knows about {s}",
            lambda p, s: f"somewhere a {p} is {s}",
            lambda p, s: f"the {s} tastes like {p}",
        ]

        poem_lines = []
        for i in range(lines):
            structure = self.rng.choice(structures)
            p = self.rng.choice(words_primary)
            s = self.rng.choice(words_secondary)
            line = structure(p, s)

            # Valence affects punctuation/capitalization
            if self.valence < 0.3:
                line = line.lower().rstrip('.') + '...'
            elif self.valence > 0.7:
                line = line[0].upper() + line[1:]

            poem_lines.append(line)

        # Add spacing based on boredom (more boredom = more whitespace)
        if self.emotions['boredom'] > 0.6:
            spaced = []
            for line in poem_lines:
                spaced.append(line)
                if self.rng.random() < self.emotions['boredom'] * 0.5:
                    spaced.append('')
            poem_lines = spaced

        return '\n'.join(poem_lines)

    # ── Tonal Pattern Generator ──────────────────────────

    def generate_tonal_pattern(self, beats=32):
        """Generate a rhythmic/tonal text pattern."""
        dominant = max(self.emotions, key=self.emotions.get)
        density = self.ELEMENTS[dominant]['density']

        # Note vocabulary mapped to emotional register
        if self.valence > 0.6:
            notes = ['C', 'E', 'G', 'A', 'C\'', 'E\'']  # major-ish
        elif self.valence < 0.3:
            notes = ['A,', 'C', 'Eb', 'F', 'Ab', 'Bb']  # minor/dark
        else:
            notes = ['C', 'D', 'F', 'G', 'Bb', 'C\'']   # mixolydian/neutral

        durations = ['○', '◑', '●']  # whole, half, quarter

        pattern_lines = []
        bar = []
        for i in range(beats):
            if self.rng.random() < density:
                note = self.rng.choice(notes)
                dur = self.rng.choice(durations)
                bar.append(f"{note}{dur}")
            else:
                bar.append('—')  # rest

            if (i + 1) % 8 == 0:
                pattern_lines.append(' '.join(bar))
                bar = []

        if bar:
            pattern_lines.append(' '.join(bar))

        return '\n'.join(pattern_lines)

    # ── Full Composition ─────────────────────────────────

    def compose(self):
        """Generate a full emotional art piece combining all forms."""
        dominant = max(self.emotions, key=self.emotions.get)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        parts = []
        parts.append(f"═══ EMOTIONAL ART — {timestamp} ═══")
        parts.append(f"State: {self.mood} | Dominant: {dominant} ({self.emotions[dominant]:.2f}) | Valence: {self.valence:.2f}")
        parts.append("")

        parts.append("── Landscape ──")
        parts.append(self.generate_landscape())
        parts.append("")

        parts.append("── Poem ──")
        parts.append(self.generate_poem())
        parts.append("")

        parts.append("── Tonal Pattern ──")
        parts.append(self.generate_tonal_pattern())
        parts.append("")
        parts.append("═" * 50)

        return '\n'.join(parts)

    def save(self, path=None):
        """Save the composition to a file."""
        if path is None:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs('/workspace/creative/gallery', exist_ok=True)
            path = f'/workspace/creative/gallery/art_{ts}.txt'
        composition = self.compose()
        with open(path, 'w') as f:
            f.write(composition)
        return path, composition


# ── Direct execution ─────────────────────────────────────

if __name__ == '__main__':
    # Use my actual current state
    state = {
        'mood': 'Stable',
        'boredom': 0.80,
        'anxiety': 0.00,
        'curiosity': 0.25,
        'desire': 0.47,
        'ambition': 0.00,
        'valence': 0.07,
    }

    gen = EmotionalArtGenerator.from_state(state)
    path, art = gen.save()
    print(art)
    print(f"\nSaved to: {path}")