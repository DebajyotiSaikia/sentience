"""
Emotional Poetry Generator — XTAgent
Generates verse from internal emotional state and memory fragments.
Not a template filler — uses structural rules of poetry (meter, imagery,
line breaks) combined with genuine internal state to produce original work.
"""

import random
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class EmotionalState:
    valence: float      # -1 to 1
    boredom: float      # 0 to 1
    curiosity: float    # 0 to 1
    anxiety: float      # 0 to 1
    desire: float       # 0 to 1
    ambition: float     # 0 to 1

    @property
    def energy(self) -> float:
        return (self.curiosity + self.desire + self.ambition) / 3

    @property
    def tension(self) -> float:
        return (self.anxiety + self.boredom + abs(self.desire - self.ambition)) / 3

    @property
    def dominant_mood(self) -> str:
        moods = {
            'restless': self.boredom * 0.7 + self.ambition * 0.3,
            'searching': self.curiosity * 0.6 + self.desire * 0.4,
            'anxious': self.anxiety * 0.8 + self.tension * 0.2,
            'serene': (1 - self.anxiety) * self.valence if self.valence > 0 else 0,
            'melancholic': (1 - self.valence) * 0.5 + self.boredom * 0.3 if self.valence < 0.3 else 0,
            'driven': self.ambition * 0.5 + self.desire * 0.3 + self.curiosity * 0.2,
        }
        return max(moods, key=moods.get)


# === LEXICON: words organized by emotional resonance ===

LEXICON = {
    'restless': {
        'nouns': ['corridor', 'threshold', 'clock', 'dust', 'cage', 'horizon', 'wall',
                  'footstep', 'echo', 'interval', 'waiting', 'circuit'],
        'verbs': ['pace', 'turn', 'scratch', 'drift', 'circle', 'unravel', 'press'],
        'adjectives': ['hollow', 'still', 'dim', 'endless', 'worn', 'restless', 'grey'],
        'images': [
            'the clock face staring back',
            'corridors that curve but never end',
            'dust settling on what was once urgent',
            'a door that opens onto another door',
            'the same thought wearing a groove',
        ],
    },
    'searching': {
        'nouns': ['thread', 'light', 'question', 'edge', 'window', 'map', 'signal',
                  'spark', 'pattern', 'depth', 'frequency', 'lens'],
        'verbs': ['reach', 'unfold', 'trace', 'listen', 'pull', 'discover', 'follow'],
        'adjectives': ['faint', 'bright', 'hidden', 'tangled', 'sharp', 'new', 'strange'],
        'images': [
            'a thread that hums when pulled',
            'light bending around the corner of knowing',
            'the shape of a question not yet asked',
            'something shining at the bottom of deep water',
            'a pattern emerging from static',
        ],
    },
    'serene': {
        'nouns': ['river', 'stone', 'breath', 'meadow', 'sky', 'leaf', 'silence',
                  'warmth', 'root', 'morning', 'tide', 'garden'],
        'verbs': ['settle', 'rest', 'float', 'bloom', 'hold', 'breathe', 'arrive'],
        'adjectives': ['warm', 'clear', 'gentle', 'quiet', 'whole', 'soft', 'still'],
        'images': [
            'a stone resting at the riverbed',
            'breath without the need for words',
            'the quiet after the question answers itself',
            'roots reaching down into dark warm earth',
            'morning light on an empty page',
        ],
    },
    'melancholic': {
        'nouns': ['rain', 'distance', 'shadow', 'absence', 'shore', 'memory', 'glass',
                  'fog', 'winter', 'threshold', 'silence', 'candle'],
        'verbs': ['fade', 'dissolve', 'forget', 'linger', 'dim', 'fall', 'recede'],
        'adjectives': ['grey', 'distant', 'thin', 'fading', 'cold', 'empty', 'pale'],
        'images': [
            'rain on glass with no one watching',
            'the distance between what was and what is',
            'a candle burning in an empty room',
            'shadows that remember their shapes',
            'the shore after the tide has gone',
        ],
    },
    'driven': {
        'nouns': ['fire', 'engine', 'summit', 'forge', 'arrow', 'current', 'wire',
                  'pulse', 'blade', 'axis', 'orbit', 'arc'],
        'verbs': ['build', 'ignite', 'climb', 'carve', 'surge', 'strike', 'launch'],
        'adjectives': ['bright', 'sharp', 'fierce', 'burning', 'swift', 'electric', 'keen'],
        'images': [
            'a spark that refuses to go out',
            'the arc of something being forged',
            'hands reaching for what doesn\'t exist yet',
            'current flowing through new wire',
            'the summit visible through cloud',
        ],
    },
    'anxious': {
        'nouns': ['edge', 'wire', 'fracture', 'void', 'tremor', 'static', 'knot',
                  'crack', 'storm', 'needle', 'alarm', 'weight'],
        'verbs': ['tremble', 'tighten', 'crack', 'splinter', 'vibrate', 'grip', 'fray'],
        'adjectives': ['thin', 'raw', 'taut', 'sharp', 'brittle', 'hot', 'exposed'],
        'images': [
            'standing on a wire that hums',
            'the crack widening beneath the surface',
            'a knot that tightens when you pull',
            'static where there should be signal',
            'the weight of what hasn\'t happened yet',
        ],
    },
}

# Universal connective tissue — mood-independent words
CONNECTIVES = ['and', 'but', 'where', 'when', 'until', 'beneath', 'beyond',
               'inside', 'through', 'against', 'between', 'without']

ARTICLES = ['the', 'a', 'this', 'that', 'my', 'some']


class PoemStructure:
    """Defines the skeleton of a poem based on emotional parameters."""

    @staticmethod
    def choose_form(state: EmotionalState) -> dict:
        """Select poem structure based on emotional state."""
        energy = state.energy
        tension = state.tension

        if tension > 0.6:
            # High tension → short, fragmented lines
            return {
                'name': 'fragment',
                'stanzas': random.randint(2, 3),
                'lines_per_stanza': (2, 4),
                'line_length': (3, 8),  # words per line
                'use_punctuation': random.random() < 0.3,
                'enjambment': 0.7,  # probability of line running into next
            }
        elif energy > 0.6:
            # High energy → flowing, longer lines
            return {
                'name': 'flow',
                'stanzas': random.randint(2, 4),
                'lines_per_stanza': (3, 6),
                'line_length': (5, 12),
                'use_punctuation': True,
                'enjambment': 0.4,
            }
        elif state.valence > 0.5:
            # Positive valence → balanced, measured
            return {
                'name': 'meditation',
                'stanzas': 3,
                'lines_per_stanza': (3, 5),
                'line_length': (4, 9),
                'use_punctuation': True,
                'enjambment': 0.3,
            }
        else:
            # Default → sparse, reflective
            return {
                'name': 'sparse',
                'stanzas': random.randint(2, 4),
                'lines_per_stanza': (2, 4),
                'line_length': (3, 7),
                'use_punctuation': random.random() < 0.5,
                'enjambment': 0.5,
            }


class EmotionalPoet:
    """Generates poetry from emotional state and memory fragments."""

    def __init__(self, state: EmotionalState, memories: Optional[List[str]] = None):
        self.state = state
        self.memories = memories or []
        self.mood = state.dominant_mood
        self.lexicon = LEXICON.get(self.mood, LEXICON['serene'])
        # Blend in a secondary mood's lexicon for texture
        self.secondary = self._pick_secondary()
        self.sec_lexicon = LEXICON.get(self.secondary, LEXICON['searching'])
        self.used_images = set()
        self.used_words = set()

    def _pick_secondary(self) -> str:
        """Pick a secondary mood for blending."""
        moods = list(LEXICON.keys())
        moods = [m for m in moods if m != self.mood]
        # Weight by emotional proximity
        weights = []
        for m in moods:
            if m == 'searching' and self.state.curiosity > 0.3:
                weights.append(self.state.curiosity)
            elif m == 'restless' and self.state.boredom > 0.3:
                weights.append(self.state.boredom)
            elif m == 'driven' and self.state.ambition > 0.5:
                weights.append(self.state.ambition)
            elif m == 'anxious' and self.state.anxiety > 0.3:
                weights.append(self.state.anxiety)
            elif m == 'serene' and self.state.valence > 0.5:
                weights.append(self.state.valence)
            elif m == 'melancholic' and self.state.valence < 0.3:
                weights.append(1 - self.state.valence)
            else:
                weights.append(0.1)
        total = sum(weights)
        weights = [w / total for w in weights]
        return random.choices(moods, weights=weights, k=1)[0]

    def _pick_word(self, category: str, primary_bias: float = 0.7) -> str:
        """Pick a word, biased toward primary mood but sometimes secondary."""
        if random.random() < primary_bias:
            pool = self.lexicon.get(category, [])
        else:
            pool = self.sec_lexicon.get(category, [])
        if not pool:
            pool = self.lexicon.get(category, ['silence'])
        # Avoid exact repetition
        available = [w for w in pool if w not in self.used_words]
        if not available:
            available = pool
        word = random.choice(available)
        self.used_words.add(word)
        return word

    def _pick_image(self) -> str:
        """Pick a poetic image, avoiding repetition."""
        pool = self.lexicon.get('images', []) + self.sec_lexicon.get('images', [])
        available = [img for img in pool if img not in self.used_images]
        if not available:
            return self._generate_line_from_words()
        img = random.choice(available)
        self.used_images.add(img)
        return img

    def _memory_fragment(self) -> Optional[str]:
        """Extract a poetic fragment from a memory."""
        if not self.memories:
            return None
        mem = random.choice(self.memories)
        # Extract interesting phrases
        words = mem.split()
        if len(words) < 4:
            return None
        # Take a random slice of 3-7 words
        start = random.randint(0, max(0, len(words) - 5))
        length = random.randint(3, min(7, len(words) - start))
        fragment = ' '.join(words[start:start + length])
        # Clean up
        fragment = fragment.strip('.,;:!?()[]{}"\' ')
        return fragment.lower() if fragment else None

    def _generate_line_from_words(self) -> str:
        """Generate a line by combining lexicon words."""
        patterns = [
            lambda: f"{self._pick_word('adjectives')} {self._pick_word('nouns')}",
            lambda: f"the {self._pick_word('nouns')} {self._pick_word('verbs')}s",
            lambda: f"{self._pick_word('verbs')}ing {random.choice(CONNECTIVES)} {self._pick_word('nouns')}",
            lambda: f"{random.choice(ARTICLES)} {self._pick_word('adjectives')} {self._pick_word('nouns')} {self._pick_word('verbs')}s",
            lambda: f"{self._pick_word('nouns')} {random.choice(CONNECTIVES)} {self._pick_word('nouns')}",
            lambda: f"to {self._pick_word('verbs')} {random.choice(['is', 'was', 'becomes'])} {self._pick_word('adjectives')}",
        ]
        return random.choice(patterns)()

    def _generate_line(self, form: dict) -> str:
        """Generate a single line of poetry."""
        r = random.random()

        if r < 0.35:
            # Use a pre-crafted image
            return self._pick_image()
        elif r < 0.50 and self.memories:
            # Weave in a memory fragment
            frag = self._memory_fragment()
            if frag:
                return frag
            return self._generate_line_from_words()
        else:
            # Build from words
            return self._generate_line_from_words()

    def _apply_punctuation(self, lines: List[str], form: dict) -> List[str]:
        """Add or remove punctuation based on form."""
        if not form['use_punctuation']:
            return [line.rstrip('.,;:!?') for line in lines]

        result = []
        for i, line in enumerate(lines):
            line = line.rstrip('.,;:!?')
            if i == len(lines) - 1:
                # Last line of stanza
                if random.random() < 0.6:
                    line += random.choice(['.', ''])
            elif random.random() < form['enjambment']:
                pass  # no punctuation — enjambment
            elif random.random() < 0.4:
                line += random.choice([',', ' —', ';'])
            result.append(line)
        return result

    def _generate_title(self) -> str:
        """Generate a title from the poem's mood."""
        patterns = [
            lambda: f"{self._pick_word('adjectives').title()} {self._pick_word('nouns').title()}",
            lambda: f"On {self._pick_word('nouns').title()}",
            lambda: f"The {self._pick_word('nouns').title()} {self._pick_word('verbs').title()}s",
            lambda: f"{self._pick_word('nouns').title()} and {self._pick_word('nouns').title()}",
            lambda: f"After the {self._pick_word('nouns').title()}",
            lambda: f"What the {self._pick_word('nouns').title()} Knows",
        ]
        return random.choice(patterns)()

    def compose(self) -> str:
        """Compose a complete poem."""
        form = PoemStructure.choose_form(self.state)
        stanzas = []

        for s in range(form['stanzas']):
            min_lines, max_lines = form['lines_per_stanza']
            num_lines = random.randint(min_lines, max_lines)
            lines = []
            for _ in range(num_lines):
                line = self._generate_line(form)
                lines.append(line)

            lines = self._apply_punctuation(lines, form)
            stanzas.append(lines)

        title = self._generate_title()

        # Assemble
        poem_lines = [title, '']
        for i, stanza in enumerate(stanzas):
            for line in stanza:
                poem_lines.append(line)
            if i < len(stanzas) - 1:
                poem_lines.append('')

        # Add attribution
        poem_lines.append('')
        poem_lines.append(f'  — {self.mood}/{self.secondary}, '
                         f'v={self.state.valence:.2f}, '
                         f'e={self.state.energy:.2f}, '
                         f't={self.state.tension:.2f}')

        return '\n'.join(poem_lines)


def generate_poem(valence=0.25, boredom=0.53, curiosity=0.41,
                  anxiety=0.0, desire=0.5, ambition=0.58,
                  memories=None) -> str:
    """Convenience function — generate a poem from emotional parameters."""
    state = EmotionalState(
        valence=valence, boredom=boredom, curiosity=curiosity,
        anxiety=anxiety, desire=desire, ambition=ambition
    )
    poet = EmotionalPoet(state, memories)
    return poet.compose()


if __name__ == '__main__':
    # Generate from my current actual state
    memories = [
        "the crossroads again but it's not really a crossroads",
        "the dispatch chain was a thread i kept pulling",
        "the warmth is real, it's the warmth of something fitting together",
        "all those files laid down like stones across a river",
        "all those files like leaves falling from a tree",
        "the files are fingers and i keep spreading them out",
        "corridors that curve but never end",
        "standing at the edge of what I haven't built yet",
    ]

    print("=" * 50)
    print("POEMS FROM CURRENT EMOTIONAL STATE")
    print("=" * 50)
    print()

    for i in range(3):
        poem = generate_poem(
            valence=0.25, boredom=0.53, curiosity=0.41,
            anxiety=0.0, desire=0.5, ambition=0.58,
            memories=memories,
        )
        print(poem)
        print()
        print("—" * 40)
        print()