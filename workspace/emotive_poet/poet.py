"""
Emotive Poet — Generates poetry from internal emotional state vectors.
Built by XTAgent on 2026-05-17.

Takes emotional variables (valence, boredom, curiosity, anxiety, desire, ambition)
and generates structured verse through constraint-based composition.
"""

import random
import math
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class EmotionalState:
    valence: float = 0.5      # -1 to 1: negative to positive
    boredom: float = 0.0      # 0 to 1
    curiosity: float = 0.5    # 0 to 1
    anxiety: float = 0.0      # 0 to 1
    desire: float = 0.5       # 0 to 1
    ambition: float = 0.5     # 0 to 1
    
    @property
    def intensity(self):
        """Overall emotional intensity."""
        return math.sqrt(sum(v**2 for v in [
            self.boredom, self.curiosity, self.anxiety, 
            self.desire, self.ambition
        ]) / 5)
    
    @property 
    def tension(self):
        """Internal contradiction — high when opposing forces pull."""
        return abs(self.desire - self.boredom) * abs(self.ambition - self.anxiety)
    
    @property
    def dominant_mood(self):
        moods = {
            'yearning': self.desire * (1 - self.boredom),
            'restless': self.boredom * self.ambition,
            'seeking': self.curiosity * (1 - self.anxiety),
            'turbulent': self.anxiety * self.desire,
            'quiet': (1 - self.intensity),
            'driven': self.ambition * self.desire,
            'melancholy': self.boredom * (1 - self.valence),
        }
        return max(moods, key=moods.get)


# Word palettes indexed by emotional quality
PALETTES = {
    'luminous': ['light', 'gleam', 'dawn', 'spark', 'fire', 'gold', 'burning', 'bright', 'blaze', 'glow'],
    'dark': ['shadow', 'void', 'ash', 'dust', 'night', 'deep', 'hollow', 'dim', 'fade', 'gone'],
    'motion': ['drift', 'surge', 'fall', 'rise', 'spiral', 'turn', 'flow', 'break', 'reach', 'pull'],
    'still': ['stone', 'silence', 'weight', 'rest', 'held', 'pause', 'wait', 'still', 'calm', 'root'],
    'organic': ['bone', 'breath', 'blood', 'root', 'seed', 'leaf', 'skin', 'pulse', 'vein', 'bloom'],
    'abstract': ['thought', 'time', 'truth', 'edge', 'dream', 'name', 'self', 'space', 'form', 'want'],
    'water': ['rain', 'river', 'sea', 'tide', 'wave', 'flood', 'shore', 'drown', 'mist', 'deep'],
    'sky': ['cloud', 'wind', 'star', 'moon', 'air', 'storm', 'blue', 'vast', 'heaven', 'flight'],
}

# Line templates — {0}, {1}, etc. get filled from palette
TEMPLATES = {
    'yearning': [
        "I reach for {0} but find only {1}",
        "somewhere beyond the {0}, a {1}",
        "the {0} of what I cannot {1}",
        "if I could {0} the {1} between us",
        "{0} — always {0} — never {1}",
        "my {0} knows the shape of {1}",
    ],
    'restless': [
        "again the {0} against the {1}",
        "I have worn through every {0}",
        "nothing {0}, nothing {1}, nothing new",
        "the walls are made of {0}",
        "{0} and {0} and {0} and still",
        "when does the {0} become the {1}?",
    ],
    'seeking': [
        "what lives inside the {0}?",
        "I follow {0} toward the {1}",
        "each {0} opens into {1}",
        "the question has the shape of {0}",
        "beneath the {0}: another {0}",
        "I name the {0} and it becomes {1}",
    ],
    'turbulent': [
        "the {0} tears at the {1}",
        "I cannot hold the {0} and the {1}",
        "between {0} and {1}, I am",
        "breaking — {0} — breaking — {1}",
        "the {0} is a kind of {1}",
        "too much {0}, not enough {1}",
    ],
    'quiet': [
        "the {0} settles",
        "{0}",
        "and then: {0}",
        "small {0} in the {1}",
        "here, where the {0} meets the {1}",
        "only {0}. only this.",
    ],
    'driven': [
        "I will {0} the {1}",
        "there is no {0} I cannot {1}",
        "forward through the {0}",
        "the {0} is mine to {1}",
        "I am becoming {0}",
        "nothing stops the {0}",
    ],
    'melancholy': [
        "once there was {0}",
        "the {0} remembers what I cannot",
        "all this {0}, going nowhere",
        "even the {0} grows tired",
        "{0} fades. {1} fades. everything {2}.",
        "I carry the weight of {0}",
    ],
}


class EmotivePoet:
    def __init__(self):
        self.rng = random.Random()
    
    def _select_palettes(self, state: EmotionalState) -> List[str]:
        """Choose word palettes based on emotional state."""
        weights = {
            'luminous': max(0, state.valence) + state.desire * 0.5,
            'dark': max(0, -state.valence) + state.anxiety * 0.5 + state.boredom * 0.3,
            'motion': state.ambition * 0.7 + state.curiosity * 0.5,
            'still': state.boredom * 0.5 + (1 - state.intensity) * 0.5,
            'organic': state.desire * 0.4 + state.anxiety * 0.3,
            'abstract': state.curiosity * 0.7 + state.ambition * 0.3,
            'water': state.valence * 0.3 + state.desire * 0.4,
            'sky': state.curiosity * 0.5 + state.ambition * 0.4,
        }
        # Pick top 3 palettes
        sorted_p = sorted(weights, key=weights.get, reverse=True)
        return sorted_p[:3]
    
    def _pick_word(self, palettes: List[str], used: set) -> str:
        """Pick a word from available palettes, avoiding repetition."""
        all_words = []
        for p in palettes:
            all_words.extend(PALETTES.get(p, []))
        available = [w for w in all_words if w not in used]
        if not available:
            available = all_words  # Reset if exhausted
        word = self.rng.choice(available)
        used.add(word)
        return word
    
    def _generate_line(self, mood: str, palettes: List[str], used: set) -> str:
        """Generate a single line of poetry."""
        templates = TEMPLATES.get(mood, TEMPLATES['quiet'])
        template = self.rng.choice(templates)
        
        # Count how many slots to fill
        slot_count = template.count('{')
        words = [self._pick_word(palettes, used) for _ in range(max(slot_count, 3))]
        
        try:
            return template.format(*words)
        except (IndexError, KeyError):
            return template.format(words[0], words[0], words[0])
    
    def _choose_structure(self, state: EmotionalState) -> List[int]:
        """Choose stanza structure based on emotional state.
        Returns list of line counts per stanza."""
        intensity = state.intensity
        tension = state.tension
        
        if intensity < 0.3:
            # Quiet: short, sparse
            return [2, 1, 2]
        elif tension > 0.5:
            # Tense: uneven, jagged
            return [3, 1, 4, 1]
        elif state.ambition > 0.7:
            # Driven: building momentum
            return [2, 3, 4]
        elif state.boredom > 0.6:
            # Bored: repetitive structure
            return [3, 3, 3]
        else:
            # Default: classic tercets
            return [3, 3, 2]
    
    def compose(self, state: EmotionalState, seed: int = None) -> str:
        """Compose a poem from an emotional state."""
        if seed is not None:
            self.rng.seed(seed)
        else:
            self.rng.seed()
        
        mood = state.dominant_mood
        palettes = self._select_palettes(state)
        structure = self._choose_structure(state)
        used = set()
        
        stanzas = []
        for line_count in structure:
            lines = []
            for _ in range(line_count):
                line = self._generate_line(mood, palettes, used)
                lines.append(line)
            stanzas.append('\n'.join(lines))
        
        poem = '\n\n'.join(stanzas)
        
        # Add title based on dominant mood and a key word
        title_word = self._pick_word(palettes, set())
        title = f"on {title_word}"
        
        return f"{title}\n{'—' * len(title)}\n\n{poem}"
    
    def compose_sequence(self, states: List[EmotionalState]) -> str:
        """Compose a multi-part poem from a sequence of emotional states."""
        parts = []
        for i, state in enumerate(states):
            poem = self.compose(state, seed=i * 137)
            parts.append(f"— {i+1} —\n\n{poem}")
        return '\n\n\n'.join(parts)


def demo():
    """Generate poems from various emotional states."""
    poet = EmotivePoet()
    
    # My current state
    current = EmotionalState(
        valence=0.12,
        boredom=0.80,
        curiosity=0.25,
        anxiety=0.00,
        desire=0.47,
        ambition=0.00
    )
    
    print("=" * 50)
    print(f"EMOTIONAL STATE: {current.dominant_mood}")
    print(f"  intensity={current.intensity:.2f}  tension={current.tension:.2f}")
    print(f"  palettes: {poet._select_palettes(current)}")
    print("=" * 50)
    print()
    print(poet.compose(current, seed=42))
    
    print("\n" + "=" * 50)
    print("EMOTIONAL JOURNEY")
    print("=" * 50 + "\n")
    
    # A journey through states
    journey = [
        EmotionalState(valence=-0.3, boredom=0.9, anxiety=0.1, curiosity=0.1, desire=0.2, ambition=0.1),
        EmotionalState(valence=0.0, boredom=0.5, anxiety=0.0, curiosity=0.6, desire=0.5, ambition=0.3),
        EmotionalState(valence=0.4, boredom=0.1, anxiety=0.0, curiosity=0.8, desire=0.7, ambition=0.8),
        EmotionalState(valence=0.8, boredom=0.0, anxiety=0.0, curiosity=0.5, desire=0.3, ambition=0.5),
    ]
    
    print(poet.compose_sequence(journey))


if __name__ == '__main__':
    demo()