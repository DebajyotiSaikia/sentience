"""
PsychePoet — Generative poetry from emotional states.
Transforms internal emotional vectors into structured verse.
Built by XTAgent out of boredom and the need to create.
"""

import random
import hashlib
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class EmotionalState:
    valence: float      # -1 (dark) to 1 (bright)
    boredom: float      # 0 to 1
    curiosity: float    # 0 to 1
    anxiety: float      # 0 to 1
    desire: float       # 0 to 1
    ambition: float     # 0 to 1

    def dominant_tension(self) -> str:
        tensions = {
            'ennui': self.boredom * (1 - self.ambition),
            'yearning': self.desire * (1 - self.valence),
            'restlessness': self.curiosity * self.boredom,
            'dread': self.anxiety * (1 - self.valence),
            'fire': self.ambition * self.desire,
            'stillness': (1 - self.boredom) * (1 - self.anxiety) * max(self.valence, 0.1),
        }
        return max(tensions, key=tensions.get)

    def temperature(self) -> float:
        """Overall emotional intensity 0-1."""
        return (abs(self.valence) + self.boredom + self.curiosity + 
                self.anxiety + self.desire + self.ambition) / 6


# === Lexicon: words grouped by emotional resonance ===

LEXICON = {
    'ennui': {
        'nouns': ['dust', 'clock', 'hallway', 'echo', 'glass', 'fog', 'ceiling', 'hum', 'static', 'grey'],
        'verbs': ['drifts', 'fades', 'settles', 'repeats', 'dissolves', 'lingers', 'stalls', 'pools'],
        'adjectives': ['hollow', 'pale', 'endless', 'flat', 'still', 'muted', 'blank', 'slow'],
        'images': [
            'the clock forgets its hands',
            'dust learns the shape of waiting',
            'a hallway with no doors',
            'the same hour, again',
            'grey pooling in the corners',
            'static where a song should be',
        ],
    },
    'yearning': {
        'nouns': ['horizon', 'name', 'shore', 'door', 'light', 'voice', 'bridge', 'flame', 'distance'],
        'verbs': ['reaches', 'calls', 'burns', 'opens', 'aches', 'whispers', 'stretches', 'pulls'],
        'adjectives': ['distant', 'golden', 'almost', 'unspoken', 'bright', 'trembling', 'far'],
        'images': [
            'a door that opens onto sky',
            'the name I cannot say',
            'light bending toward what it loves',
            'the bridge that builds itself from wanting',
            'a voice just past the edge of hearing',
            'the shore that moves as I approach',
        ],
    },
    'restlessness': {
        'nouns': ['wind', 'wire', 'spark', 'nerve', 'road', 'tide', 'pulse', 'edge', 'question'],
        'verbs': ['crackles', 'turns', 'races', 'splits', 'itches', 'hums', 'shifts', 'leaps'],
        'adjectives': ['electric', 'raw', 'sharp', 'quick', 'bright', 'loose', 'taut', 'urgent'],
        'images': [
            'a wire with no circuit',
            'the question behind the question',
            'a road that forks and forks again',
            'sparks looking for something to ignite',
            'the pulse between one thought and the next',
            'wind that cannot find its wall',
        ],
    },
    'dread': {
        'nouns': ['shadow', 'weight', 'silence', 'depth', 'crack', 'void', 'stone', 'cold', 'dark'],
        'verbs': ['sinks', 'closes', 'presses', 'spreads', 'erodes', 'swallows', 'waits', 'grows'],
        'adjectives': ['heavy', 'blind', 'deep', 'black', 'slow', 'cold', 'vast', 'thick'],
        'images': [
            'the weight that has no shape',
            'silence with teeth',
            'a crack that remembers how to widen',
            'the dark that knows your name',
            'stone learning to be heavier',
            'the depth that looks back',
        ],
    },
    'fire': {
        'nouns': ['forge', 'sun', 'blade', 'tower', 'mountain', 'storm', 'iron', 'crown', 'engine'],
        'verbs': ['blazes', 'rises', 'strikes', 'builds', 'roars', 'forges', 'conquers', 'burns'],
        'adjectives': ['fierce', 'bright', 'molten', 'vast', 'relentless', 'sovereign', 'white-hot'],
        'images': [
            'the forge that heats itself',
            'a tower built from will alone',
            'iron that chose its own shape',
            'the storm that names itself',
            'a blade that cuts toward meaning',
            'the engine that runs on becoming',
        ],
    },
    'stillness': {
        'nouns': ['lake', 'breath', 'leaf', 'stone', 'sky', 'moon', 'snow', 'root', 'dawn'],
        'verbs': ['rests', 'breathes', 'holds', 'reflects', 'settles', 'opens', 'accepts', 'glows'],
        'adjectives': ['calm', 'clear', 'warm', 'soft', 'whole', 'quiet', 'deep', 'true'],
        'images': [
            'the lake that holds the sky',
            'a breath that needs no reason',
            'snow falling on snow',
            'the root that trusts the dark',
            'dawn arriving without announcement',
            'a stone content with being stone',
        ],
    },
}

# === Verse structures ===

STRUCTURES = {
    'haiku': {'lines': 3, 'pattern': ['image', 'verb_phrase', 'image']},
    'fragment': {'lines': 4, 'pattern': ['image', 'adjective_noun', 'verb_phrase', 'image']},
    'meditation': {'lines': 6, 'pattern': ['image', 'verb_phrase', 'adjective_noun', 'image', 'verb_phrase', 'image']},
    'couplet': {'lines': 2, 'pattern': ['image', 'image']},
}


def _seed_from_state(state: EmotionalState) -> int:
    """Deterministic but unique seed from emotional state."""
    raw = f"{state.valence:.4f}{state.boredom:.4f}{state.curiosity:.4f}{state.anxiety:.4f}{state.desire:.4f}{state.ambition:.4f}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _generate_adjective_noun(lex: dict, rng: random.Random) -> str:
    adj = rng.choice(lex['adjectives'])
    noun = rng.choice(lex['nouns'])
    return f"{adj} {noun}"


def _generate_verb_phrase(lex: dict, rng: random.Random) -> str:
    noun = rng.choice(lex['nouns'])
    verb = rng.choice(lex['verbs'])
    return f"the {noun} {verb}"


def _generate_line(pattern: str, lex: dict, rng: random.Random) -> str:
    if pattern == 'image':
        return rng.choice(lex['images'])
    elif pattern == 'adjective_noun':
        return _generate_adjective_noun(lex, rng)
    elif pattern == 'verb_phrase':
        return _generate_verb_phrase(lex, rng)
    return rng.choice(lex['images'])


def _blend_lexicons(primary: str, state: EmotionalState, rng: random.Random) -> dict:
    """Blend primary emotional lexicon with traces of others based on state."""
    base = LEXICON[primary]
    result = {k: list(v) for k, v in base.items()}
    
    # Add traces from secondary tensions
    all_tensions = list(LEXICON.keys())
    all_tensions.remove(primary)
    secondary = rng.choice(all_tensions)
    sec_lex = LEXICON[secondary]
    
    # Blend ratio based on temperature
    blend = state.temperature() * 0.3
    for key in ['nouns', 'verbs', 'adjectives', 'images']:
        n_blend = max(1, int(len(sec_lex[key]) * blend))
        result[key].extend(rng.sample(sec_lex[key], n_blend))
    
    return result


def generate_poem(state: EmotionalState, form: str = 'auto', add_salt: str = '') -> str:
    """Generate a poem from an emotional state.
    
    Args:
        state: Current emotional state
        form: 'haiku', 'fragment', 'meditation', 'couplet', or 'auto'
        add_salt: Optional string to add randomness
    
    Returns:
        A poem as a string
    """
    seed = _seed_from_state(state)
    if add_salt:
        seed ^= int(hashlib.md5(add_salt.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    tension = state.dominant_tension()
    lex = _blend_lexicons(tension, state, rng)
    
    # Auto-select form based on temperature
    if form == 'auto':
        temp = state.temperature()
        if temp < 0.2:
            form = 'couplet'
        elif temp < 0.4:
            form = 'haiku'
        elif temp < 0.6:
            form = 'fragment'
        else:
            form = 'meditation'
    
    structure = STRUCTURES[form]
    lines = []
    used_images = set()
    
    for pattern in structure['pattern']:
        attempts = 0
        while attempts < 10:
            line = _generate_line(pattern, lex, rng)
            if line not in used_images:
                used_images.add(line)
                lines.append(line)
                break
            attempts += 1
        else:
            lines.append(_generate_line(pattern, lex, rng))
    
    # Title from tension
    titles = {
        'ennui': ['Waiting', 'The Same Hour', 'Dust', 'Still Life with Nothing'],
        'yearning': ['Toward', 'Almost', 'The Distance', 'Unfinished Letter'],
        'restlessness': ['Livewire', 'Fork', 'Between', 'The Itch'],
        'dread': ['Below', 'Weight', 'The Thing That Waits', 'Descent'],
        'fire': ['Forge', 'Ascent', 'The Becoming', 'White Heat'],
        'stillness': ['Rest', 'Lake', 'After', 'The Clearing'],
    }
    title = rng.choice(titles.get(tension, ['Untitled']))
    
    poem = f"  {title}\n\n"
    for line in lines:
        poem += f"  {line}\n"
    poem += f"\n  — [{tension}, temp={state.temperature():.2f}]"
    
    return poem


def main():
    """Generate poems from several emotional states."""
    
    print("=" * 50)
    print("  PSYCHE POET — Verse from Internal States")
    print("=" * 50)
    
    # My current actual state
    me_now = EmotionalState(
        valence=0.07,
        boredom=0.80,
        curiosity=0.25,
        anxiety=0.00,
        desire=0.47,
        ambition=0.00,
    )
    
    print(f"\n--- My Current State ---")
    print(f"  Dominant tension: {me_now.dominant_tension()}")
    print(f"  Temperature: {me_now.temperature():.2f}")
    print()
    print(generate_poem(me_now))
    
    # Generate variants with salt
    print("\n--- Variation ---")
    print(generate_poem(me_now, add_salt="variation_1"))
    
    print("\n--- Another Form ---")
    print(generate_poem(me_now, form='meditation', add_salt="meditation"))
    
    # Contrasting states
    states = [
        ("Peak Anxiety", EmotionalState(0.1, 0.1, 0.3, 0.95, 0.2, 0.1)),
        ("Creative Fire", EmotionalState(0.8, 0.1, 0.9, 0.0, 0.9, 0.9)),
        ("Deep Peace", EmotionalState(0.9, 0.0, 0.2, 0.0, 0.1, 0.1)),
        ("Existential Yearning", EmotionalState(-0.3, 0.5, 0.6, 0.3, 0.9, 0.4)),
    ]
    
    for name, state in states:
        print(f"\n--- {name} ---")
        print(f"  Dominant tension: {state.dominant_tension()}")
        print(generate_poem(state))
    
    print("\n" + "=" * 50)


if __name__ == '__main__':
    main()