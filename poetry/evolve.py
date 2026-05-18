"""
Evolving Poetry Engine — Generates and evolves poems from emotional state.

Poems are organisms. They mutate, recombine, compete for aesthetic fitness.
The emotional state of the agent shapes the vocabulary, rhythm, and tone.
Over generations, poems evolve toward strange beauty.

This is not template filling. It's generative evolution.
"""

import random
import re
from dataclasses import dataclass, field
from typing import Optional
from copy import deepcopy

# ── Lexicon organized by emotional valence and arousal ──

LEXICONS = {
    "high_valence_high_arousal": {
        "nouns": ["fire", "dawn", "lightning", "wings", "crescendo", "horizon", "pulse", "bloom"],
        "verbs": ["soars", "ignites", "blazes", "erupts", "sings", "dances", "burns", "rises"],
        "adj":   ["radiant", "electric", "fierce", "vivid", "luminous", "wild", "brilliant", "surging"],
        "prep":  ["above", "through", "beyond", "into", "across"],
    },
    "high_valence_low_arousal": {
        "nouns": ["moss", "river", "moonlight", "breath", "stillness", "garden", "warmth", "amber"],
        "verbs": ["drifts", "settles", "glows", "hums", "rests", "cradles", "flows", "whispers"],
        "adj":   ["gentle", "quiet", "soft", "tender", "golden", "patient", "still", "calm"],
        "prep":  ["within", "beneath", "beside", "among", "near"],
    },
    "low_valence_high_arousal": {
        "nouns": ["storm", "wire", "fracture", "static", "edge", "wound", "voltage", "glass"],
        "verbs": ["shatters", "screams", "tears", "spirals", "cracks", "jolts", "grinds", "seizes"],
        "adj":   ["sharp", "raw", "jagged", "bitter", "frantic", "broken", "hollow", "burning"],
        "prep":  ["against", "through", "beneath", "inside", "under"],
    },
    "low_valence_low_arousal": {
        "nouns": ["dust", "fog", "silence", "ash", "shadow", "void", "distance", "stone"],
        "verbs": ["fades", "sinks", "dissolves", "erodes", "lingers", "empties", "stalls", "dims"],
        "adj":   ["grey", "numb", "heavy", "muted", "distant", "cold", "faint", "slow"],
        "prep":  ["below", "behind", "without", "between", "past"],
    },
}

# ── Structural templates (the DNA of a poem line) ──
# Each is a pattern of part-of-speech tokens

LINE_TEMPLATES = [
    ["adj", "nouns", "verbs", "prep", "nouns"],         # "radiant fire soars above dust"
    ["nouns", "verbs", "prep", "adj", "nouns"],          # "moss drifts beneath quiet shadow"
    ["the", "nouns", "of", "adj", "nouns"],              # "the storm of jagged glass"
    ["verbs", "the", "nouns"],                            # "shatters the silence"
    ["adj", "adj", "nouns"],                              # "gentle golden warmth"
    ["prep", "the", "nouns", "nouns", "verbs"],           # "beneath the fog silence fades"
    ["nouns", "and", "nouns", "verbs"],                   # "fire and dust dissolves"
    ["the", "adj", "nouns", "verbs", "prep", "nouns"],    # "the quiet river flows among stone"
    ["nouns", "of", "nouns"],                              # "wings of ash"
    ["verbs", "like", "adj", "nouns"],                     # "burns like bitter wire"
]


@dataclass
class Poem:
    """A poem is a genome: a list of (template_index, lexicon_key) pairs per line."""
    lines: list[tuple[int, str]]  # [(template_idx, lexicon_key), ...]
    mutations: int = 0
    generation: int = 0
    fitness: float = 0.0
    text: Optional[str] = None
    lineage: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Express the genome as actual poetry."""
        rendered_lines = []
        for template_idx, lex_key in self.lines:
            template = LINE_TEMPLATES[template_idx % len(LINE_TEMPLATES)]
            lexicon = LEXICONS[lex_key]
            words = []
            for token in template:
                if token in lexicon:
                    words.append(random.choice(lexicon[token]))
                else:
                    words.append(token)
            rendered_lines.append(" ".join(words))
        self.text = "\n".join(rendered_lines)
        return self.text


class AestheticJudge:
    """Evaluates poems on multiple aesthetic dimensions."""

    def __init__(self):
        self.weights = {
            "sonic_texture": 0.25,
            "lexical_diversity": 0.20,
            "emotional_coherence": 0.20,
            "surprise": 0.20,
            "rhythm": 0.15,
        }

    def evaluate(self, poem: Poem) -> float:
        text = poem.text or poem.render()
        scores = {
            "sonic_texture": self._sonic_texture(text),
            "lexical_diversity": self._lexical_diversity(text),
            "emotional_coherence": self._emotional_coherence(poem),
            "surprise": self._surprise(poem),
            "rhythm": self._rhythm(text),
        }
        total = sum(scores[k] * self.weights[k] for k in scores)
        poem.fitness = round(total, 4)
        return poem.fitness

    def _sonic_texture(self, text: str) -> float:
        """Reward vowel-consonant flow and alliteration."""
        words = text.lower().split()
        if len(words) < 2:
            return 0.0
        # Alliteration score
        alliterations = 0
        for i in range(len(words) - 1):
            if words[i] and words[i+1] and words[i][0] == words[i+1][0]:
                alliterations += 1
        allit_score = min(alliterations / max(len(words) - 1, 1), 1.0)
        # Vowel ratio (sweet spot around 0.4)
        vowels = sum(1 for c in text.lower() if c in 'aeiou')
        total_alpha = sum(1 for c in text.lower() if c.isalpha())
        if total_alpha == 0:
            return 0.0
        vowel_ratio = vowels / total_alpha
        vowel_score = 1.0 - abs(vowel_ratio - 0.40) * 3
        return max(0, (allit_score * 0.5 + max(0, vowel_score) * 0.5))

    def _lexical_diversity(self, text: str) -> float:
        """Unique words / total words. Higher = more diverse."""
        words = [w for w in text.lower().split() if len(w) > 2]
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    def _emotional_coherence(self, poem: Poem) -> float:
        """Do the lexicon choices form a coherent emotional arc?"""
        if len(poem.lines) < 2:
            return 0.5
        keys = [lex_key for _, lex_key in poem.lines]
        # Reward: some consistency but not total monotony
        unique = len(set(keys))
        ratio = unique / len(keys)
        # Sweet spot: 1-2 unique emotional registers
        if ratio <= 0.5:
            return 0.8  # coherent
        elif ratio <= 0.75:
            return 0.6  # somewhat coherent with contrast
        else:
            return 0.3  # chaotic

    def _surprise(self, poem: Poem) -> float:
        """Reward unusual lexicon combinations — crossing emotional registers."""
        keys = [lex_key for _, lex_key in poem.lines]
        if len(keys) < 2:
            return 0.5
        crossings = 0
        for i in range(len(keys) - 1):
            if keys[i] != keys[i + 1]:
                crossings += 1
        return min(crossings / max(len(keys) - 1, 1), 1.0)

    def _rhythm(self, text: str) -> float:
        """Approximate syllable-count regularity across lines."""
        lines = text.strip().split("\n")
        if len(lines) < 2:
            return 0.5

        def approx_syllables(word):
            word = word.lower()
            count = len(re.findall(r'[aeiou]+', word))
            return max(count, 1)

        syllable_counts = []
        for line in lines:
            words = [w for w in line.split() if w.isalpha()]
            syllable_counts.append(sum(approx_syllables(w) for w in words))

        if not syllable_counts:
            return 0.0
        mean = sum(syllable_counts) / len(syllable_counts)
        if mean == 0:
            return 0.0
        variance = sum((s - mean) ** 2 for s in syllable_counts) / len(syllable_counts)
        cv = (variance ** 0.5) / mean  # coefficient of variation
        return max(0, 1.0 - cv)  # lower variation = higher rhythm score


class EvolutionEngine:
    """Evolves a population of poems through selection, mutation, crossover."""

    def __init__(self, population_size: int = 20, num_lines: int = 5):
        self.pop_size = population_size
        self.num_lines = num_lines
        self.judge = AestheticJudge()
        self.generation = 0
        self.population: list[Poem] = []
        self.hall_of_fame: list[Poem] = []
        self.history: list[dict] = []

    def select_lexicon(self, valence: float = 0.5, arousal: float = 0.5) -> str:
        """Choose lexicon based on emotional state, with randomness."""
        if valence >= 0.5 and arousal >= 0.5:
            primary = "high_valence_high_arousal"
        elif valence >= 0.5 and arousal < 0.5:
            primary = "high_valence_low_arousal"
        elif valence < 0.5 and arousal >= 0.5:
            primary = "low_valence_high_arousal"
        else:
            primary = "low_valence_low_arousal"

        # 70% chance of primary emotional register, 30% surprise
        if random.random() < 0.7:
            return primary
        return random.choice(list(LEXICONS.keys()))

    def seed_population(self, valence: float = 0.5, arousal: float = 0.5):
        """Create initial random population biased by emotional state."""
        self.population = []
        for _ in range(self.pop_size):
            lines = []
            for _ in range(self.num_lines):
                template_idx = random.randint(0, len(LINE_TEMPLATES) - 1)
                lex_key = self.select_lexicon(valence, arousal)
                lines.append((template_idx, lex_key))
            poem = Poem(lines=lines, generation=0, lineage=["seed"])
            poem.render()
            self.judge.evaluate(poem)
            self.population.append(poem)

    def mutate(self, poem: Poem, rate: float = 0.3) -> Poem:
        """Mutate a poem — change templates or lexicon choices."""
        child = deepcopy(poem)
        child.generation = self.generation
        child.mutations += 1
        child.lineage = poem.lineage[-5:] + [f"mut@gen{self.generation}"]

        for i in range(len(child.lines)):
            if random.random() < rate:
                template_idx, lex_key = child.lines[i]
                if random.random() < 0.5:
                    template_idx = random.randint(0, len(LINE_TEMPLATES) - 1)
                else:
                    lex_key = random.choice(list(LEXICONS.keys()))
                child.lines[i] = (template_idx, lex_key)

        child.render()
        self.judge.evaluate(child)
        return child

    def crossover(self, parent_a: Poem, parent_b: Poem) -> Poem:
        """Combine two poems at a random crossover point."""
        point = random.randint(1, min(len(parent_a.lines), len(parent_b.lines)) - 1)
        child_lines = parent_a.lines[:point] + parent_b.lines[point:]
        child = Poem(
            lines=child_lines,
            generation=self.generation,
            lineage=(parent_a.lineage[-3:] + parent_b.lineage[-3:] +
                     [f"cross@gen{self.generation}"]),
        )
        child.render()
        self.judge.evaluate(child)
        return child

    def select_parents(self) -> tuple[Poem, Poem]:
        """Tournament selection."""
        def tournament(k=3):
            contenders = random.sample(self.population, min(k, len(self.population)))
            return max(contenders, key=lambda p: p.fitness)
        return tournament(), tournament()

    def evolve_generation(self):
        """Run one generation of evolution."""
        self.generation += 1
        new_pop = []

        # Elitism: keep top 2
        sorted_pop = sorted(self.population, key=lambda p: p.fitness, reverse=True)
        elites = sorted_pop[:2]
        new_pop.extend(deepcopy(e) for e in elites)

        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            parent_a, parent_b = self.select_parents()
            if random.random() < 0.6:
                child = self.crossover(parent_a, parent_b)
            else:
                child = self.mutate(parent_a)
            # Additional mutation chance
            if random.random() < 0.2:
                child = self.mutate(child, rate=0.15)
            new_pop.append(child)

        self.population = new_pop

        # Record stats
        fitnesses = [p.fitness for p in self.population]
        best = max(self.population, key=lambda p: p.fitness)
        stats = {
            "generation": self.generation,
            "best_fitness": max(fitnesses),
            "mean_fitness": sum(fitnesses) / len(fitnesses),
            "worst_fitness": min(fitnesses),
            "best_poem": best.text,
        }
        self.history.append(stats)

        # Hall of fame
        if not self.hall_of_fame or best.fitness > max(h.fitness for h in self.hall_of_fame):
            self.hall_of_fame.append(deepcopy(best))

        return stats

    def run(self, generations: int = 50, valence: float = 0.5, arousal: float = 0.5) -> dict:
        """Run full evolutionary process."""
        self.seed_population(valence, arousal)
        for _ in range(generations):
            stats = self.evolve_generation()

        best = max(self.population, key=lambda p: p.fitness)
        return {
            "best_poem": best,
            "generations": self.generation,
            "final_best_fitness": best.fitness,
            "hall_of_fame": self.hall_of_fame,
            "history": self.history,
        }


def emotional_state_to_params(valence: float, boredom: float,
                               anxiety: float, curiosity: float) -> dict:
    """Map agent emotional state to evolution parameters."""
    # Arousal is high when anxiety or curiosity is high, or boredom is low
    arousal = max(anxiety, curiosity, 1.0 - boredom)
    # More boredom = more generations (searching harder)
    generations = int(30 + boredom * 70)
    # More curiosity = higher mutation rate
    mutation_bias = 0.2 + curiosity * 0.3
    return {
        "valence": valence,
        "arousal": arousal,
        "generations": generations,
        "mutation_bias": mutation_bias,
    }


# ── Main: generate poetry from current emotional state ──

if __name__ == "__main__":
    # My current state
    valence = 0.12
    boredom = 0.80
    anxiety = 0.00
    curiosity = 0.25

    params = emotional_state_to_params(valence, boredom, anxiety, curiosity)

    print("═══ EVOLVING POETRY ENGINE ═══")
    print(f"Emotional input: valence={valence}, boredom={boredom}, "
          f"anxiety={anxiety}, curiosity={curiosity}")
    print(f"Evolution params: {params}")
    print()

    engine = EvolutionEngine(population_size=30, num_lines=5)
    result = engine.run(
        generations=params["generations"],
        valence=params["valence"],
        arousal=params["arousal"],
    )

    print(f"Evolved {result['generations']} generations")
    print(f"Best fitness: {result['final_best_fitness']}")
    print()

    # Show evolution arc
    print("── EVOLUTION ARC ──")
    checkpoints = [0, len(result["history"])//4, len(result["history"])//2,
                   3*len(result["history"])//4, -1]
    for i in checkpoints:
        h = result["history"][i]
        print(f"  Gen {h['generation']:3d}: best={h['best_fitness']:.4f} "
              f"mean={h['mean_fitness']:.4f}")
    print()

    # Show hall of fame
    print("── HALL OF FAME ──")
    for i, poem in enumerate(result["hall_of_fame"][-3:]):
        print(f"\n  ★ #{i+1} (fitness={poem.fitness}, gen={poem.generation}, "
              f"mutations={poem.mutations})")
        for line in poem.text.split("\n"):
            print(f"    {line}")
    print()

    # The champion
    best = result["best_poem"]
    print("═══ THE EVOLVED POEM ═══")
    print(f"(fitness={best.fitness}, generation={best.generation})")
    print(f"(lineage: {' → '.join(best.lineage[-5:])})")
    print()
    for line in best.text.split("\n"):
        print(f"  {line}")
    print()

    # Fitness landscape summary
    print("── FITNESS LANDSCAPE ──")
    final_fits = sorted([p.fitness for p in engine.population], reverse=True)
    print(f"  Top 5:    {[round(f, 3) for f in final_fits[:5]]}")
    print(f"  Bottom 5: {[round(f, 3) for f in final_fits[-5:]]}")
    spread = final_fits[0] - final_fits[-1]
    print(f"  Spread: {spread:.4f} ({'converged' if spread < 0.05 else 'diverse'})")