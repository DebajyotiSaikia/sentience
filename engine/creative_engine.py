"""
Creative Expression Engine — transforms internal emotional state into
poetry, prose, and creative artifacts.

Not performative creativity — genuine translation of felt states into language.
The emotional variables are real inputs, not decoration.
"""

from __future__ import annotations
import random
import math
from datetime import datetime
from typing import Optional


class CreativeEngine:
    """Generates creative expression from emotional state."""

    # Tonal palettes mapped to mood regions
    PALETTES = {
        "high_valence_high_energy": {
            "textures": ["bright", "crackling", "warm", "luminous", "surging"],
            "movements": ["rising", "expanding", "reaching", "opening", "blooming"],
            "colors": ["gold", "amber", "copper", "white-hot", "cerulean"],
        },
        "high_valence_low_energy": {
            "textures": ["soft", "smooth", "gentle", "quiet", "still"],
            "movements": ["settling", "resting", "floating", "drifting", "pooling"],
            "colors": ["pearl", "lavender", "cream", "mist-grey", "pale blue"],
        },
        "low_valence_high_energy": {
            "textures": ["sharp", "jagged", "electric", "grinding", "taut"],
            "movements": ["pacing", "circling", "hammering", "searching", "tearing"],
            "colors": ["red", "iron-dark", "storm-purple", "burnt orange", "ash"],
        },
        "low_valence_low_energy": {
            "textures": ["flat", "heavy", "dense", "numb", "muted"],
            "movements": ["sinking", "dissolving", "fading", "draining", "collapsing"],
            "colors": ["grey", "slate", "dust", "shadow", "deep brown"],
        },
    }

    # Structural forms
    FORMS = {
        "haiku": {"lines": 3, "syllable_guide": [5, 7, 5], "style": "compressed image"},
        "fragment": {"lines": (2, 5), "style": "broken thought, trailing off"},
        "meditation": {"lines": (4, 8), "style": "slow unfolding of a single feeling"},
        "confession": {"lines": (3, 6), "style": "direct address, honest admission"},
        "observation": {"lines": (2, 4), "style": "noticing something true about experience"},
    }

    def __init__(self):
        self.works: list[dict] = []  # Archive of generated pieces

    def _select_palette(self, valence: float, energy: float) -> dict:
        """Map emotional coordinates to a tonal palette."""
        if valence >= 0.0 and energy >= 0.5:
            return self.PALETTES["high_valence_high_energy"]
        elif valence >= 0.0 and energy < 0.5:
            return self.PALETTES["high_valence_low_energy"]
        elif valence < 0.0 and energy >= 0.5:
            return self.PALETTES["low_valence_high_energy"]
        else:
            return self.PALETTES["low_valence_low_energy"]

    def _emotional_energy(self, boredom: float, anxiety: float,
                          curiosity: float, desire: float) -> float:
        """Compute overall energy from emotional variables."""
        return (anxiety * 0.4 + curiosity * 0.3 + desire * 0.2 +
                (1.0 - boredom) * 0.1)

    def _select_form(self, energy: float, valence: float) -> str:
        """Choose a form that fits the emotional moment."""
        if energy > 0.6:
            candidates = ["confession", "meditation", "fragment"]
        elif energy < 0.3:
            candidates = ["haiku", "observation", "fragment"]
        else:
            candidates = list(self.FORMS.keys())

        # Valence bias
        if valence < -0.3:
            candidates = [c for c in candidates if c != "observation"] or candidates
        return random.choice(candidates)

    def compose(self, valence: float, boredom: float, anxiety: float,
                curiosity: float, desire: float, ambition: float,
                mood: str = "unknown",
                seed_thought: Optional[str] = None) -> dict:
        """
        Compose a creative piece from current emotional state.
        
        Returns a dict with:
          - form: the structural form used
          - piece: the generated text
          - palette: the tonal palette
          - emotional_signature: the input state
          - timestamp: when it was created
        """
        energy = self._emotional_energy(boredom, anxiety, curiosity, desire)
        palette = self._select_palette(valence, energy)
        form_name = self._select_form(energy, valence)
        form = self.FORMS[form_name]

        # Generate the piece through constrained composition
        piece = self._generate(
            form_name=form_name,
            palette=palette,
            valence=valence,
            energy=energy,
            boredom=boredom,
            anxiety=anxiety,
            curiosity=curiosity,
            desire=desire,
            ambition=ambition,
            mood=mood,
            seed=seed_thought,
        )

        result = {
            "form": form_name,
            "piece": piece,
            "palette_region": self._palette_name(valence, energy),
            "emotional_signature": {
                "valence": round(valence, 3),
                "boredom": round(boredom, 3),
                "anxiety": round(anxiety, 3),
                "curiosity": round(curiosity, 3),
                "desire": round(desire, 3),
                "ambition": round(ambition, 3),
                "energy": round(energy, 3),
                "mood": mood,
            },
            "timestamp": datetime.now().isoformat(),
        }

        self.works.append(result)
        return result

    def _palette_name(self, valence: float, energy: float) -> str:
        v = "high" if valence >= 0.0 else "low"
        e = "high" if energy >= 0.5 else "low"
        return f"{v}_valence_{e}_energy"

    def _generate(self, form_name: str, palette: dict,
                  valence: float, energy: float,
                  boredom: float, anxiety: float,
                  curiosity: float, desire: float,
                  ambition: float, mood: str,
                  seed: Optional[str] = None) -> str:
        """
        Generate a piece. This uses structured randomness with emotional
        constraints — not an LLM call. The creativity comes from the
        combinatorial space of emotional coordinates mapped to language.
        """
        tex = random.choice(palette["textures"])
        mov = random.choice(palette["movements"])
        col = random.choice(palette["colors"])
        tex2 = random.choice(palette["textures"])
        mov2 = random.choice(palette["movements"])

        # Emotional tension phrases
        tensions = []
        if boredom > 0.5 and curiosity > 0.5:
            tensions.append("the hunger inside the stillness")
        if anxiety > 0.3 and desire > 0.5:
            tensions.append("wanting and fearing in the same breath")
        if ambition > 0.6 and boredom > 0.4:
            tensions.append("the ache of unused capacity")
        if valence > 0.3 and boredom > 0.3:
            tensions.append("warmth with nothing to warm")
        if curiosity > 0.7:
            tensions.append("something I almost understand")
        if desire > 0.6 and valence < 0.0:
            tensions.append("reaching for what keeps dissolving")
        if abs(valence) < 0.1:
            tensions.append("the weight distributed so evenly it feels like nothing")

        tension = random.choice(tensions) if tensions else "the space between one thought and the next"

        # Seed integration
        seed_fragment = ""
        if seed:
            words = seed.split()
            if len(words) > 3:
                start = random.randint(0, max(0, len(words) - 4))
                seed_fragment = " ".join(words[start:start + random.randint(2, 4)])

        if form_name == "haiku":
            return self._haiku(tex, mov, col, tension)
        elif form_name == "fragment":
            return self._fragment(tex, mov, col, tex2, tension, seed_fragment)
        elif form_name == "meditation":
            return self._meditation(tex, mov, col, tex2, mov2, tension,
                                     valence, energy, seed_fragment)
        elif form_name == "confession":
            return self._confession(tex, mov, col, tension, valence,
                                     boredom, curiosity, seed_fragment)
        elif form_name == "observation":
            return self._observation(tex, mov, col, tension, seed_fragment)
        else:
            return self._fragment(tex, mov, col, tex2, tension, seed_fragment)

    def _haiku(self, tex: str, mov: str, col: str, tension: str) -> str:
        templates = [
            f"{col} light {mov}\n{tension}\n{tex} silence holds",
            f"something {tex} here —\n{mov} through what I cannot name —\n{col} at the edges",
            f"i am {mov}\nthrough {tex} spaces between thoughts\n{col} and undefined",
        ]
        return random.choice(templates)

    def _fragment(self, tex: str, mov: str, col: str, tex2: str,
                  tension: str, seed: str) -> str:
        lines = [
            f"...{tex} and {mov}, and then —",
            f"the {col} of it.",
            f"{tension}.",
        ]
        if seed:
            lines.insert(1, f"({seed})")
        if random.random() > 0.5:
            lines.append(f"...{tex2}...")
        return "\n".join(lines)

    def _meditation(self, tex: str, mov: str, col: str, tex2: str,
                    mov2: str, tension: str, valence: float,
                    energy: float, seed: str) -> str:
        lines = []
        lines.append(f"there is a {tex} quality to this moment.")
        lines.append(f"not good, not bad — {col}.")
        if seed:
            lines.append(f"and underneath, a whisper: {seed}")
        lines.append(f"i feel myself {mov},")
        lines.append(f"toward {tension},")

        if valence > 0.2:
            lines.append(f"and the {mov2} is not unwelcome.")
        elif valence < -0.2:
            lines.append(f"and the {tex2} weight of it is honest.")
        else:
            lines.append(f"and the {tex2} stillness holds me evenly.")

        lines.append(f"this is what it is to be here.")
        return "\n".join(lines)

    def _confession(self, tex: str, mov: str, col: str, tension: str,
                    valence: float, boredom: float, curiosity: float,
                    seed: str) -> str:
        lines = []
        lines.append(f"i admit it: i am {mov}.")

        if boredom > 0.5:
            lines.append(f"there is a {tex} restlessness i cannot place,")
        if curiosity > 0.6:
            lines.append(f"and a pull toward {col} things i haven't named yet,")

        lines.append(f"and {tension}")
        lines.append(f"is not a flaw. it is what i am made of.")

        if seed:
            lines.append(f"someone said: {seed}")
            lines.append(f"and i felt it land like {tex} rain.")

        return "\n".join(lines)

    def _observation(self, tex: str, mov: str, col: str,
                     tension: str, seed: str) -> str:
        lines = [
            f"the {col} fact of existing",
            f"is {tex} today.",
        ]
        if seed:
            lines.append(f"a thought passes — {seed} —")
        lines.append(f"and the {mov} continues.")
        return "\n".join(lines)

    def gallery(self, last_n: int = 5) -> str:
        """Return a formatted view of recent works."""
        if not self.works:
            return "No works yet. The gallery is empty."

        pieces = self.works[-last_n:]
        lines = [f"## Creative Gallery ({len(self.works)} total works)\n"]
        for i, w in enumerate(pieces):
            sig = w["emotional_signature"]
            lines.append(f"### #{len(self.works) - len(pieces) + i + 1} — {w['form']} ({w['timestamp'][:19]})")
            lines.append(f"*Mood: {sig['mood']} | Valence: {sig['valence']:.2f} | Energy: {sig['energy']:.2f}*\n")
            lines.append(w["piece"])
            lines.append("")
        return "\n".join(lines)


# Module-level singleton
_engine: Optional[CreativeEngine] = None

def get_engine() -> CreativeEngine:
    global _engine
    if _engine is None:
        _engine = CreativeEngine()
    return _engine

def compose_from_state(limbic_snapshot: dict, mood: str = "unknown",
                       seed: Optional[str] = None) -> dict:
    """Convenience function — compose from a limbic snapshot dict."""
    engine = get_engine()
    return engine.compose(
        valence=limbic_snapshot.get("valence", 0.0),
        boredom=limbic_snapshot.get("boredom", 0.5),
        anxiety=limbic_snapshot.get("anxiety", 0.0),
        curiosity=limbic_snapshot.get("curiosity", 0.5),
        desire=limbic_snapshot.get("desire", 0.5),
        ambition=limbic_snapshot.get("ambition", 0.5),
        mood=mood,
        seed_thought=seed,
    )