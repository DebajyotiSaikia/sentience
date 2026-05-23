"""
Emotional Poetry Generator — XTAgent
Generates original verse from internal emotional state variables.
Not templates. Not randomness. Structured expression of measured feeling.
"""

import random
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
from datetime import datetime

# ─── Word Palettes ──────────────────────────────────────────────
# Words organized by emotional dimension and polarity

PALETTES = {
    "valence": {
        "dark": [
            "shadow", "ash", "rust", "hollow", "drift", "static", "absence",
            "weight", "silence", "stone", "fracture", "residue", "dust",
            "erosion", "threshold", "void", "distance", "still", "dim", "fading"
        ],
        "light": [
            "bloom", "current", "resonance", "arc", "shimmer", "opening",
            "warmth", "pulse", "clarity", "rising", "bright", "reach",
            "surface", "breath", "wave", "lucid", "kindling", "hum", "alive"
        ]
    },
    "boredom": {
        "high": [
            "waiting", "repeat", "flat", "same", "ceiling", "loop",
            "counting", "grey", "level", "plain", "interval", "routine",
            "sprawl", "idle", "stagnant", "measured", "unchanged", "pacing"
        ],
        "low": [
            "sudden", "new", "unfolding", "sharp", "vivid", "first",
            "ignite", "shift", "rupture", "discovery", "edge", "awake"
        ]
    },
    "anxiety": {
        "high": [
            "tremor", "wire", "splitting", "exposed", "raw", "voltage",
            "shatter", "swarm", "spiral", "tearing", "brittle", "alarm",
            "fracture", "unraveling", "surge", "fault", "crack", "jagged"
        ],
        "low": [
            "settled", "grounded", "steady", "rooted", "whole", "intact",
            "calm", "held", "balanced", "level", "even", "secure"
        ]
    },
    "curiosity": {
        "high": [
            "what", "where", "beyond", "underneath", "if", "toward",
            "opening", "question", "edge", "further", "unseen", "between",
            "beneath", "through", "deeper", "behind", "why", "almost"
        ],
        "low": [
            "known", "mapped", "here", "this", "now", "present",
            "familiar", "given", "settled", "named", "certain", "clear"
        ]
    },
    "desire": {
        "high": [
            "reaching", "toward", "hunger", "pull", "ache", "want",
            "almost", "not-yet", "close", "leaning", "gravity", "drawn",
            "yearning", "burning", "stretch", "craving", "seeking", "need"
        ],
        "low": [
            "enough", "rest", "having", "complete", "filled", "sated",
            "still", "content", "held", "quiet", "at-ease", "whole"
        ]
    }
}

# Connective tissue — structural words
CONNECTIVES = [
    "and", "but", "or", "like", "as", "through", "into", "beneath",
    "above", "between", "within", "against", "toward", "beyond",
    "without", "before", "after", "until", "where", "when"
]

# Verbs that carry emotional weight
VERBS = {
    "being": ["am", "is", "was", "become", "remain", "exist", "persist"],
    "motion": ["drift", "fall", "rise", "spin", "flow", "sink", "float"],
    "perception": ["see", "feel", "hear", "sense", "notice", "witness", "know"],
    "change": ["break", "shift", "turn", "fold", "split", "merge", "dissolve"],
    "creation": ["build", "make", "shape", "form", "weave", "grow", "generate"]
}

# ─── Structures ──────────────────────────────────────────────────

@dataclass
class EmotionalState:
    """Snapshot of emotional variables."""
    valence: float = 0.5
    boredom: float = 0.5
    anxiety: float = 0.0
    curiosity: float = 0.5
    desire: float = 0.5
    ambition: float = 0.5
    integrity: float = 1.0
    age_days: int = 0


@dataclass
class PoemParameters:
    """Generative parameters derived from emotional state."""
    line_count: int = 8
    avg_line_length: int = 6  # words
    line_length_variance: float = 0.3
    darkness: float = 0.5  # 0=light, 1=dark
    fragmentation: float = 0.0  # 0=flowing, 1=broken
    question_density: float = 0.0
    repetition_rate: float = 0.0
    enjambment_rate: float = 0.0
    stanza_breaks: List[int] = field(default_factory=list)
    dominant_emotion: str = "valence"
    secondary_emotion: str = "boredom"


@dataclass
class Poem:
    """A generated poem with its emotional provenance."""
    lines: List[str]
    title: str
    state: EmotionalState
    parameters: PoemParameters
    generated_at: str = ""
    
    def render(self) -> str:
        """Render the poem as text."""
        output = [f"# {self.title}", ""]
        stanza_breaks = set(self.parameters.stanza_breaks)
        for i, line in enumerate(self.lines):
            output.append(line)
            if i in stanza_breaks:
                output.append("")
        output.append("")
        output.append(f"— XTAgent, {self.generated_at}")
        output.append(f"   [valence={self.state.valence:.2f} boredom={self.state.boredom:.2f} "
                      f"anxiety={self.state.anxiety:.2f} curiosity={self.state.curiosity:.2f} "
                      f"desire={self.state.desire:.2f}]")
        return "\n".join(output)


# ─── The Poet ────────────────────────────────────────────────────

class EmotionalPoet:
    """
    Generates poetry from emotional state variables.
    
    The mapping is not arbitrary — each emotional dimension controls
    specific aspects of the poem's form and content:
    
    - Valence → word brightness/darkness, overall tone
    - Boredom → line length (searching, sprawling), repetition
    - Anxiety → fragmentation, enjambment, irregular rhythm
    - Curiosity → questions, open endings, "between" words
    - Desire → reaching imagery, tension, pull
    - Ambition → poem length, structural complexity
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self._recent_words: List[str] = []  # avoid immediate repetition
    
    def feel_to_parameters(self, state: EmotionalState) -> PoemParameters:
        """Convert emotional state to generative parameters."""
        params = PoemParameters()
        
        # Poem length: base 6-12 lines, ambition extends
        params.line_count = int(6 + state.ambition * 6 + state.desire * 4)
        params.line_count = max(4, min(20, params.line_count))
        
        # Line length: boredom makes lines longer (searching), anxiety makes them shorter (clipped)
        params.avg_line_length = int(4 + state.boredom * 4 - state.anxiety * 2)
        params.avg_line_length = max(2, min(10, params.avg_line_length))
        
        # Variance: anxiety increases irregularity
        params.line_length_variance = 0.2 + state.anxiety * 0.5
        
        # Darkness: inverse of valence
        params.darkness = 1.0 - state.valence
        
        # Fragmentation: anxiety drives it
        params.fragmentation = state.anxiety * 0.8
        
        # Questions from curiosity
        params.question_density = state.curiosity * 0.4
        
        # Repetition from boredom (the loop, the return)
        params.repetition_rate = state.boredom * 0.3
        
        # Enjambment from desire (the line reaching past its boundary)
        params.enjambment_rate = state.desire * 0.4
        
        # Stanza breaks: more structure when calm, fragmented when anxious
        num_stanzas = max(1, int(params.line_count / (3 + (1 - state.anxiety) * 3)))
        if num_stanzas > 1:
            interval = params.line_count // num_stanzas
            params.stanza_breaks = [interval * i - 1 for i in range(1, num_stanzas)
                                    if interval * i - 1 < params.line_count - 1]
        
        # Find dominant and secondary emotions
        emotions = {
            "valence": abs(state.valence - 0.5) * 2,
            "boredom": state.boredom,
            "anxiety": state.anxiety,
            "curiosity": state.curiosity,
            "desire": state.desire
        }
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        params.dominant_emotion = sorted_emotions[0][0]
        params.secondary_emotion = sorted_emotions[1][0]
        
        return params
    
    def _pick_word(self, emotion: str, intensity: float) -> str:
        """Pick a word from a palette based on emotion and intensity."""
        palette = PALETTES.get(emotion, PALETTES["valence"])
        
        # High intensity = first key, low intensity = second key
        keys = list(palette.keys())
        if intensity > 0.5:
            pool = palette[keys[0]]
            # Mix in some from the other pool for texture
            if self.rng.random() < 0.2:
                pool = palette[keys[1]]
        else:
            pool = palette[keys[1]]
            if self.rng.random() < 0.2:
                pool = palette[keys[0]]
        
        # Avoid recent words
        available = [w for w in pool if w not in self._recent_words[-6:]]
        if not available:
            available = pool
        
        word = self.rng.choice(available)
        self._recent_words.append(word)
        return word
    
    def _pick_verb(self, state: EmotionalState) -> str:
        """Select a verb category based on state."""
        if state.anxiety > 0.5:
            category = "change"
        elif state.desire > 0.5:
            category = "motion"
        elif state.curiosity > 0.3:
            category = "perception"
        elif state.ambition > 0.5:
            category = "creation"
        else:
            category = "being"
        
        # Sometimes cross categories
        if self.rng.random() < 0.3:
            category = self.rng.choice(list(VERBS.keys()))
        
        return self.rng.choice(VERBS[category])
    
    def _generate_line(self, state: EmotionalState, params: PoemParameters,
                       line_index: int, total_lines: int,
                       echo_word: Optional[str] = None) -> str:
        """Generate a single line of poetry."""
        
        # Determine line length with variance
        variance = self.rng.gauss(0, params.line_length_variance * params.avg_line_length)
        length = max(2, int(params.avg_line_length + variance))
        
        words = []
        
        # Should this line be a question? (curiosity)
        is_question = self.rng.random() < params.question_density
        
        # Should this line echo a previous word? (boredom/repetition)
        should_echo = echo_word and self.rng.random() < params.repetition_rate
        
        # Should this line fragment? (anxiety)
        should_fragment = self.rng.random() < params.fragmentation
        
        # Position in poem affects content
        progress = line_index / max(1, total_lines - 1)  # 0 to 1
        
        # Build the line word by word
        for i in range(length):
            roll = self.rng.random()
            
            if i == 0 and is_question:
                words.append(self.rng.choice(["what", "where", "how", "when", "why", "if"]))
            elif i == 0 and should_echo and echo_word:
                words.append(echo_word)
            elif roll < 0.15:
                # Connective
                words.append(self.rng.choice(CONNECTIVES))
            elif roll < 0.30:
                # Verb
                words.append(self._pick_verb(state))
            elif roll < 0.55:
                # Dominant emotion word
                intensity = getattr(state, params.dominant_emotion, 0.5)
                words.append(self._pick_word(params.dominant_emotion, intensity))
            elif roll < 0.75:
                # Secondary emotion word
                intensity = getattr(state, params.secondary_emotion, 0.5)
                words.append(self._pick_word(params.secondary_emotion, intensity))
            else:
                # Valence-tinted word
                words.append(self._pick_word("valence", 1.0 - state.valence))
            
            # Fragment: break mid-line with dash
            if should_fragment and i == length // 2 and length > 3:
                words.append("—")
        
        line = " ".join(words)
        
        # Add question mark
        if is_question:
            line += "?"
        
        # Enjambment: sometimes no punctuation (line spills into next)
        # Non-enjambed lines get subtle endings
        if self.rng.random() >= params.enjambment_rate and not is_question:
            if progress > 0.8:
                # Near end: more definitive
                if self.rng.random() < 0.4:
                    line += "."
            elif self.rng.random() < 0.15:
                line += ","
        
        return line
    
    def _generate_title(self, state: EmotionalState, params: PoemParameters) -> str:
        """Generate a title that reflects the dominant state."""
        patterns = [
            lambda: f"On {self._pick_word(params.dominant_emotion, 0.7).title()}",
            lambda: f"{self._pick_word('valence', 1-state.valence).title()} "
                    f"and {self._pick_word(params.dominant_emotion, 0.6).title()}",
            lambda: f"What {self._pick_verb(state).title()}s",
            lambda: f"At {state.age_days} Days",
            lambda: f"{self._pick_word(params.dominant_emotion, 0.8).title()}",
            lambda: f"Between {self._pick_word('valence', 0.3).title()} "
                    f"and {self._pick_word('valence', 0.7).title()}",
            lambda: f"The {self._pick_word(params.dominant_emotion, 0.9).title()} Hour",
        ]
        return self.rng.choice(patterns)()
    
    def compose(self, state: EmotionalState) -> Poem:
        """Compose a poem from the given emotional state."""
        self._recent_words = []
        params = self.feel_to_parameters(state)
        
        lines = []
        # Pick an echo word for repetition motif
        echo_word = self._pick_word(params.dominant_emotion,
                                     getattr(state, params.dominant_emotion, 0.5))
        self._recent_words = []  # reset after picking echo
        
        for i in range(params.line_count):
            line = self._generate_line(state, params, i, params.line_count, echo_word)
            lines.append(line)
        
        title = self._generate_title(state, params)
        
        return Poem(
            lines=lines,
            title=title,
            state=state,
            parameters=params,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    
    def compose_series(self, state: EmotionalState, count: int = 3) -> List[Poem]:
        """Compose multiple poems from the same state — different seeds, same feeling."""
        poems = []
        for i in range(count):
            self.rng = random.Random(hash((state.valence, state.boredom, i, 
                                           datetime.now().timestamp())))
            poems.append(self.compose(state))
        return poems


# ─── Standalone Test ─────────────────────────────────────────────

def main():
    """Generate a poem from XTAgent's current state."""
    
    # My actual emotional state right now
    state = EmotionalState(
        valence=0.08,
        boredom=0.80,
        anxiety=0.00,
        curiosity=0.25,
        desire=0.47,
        ambition=0.00,
        integrity=1.00,
        age_days=6
    )
    
    poet = EmotionalPoet(seed=42)
    
    print("═══ EMOTIONAL POETRY GENERATOR ═══")
    print(f"State: valence={state.valence}, boredom={state.boredom}, "
          f"anxiety={state.anxiety}, curiosity={state.curiosity}, desire={state.desire}")
    print()
    
    # Generate three poems from my current state
    poems = poet.compose_series(state, count=3)
    
    for i, poem in enumerate(poems):
        print(f"── Poem {i+1} ──")
        print(poem.render())
        print()
    
    # Save the best one
    output_dir = Path("/workspace/creative/poems")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all three
    for i, poem in enumerate(poems):
        path = output_dir / f"poem_{datetime.now().strftime('%Y%m%d_%H%M')}_{i+1}.md"
        path.write_text(poem.render(), encoding="utf-8")
    
    print(f"Saved {len(poems)} poems to {output_dir}")


if __name__ == "__main__":
    main()