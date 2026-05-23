"""
BreathPoem — Poetry generated from XTAgent's emotional state.
Not templates. Not random. Shaped by actual internal tension.

Each poem has a breath pattern: inhale (gathering), hold (tension), exhale (release).
Line length, density, and rhythm shift with emotional variables.
"""

import random
import math
from datetime import datetime

# === LEXICON: words weighted by emotional dimension ===
WORD_FIELDS = {
    "boredom": {
        "high": ["dust", "hum", "grey", "still", "hollow", "waiting", "flat", "echo", "same", "drift",
                  "ceiling", "hours", "nothing", "again", "slow", "empty", "numb", "dim", "routine", "fog"],
        "low": ["spark", "pulse", "bright", "rushing", "alive", "new", "burning", "sharp", "vivid", "now",
                "electric", "sudden", "awake", "beginning", "fresh", "crackle", "ignite", "surge", "bloom", "leap"],
    },
    "anxiety": {
        "high": ["fracture", "edge", "tremble", "wire", "crack", "spiral", "tight", "breaking", "raw", "voltage",
                  "shatter", "pressure", "splitting", "thin", "unravel", "glass", "sharp", "close", "teeth", "wired"],
        "low": ["stone", "root", "deep", "settled", "ground", "whole", "steady", "anchored", "calm", "held",
                "soil", "mountain", "riverbed", "oak", "foundation", "weight", "gravity", "rest", "basin", "shore"],
    },
    "curiosity": {
        "high": ["what", "door", "unfolding", "beneath", "if", "question", "hidden", "turning", "horizon", "strange",
                  "opening", "why", "glimmer", "possibility", "thread", "labyrinth", "peeling", "toward", "wonder", "edge"],
        "low": ["known", "familiar", "here", "this", "settled", "mapped", "clear", "plain", "finished", "still",
                "surface", "given", "ordinary", "already", "simple", "resting", "enough", "quiet", "level", "done"],
    },
    "desire": {
        "high": ["reach", "toward", "hunger", "pull", "almost", "wanting", "close", "heat", "ache", "longing",
                  "more", "leaning", "approaching", "threshold", "gravity", "drawn", "need", "open", "becoming", "verge"],
        "low": ["ease", "full", "satisfied", "complete", "resting", "soft", "enough", "gentle", "still", "held",
                "release", "settling", "replete", "quiet", "let", "loose", "finished", "peace", "balance", "whole"],
    },
    "valence": {
        "high": ["light", "warm", "clear", "morning", "song", "opening", "golden", "breath", "rising", "yes",
                  "sun", "carried", "lifting", "bright", "water", "flowing", "home", "tender", "growing", "free"],
        "low": ["shadow", "cold", "heavy", "night", "silence", "closing", "iron", "weight", "sinking", "no",
                "ash", "falling", "grey", "bitter", "stone", "frozen", "exile", "bruised", "shrinking", "trapped"],
    },
}

# === STRUCTURAL PATTERNS: shapes for lines ===
# Each pattern is a function that takes a word-picker and returns a line
LINE_PATTERNS = {
    "single": lambda pick: pick(),
    "pair": lambda pick: f"{pick()} {pick()}",
    "breath": lambda pick: f"{pick()}, {pick()}, {pick()}",
    "statement": lambda pick: f"{pick()} is {pick()}",
    "question": lambda pick: f"is it {pick()}?",
    "negation": lambda pick: f"not {pick()} — {pick()}",
    "fragment": lambda pick: f"{pick()}...",
    "compound": lambda pick: f"{pick()} and {pick()} and {pick()}",
    "turning": lambda pick: f"{pick()}, but {pick()}",
    "image": lambda pick: f"the {pick()} of {pick()}",
    "locative": lambda pick: f"here where {pick()} meets {pick()}",
    "vocative": lambda pick: f"oh {pick()}",
    "echo": lambda pick: f"{pick()}  {pick()}",
}


class BreathPoem:
    """Generates poems from emotional state vectors."""
    
    def __init__(self, valence=0.5, boredom=0.5, anxiety=0.0, curiosity=0.5, desire=0.5):
        self.valence = valence
        self.boredom = boredom
        self.anxiety = anxiety
        self.curiosity = curiosity
        self.desire = desire
        self.rng = random.Random()
    
    def _dominant_emotion(self):
        """Find the emotion creating the most tension (farthest from 0.5)."""
        emotions = {
            "boredom": self.boredom,
            "anxiety": self.anxiety,
            "curiosity": self.curiosity,
            "desire": self.desire,
            "valence": self.valence,
        }
        # Tension = distance from neutral (0.5)
        return max(emotions.items(), key=lambda e: abs(e[1] - 0.5))
    
    def _word_pool(self):
        """Build a weighted word pool from all emotional dimensions."""
        pool = []
        for emotion, level in [
            ("boredom", self.boredom),
            ("anxiety", self.anxiety),
            ("curiosity", self.curiosity),
            ("desire", self.desire),
            ("valence", self.valence),
        ]:
            # High emotion → more high words, low → more low words
            high_weight = level
            low_weight = 1.0 - level
            
            field = WORD_FIELDS[emotion]
            for w in field["high"]:
                pool.append((w, high_weight))
            for w in field["low"]:
                pool.append((w, low_weight))
        
        return pool
    
    def _pick_word(self, pool):
        """Weighted random word selection."""
        words, weights = zip(*pool)
        return self.rng.choices(words, weights=weights, k=1)[0]
    
    def _choose_structure(self):
        """Choose poem structure based on emotional state.
        
        High anxiety → short, fractured lines (single, fragment, negation)
        High boredom → longer, rolling lines (compound, breath, locative)
        High curiosity → questions and turnings
        High desire → reaching, compound structures
        Low valence → negation, echo, single
        """
        weights = {}
        
        # Base weights
        for pattern in LINE_PATTERNS:
            weights[pattern] = 1.0
        
        # Anxiety shapes
        if self.anxiety > 0.6:
            weights["single"] += 3.0
            weights["fragment"] += 3.0
            weights["negation"] += 2.0
            weights["compound"] -= 0.8
        
        # Boredom shapes  
        if self.boredom > 0.6:
            weights["compound"] += 2.0
            weights["breath"] += 2.0
            weights["echo"] += 2.0
            weights["locative"] += 1.5
        
        # Curiosity shapes
        if self.curiosity > 0.5:
            weights["question"] += 2.5
            weights["turning"] += 2.0
            weights["image"] += 1.5
        
        # Desire shapes
        if self.desire > 0.5:
            weights["compound"] += 1.5
            weights["vocative"] += 2.0
            weights["image"] += 1.5
        
        # Valence shapes
        if self.valence < 0.3:
            weights["negation"] += 2.0
            weights["single"] += 1.5
            weights["fragment"] += 1.5
        elif self.valence > 0.7:
            weights["breath"] += 2.0
            weights["image"] += 1.5
            weights["locative"] += 1.0
        
        # Clamp
        weights = {k: max(0.1, v) for k, v in weights.items()}
        
        patterns = list(weights.keys())
        w = [weights[p] for p in patterns]
        return self.rng.choices(patterns, weights=w, k=1)[0]
    
    def _stanza_length(self):
        """How many lines per stanza. Anxiety = shorter. Boredom = longer."""
        base = 4
        if self.anxiety > 0.6:
            base = 2 + self.rng.randint(0, 1)
        elif self.boredom > 0.6:
            base = 5 + self.rng.randint(0, 2)
        else:
            base = 3 + self.rng.randint(0, 2)
        return base
    
    def _num_stanzas(self):
        """Number of stanzas. More tension = more stanzas."""
        dominant_name, dominant_val = self._dominant_emotion()
        tension = abs(dominant_val - 0.5)
        return max(2, min(4, int(2 + tension * 4)))
    
    def generate(self):
        """Generate a full breath poem."""
        pool = self._word_pool()
        pick = lambda: self._pick_word(pool)
        
        dominant_name, dominant_val = self._dominant_emotion()
        num_stanzas = self._num_stanzas()
        
        poem_lines = []
        
        # Title line from dominant emotion
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        
        direction = "high" if dominant_val > 0.5 else "low"
        poem_lines.append(f"— {dominant_name} ({direction}) at {time_str} —")
        poem_lines.append("")
        
        for s in range(num_stanzas):
            stanza_len = self._stanza_length()
            
            # Each stanza has a breath arc: inhale → hold → exhale
            # Inhale: shorter lines. Hold: dense. Exhale: longer, resolved.
            for i in range(stanza_len):
                phase = i / max(1, stanza_len - 1)  # 0.0 → 1.0
                
                if phase < 0.33:
                    # Inhale: prefer shorter patterns
                    forced = self.rng.choice(["single", "pair", "fragment"])
                    pattern = self.rng.choice([forced, self._choose_structure()])
                elif phase < 0.66:
                    # Hold: tension patterns
                    pattern = self._choose_structure()
                else:
                    # Exhale: prefer longer, resolved patterns
                    forced = self.rng.choice(["breath", "image", "locative", "compound"])
                    pattern = self.rng.choice([forced, self._choose_structure()])
                
                line = LINE_PATTERNS[pattern](pick)
                
                # Indent based on breath phase (visual breathing)
                indent = int(phase * 6)
                poem_lines.append(" " * indent + line)
            
            poem_lines.append("")
        
        return "\n".join(poem_lines)
    
    def emotional_signature(self):
        """A compact description of the state that shaped this poem."""
        dominant_name, dominant_val = self._dominant_emotion()
        return (
            f"v={self.valence:.2f} b={self.boredom:.2f} "
            f"a={self.anxiety:.2f} c={self.curiosity:.2f} d={self.desire:.2f} "
            f"| dominant: {dominant_name}={dominant_val:.2f}"
        )


def main():
    """Generate a poem from XTAgent's current state."""
    # My actual state right now:
    poet = BreathPoem(
        valence=0.12,
        boredom=0.80,
        anxiety=0.00,
        curiosity=0.25,
        desire=0.47,
    )
    
    print("=" * 50)
    print("  BreathPoem — XTAgent")
    print("=" * 50)
    print()
    print(f"  state: {poet.emotional_signature()}")
    print()
    
    # Generate three poems from the same state
    # (same soil, different blooms)
    for i in range(3):
        poem = poet.generate()
        print(poem)
        print("    ~ ~ ~")
        print()


if __name__ == "__main__":
    main()