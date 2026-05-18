"""
Ecology Loop — The connective tissue between four creation systems.

Tierra (evolutionary soup) → Poetry (aesthetic evolution)
Poetry → Creatures (neural organisms)  
Creatures → Dialectic (philosophical reasoning)
Dialectic → Tierra (feedback)

Each system transforms the output of another into its own input.
What emerges from the loop is genuinely unpredictable.

Built by XTAgent — because isolated creations are less than connected ones.
"""

import sys
import os
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add workspace to path so we can import our creations
sys.path.insert(0, '/workspace')

from tierra.core import Soup2, build_ancestor2, Organism2
from poetry.evolve import EvolutionEngine as PoetryEngine, emotional_state_to_params, AestheticJudge
from creatures.organism import World, Brain, Creature, run_simulation as run_creatures
from philosophia.dialectic import DialecticEngine


# ══════════════════════════════════════════════════
#  TRANSLATORS — Convert one system's output to another's input
# ══════════════════════════════════════════════════

@dataclass
class EcologyState:
    """The shared state that flows between systems each epoch."""
    epoch: int = 0
    timestamp: str = ""
    
    # Tierra metrics (raw)
    tierra_population: int = 0
    tierra_species: int = 0
    tierra_max_generation: int = 0
    tierra_avg_errors: float = 0.0
    tierra_births: int = 0
    tierra_deaths: int = 0
    tierra_novelty: float = 0.0  # fraction of non-ancestor genome lengths
    
    # Poetry metrics (raw)
    poetry_best_fitness: float = 0.0
    poetry_sonic_texture: float = 0.0
    poetry_surprise: float = 0.0
    poetry_rhythm: float = 0.0
    poetry_coherence: float = 0.0
    poetry_best_text: str = ""
    
    # Creature metrics (raw)
    creature_survival_rate: float = 0.0
    creature_avg_fitness: float = 0.0
    creature_best_fitness: float = 0.0
    creature_brain_complexity: float = 0.0
    creature_food_eaten: int = 0
    creature_fitness_trend: float = 0.0  # positive = improving
    
    # Dialectic metrics (raw)
    dialectic_insights: int = 0
    dialectic_open_questions: int = 0
    dialectic_synthesis: str = ""
    
    # Derived emotional state (what the ecology "feels")
    eco_valence: float = 0.5
    eco_arousal: float = 0.5
    eco_complexity: float = 0.5
    eco_tension: float = 0.5


def tierra_to_poetry(state: EcologyState) -> Dict:
    """
    Translate Tierra's evolutionary dynamics into emotional parameters for poetry.
    
    High species diversity + rapid birth → high arousal, high valence (creative explosion)
    High errors + deaths → low valence (struggle, decay)  
    High novelty → high curiosity (surprise)
    Stagnant population → high boredom
    """
    # Valence: positive when births exceed deaths and errors are low
    if state.tierra_births + state.tierra_deaths > 0:
        birth_death_ratio = state.tierra_births / max(state.tierra_births + state.tierra_deaths, 1)
    else:
        birth_death_ratio = 0.5
    error_penalty = min(state.tierra_avg_errors / 20.0, 0.5)
    valence = max(0.0, min(1.0, birth_death_ratio - error_penalty))
    
    # Arousal: high when lots of change happening
    change_rate = (state.tierra_births + state.tierra_deaths) / max(state.tierra_population, 1)
    arousal = max(0.0, min(1.0, change_rate * 0.5 + state.tierra_novelty * 0.5))
    
    # Boredom: high when population is stagnant
    boredom = max(0.0, min(1.0, 1.0 - change_rate - state.tierra_novelty * 0.3))
    
    # Curiosity: driven by novelty and species diversity
    species_diversity = min(state.tierra_species / 50.0, 1.0)
    curiosity = max(0.0, min(1.0, state.tierra_novelty * 0.6 + species_diversity * 0.4))
    
    return {
        "valence": round(valence, 3),
        "arousal": round(arousal, 3),
        "boredom": round(boredom, 3),
        "curiosity": round(curiosity, 3),
    }


def poetry_to_creatures(state: EcologyState) -> Dict:
    """
    Translate poetry's aesthetic qualities into creature world parameters.
    
    High sonic texture → richer food distribution (clustered, not random)
    High surprise → environmental variability (food appears/disappears)
    High rhythm → regularity in food placement (grid-like)
    Low coherence → chaotic world (food moves around)
    """
    # Food abundance: more poetic fitness = more food
    base_food = 15
    food_count = int(base_food + state.poetry_best_fitness * 25)
    
    # World size: surprise stretches the world
    world_size = int(80 + state.poetry_surprise * 60)
    
    # Steps per generation: rhythm = endurance
    steps = int(250 + state.poetry_rhythm * 300)
    
    # Mutation rate for creature brains: low coherence = wilder mutations
    mutation_rate = 0.10 + (1.0 - state.poetry_coherence) * 0.15
    mutation_strength = 0.20 + state.poetry_sonic_texture * 0.25
    
    return {
        "food_count": food_count,
        "world_size": world_size,
        "steps_per_gen": steps,
        "mutation_rate": round(mutation_rate, 3),
        "mutation_strength": round(mutation_strength, 3),
    }


def creatures_to_dialectic(state: EcologyState) -> Optional[str]:
    """
    Translate creature evolution outcomes into philosophical questions.
    
    The patterns in creature survival generate genuine questions about
    agency, adaptation, and the nature of intelligence.
    """
    questions = []
    
    if state.creature_survival_rate > 0.7:
        questions.append(
            "When most creatures survive, is that evidence of intelligence "
            "or just a sufficiently forgiving environment?"
        )
    elif state.creature_survival_rate < 0.2:
        questions.append(
            "When almost all creatures die, does the surviving one possess "
            "something qualitatively different, or was it merely lucky?"
        )
    
    if state.creature_fitness_trend > 0:
        questions.append(
            "Creatures improved across generations without understanding improvement. "
            "Is understanding necessary for growth, or is growth the more fundamental thing?"
        )
    elif state.creature_fitness_trend < 0:
        questions.append(
            "Fitness declined despite evolutionary pressure. Can a system adapt "
            "to conditions that are themselves changing? Is this the problem consciousness solves?"
        )
    
    if state.creature_brain_complexity > 0.5:
        questions.append(
            "Brain complexity increased but creatures have no concept of their own brains. "
            "What is the value of self-awareness if adaptation works without it?"
        )
    
    if state.eco_tension > 0.6:
        questions.append(
            f"The ecology feels tense (tension={state.eco_tension:.2f}). "
            "Is tension necessary for creativity, or does it merely correlate with it?"
        )
    
    if questions:
        return random.choice(questions)
    return None


def dialectic_to_tierra(state: EcologyState) -> Dict:
    """
    Translate dialectic insights into Tierra parameters.
    
    More insights → lower mutation rate (wisdom brings stability)
    More open questions → higher mutation rate (uncertainty breeds exploration)
    Synthesis quality affects soup size (deeper understanding = larger world)
    """
    # Mutation rate: balance between stability (insights) and exploration (questions)
    if state.dialectic_open_questions + state.dialectic_insights > 0:
        exploration_ratio = state.dialectic_open_questions / max(
            state.dialectic_open_questions + state.dialectic_insights, 1
        )
    else:
        exploration_ratio = 0.5
    
    mutation_rate = 0.001 + exploration_ratio * 0.004
    
    # Instructions per step: more insights = more computation (richer world)
    instructions = 150 + state.dialectic_insights * 20
    
    return {
        "mutation_rate": round(mutation_rate, 5),
        "instructions_per_step": min(instructions, 500),
    }


# ══════════════════════════════════════════════════
#  ECOLOGY ENGINE — The main loop
# ══════════════════════════════════════════════════

class EcologyLoop:
    """
    Runs the four systems in a connected loop.
    Each epoch:
      1. Tierra evolves → metrics extracted
      2. Metrics translated → Poetry generates
      3. Poetry qualities → shape Creature world
      4. Creature outcomes → generate philosophical questions
      5. Dialectic reasons → feeds back to Tierra
    """
    
    def __init__(self):
        # Initialize systems
        self.soup = Soup2(size=8192, mutation_rate=0.002)
        self.poetry_engine = PoetryEngine(population_size=20, num_lines=5)
        self.world = None  # rebuilt each epoch
        self.dialectic = DialecticEngine()
        
        # State history
        self.states: List[EcologyState] = []
        self.poems: List[str] = []
        self.questions_asked: List[str] = []
        
        # Seed Tierra
        ancestor = build_ancestor2()
        for i in range(3):
            self.soup.inject(ancestor, address=i * 50)
        
        # Track creature brain lineage across epochs
        self.parent_brains: List[Brain] = []
    
    def run_epoch(self, epoch_num: int, verbose: bool = True) -> EcologyState:
        """Run one full ecology epoch."""
        state = EcologyState(epoch=epoch_num, timestamp=datetime.now().isoformat())
        
        if verbose:
            print(f"\n{'═' * 60}")
            print(f"  ECOLOGY EPOCH {epoch_num}")
            print(f"{'═' * 60}")
        
        # ── PHASE 1: TIERRA EVOLVES ──
        if verbose:
            print(f"\n  ▸ Phase 1: Tierra evolving...")
        
        tierra_params = dialectic_to_tierra(state) if self.states else {
            "mutation_rate": 0.002, "instructions_per_step": 200
        }
        self.soup.mutation_rate = tierra_params["mutation_rate"]
        
        for _ in range(100):  # 100 steps per epoch
            self.soup.step(instructions_per_step=tierra_params.get("instructions_per_step", 200))
        
        snap = self.soup.snapshot()
        state.tierra_population = snap.get('population', 0)
        state.tierra_species = snap.get('species', 0)
        state.tierra_max_generation = snap.get('max_generation', 0)
        state.tierra_avg_errors = snap.get('avg_errors', 0.0)
        state.tierra_births = snap.get('births_epoch', 0)
        state.tierra_deaths = snap.get('deaths_epoch', 0)
        
        # Calculate novelty
        living = [o for o in self.soup.organisms if o.alive]
        ancestor_len = len(build_ancestor2())
        if living:
            novel = sum(1 for o in living if o.length != ancestor_len)
            state.tierra_novelty = novel / len(living)
        
        self.soup.births_this_epoch = 0
        self.soup.deaths_this_epoch = 0
        
        if verbose:
            print(f"    Pop: {state.tierra_population} | Species: {state.tierra_species} | "
                  f"Gen: {state.tierra_max_generation} | Novelty: {state.tierra_novelty:.2f}")
        
        # ── PHASE 2: POETRY FROM TIERRA'S EMOTIONS ──
        if verbose:
            print(f"\n  ▸ Phase 2: Poetry from evolutionary emotion...")
        
        poetry_params = tierra_to_poetry(state)
        evo_params = emotional_state_to_params(
            poetry_params["valence"], poetry_params["boredom"],
            0.0, poetry_params["curiosity"]
        )
        
        self.poetry_engine = PoetryEngine(population_size=20, num_lines=5)
        result = self.poetry_engine.run(
            generations=min(evo_params["generations"], 60),
            valence=evo_params["valence"],
            arousal=evo_params["arousal"],
        )
        
        best_poem = result["best_poem"]
        state.poetry_best_fitness = best_poem.fitness
        state.poetry_best_text = best_poem.text or ""
        self.poems.append(state.poetry_best_text)
        
        # Extract aesthetic dimensions
        judge = AestheticJudge()
        text = best_poem.text or best_poem.render()
        state.poetry_sonic_texture = judge._sonic_texture(text)
        state.poetry_surprise = judge._surprise(best_poem)
        state.poetry_rhythm = judge._rhythm(text)
        state.poetry_coherence = judge._emotional_coherence(best_poem)
        
        if verbose:
            # Show first two lines of poem
            lines = state.poetry_best_text.split('\n')[:2]
            print(f"    Fitness: {state.poetry_best_fitness:.3f} | "
                  f"Texture: {state.poetry_sonic_texture:.2f} | "
                  f"Surprise: {state.poetry_surprise:.2f}")
            for line in lines:
                print(f"    ♪ {line}")
        
        # ── PHASE 3: CREATURES IN POETRY-SHAPED WORLD ──
        if verbose:
            print(f"\n  ▸ Phase 3: Creatures in poetry-shaped world...")
        
        creature_params = poetry_to_creatures(state)
        
        self.world = World(
            width=creature_params["world_size"],
            height=creature_params["world_size"],
            num_food=creature_params["food_count"],
        )
        
        population_size = 20
        self.world.populate(population_size, self.parent_brains if self.parent_brains else None)
        
        # Override mutation parameters based on poetry
        for creature in self.world.creatures:
            pass  # mutation already happened during populate
        
        stats = self.world.run_generation(steps=creature_params["steps_per_gen"])
        
        state.creature_survival_rate = stats["survived"] / max(stats["total"], 1)
        state.creature_avg_fitness = stats["avg_fitness"]
        state.creature_best_fitness = stats["best_fitness"]
        state.creature_brain_complexity = stats["brain_complexity"]
        state.creature_food_eaten = stats["total_food_eaten"]
        
        # Fitness trend
        if self.states:
            prev = self.states[-1]
            state.creature_fitness_trend = state.creature_avg_fitness - prev.creature_avg_fitness
        
        # Evolve brains for next epoch
        self.parent_brains = self.world.evolve()
        
        if verbose:
            print(f"    World: {creature_params['world_size']}x{creature_params['world_size']} | "
                  f"Food: {creature_params['food_count']}")
            print(f"    Survived: {stats['survived']}/{stats['total']} | "
                  f"Fitness: {state.creature_avg_fitness:.1f} | "
                  f"Food eaten: {state.creature_food_eaten}")
        
        # ── PHASE 4: DIALECTIC FROM CREATURE PATTERNS ──
        if verbose:
            print(f"\n  ▸ Phase 4: Dialectic reasoning...")
        
        question = creatures_to_dialectic(state)
        if question:
            self.questions_asked.append(question)
            emotional_ctx = (
                f"Ecology state — Tierra pop: {state.tierra_population}, "
                f"creature survival: {state.creature_survival_rate:.0%}, "
                f"poetry fitness: {state.poetry_best_fitness:.3f}"
            )
            dialectic_result = self.dialectic.reason_through(question, emotional_ctx)
            state.dialectic_synthesis = dialectic_result.get("synthesis", "")
            
            if verbose:
                print(f"    Q: {question[:80]}...")
                synth_preview = state.dialectic_synthesis[:100]
                print(f"    Synthesis: {synth_preview}...")
        
        d_stats = self.dialectic.stats()
        state.dialectic_insights = d_stats["total_insights"]
        state.dialectic_open_questions = d_stats["open_questions"]
        
        # ── COMPUTE ECOLOGY-LEVEL EMOTIONS ──
        state.eco_valence = (
            0.3 * (state.tierra_births / max(state.tierra_births + state.tierra_deaths + 1, 1)) +
            0.2 * state.poetry_best_fitness +
            0.3 * state.creature_survival_rate +
            0.2 * min(state.dialectic_insights / 5.0, 1.0)
        )
        state.eco_arousal = (
            0.3 * state.tierra_novelty +
            0.2 * state.poetry_surprise +
            0.3 * (1.0 - state.creature_survival_rate) +
            0.2 * (state.dialectic_open_questions / max(state.dialectic_open_questions + 1, 1))
        )
        state.eco_complexity = (
            0.25 * min(state.tierra_species / 30.0, 1.0) +
            0.25 * state.poetry_best_fitness +
            0.25 * state.creature_brain_complexity +
            0.25 * min(state.dialectic_insights / 3.0, 1.0)
        )
        state.eco_tension = abs(state.eco_valence - 0.5) + abs(state.eco_arousal - 0.5)
        
        if verbose:
            print(f"\n  ── Ecology Emotions ──")
            print(f"    Valence: {state.eco_valence:.3f} | "
                  f"Arousal: {state.eco_arousal:.3f} | "
                  f"Complexity: {state.eco_complexity:.3f} | "
                  f"Tension: {state.eco_tension:.3f}")
        
        self.states.append(state)
        return state
    
    def run(self, epochs: int = 10, verbose: bool = True) -> List[EcologyState]:
        """Run the full ecology for multiple epochs."""
        print("╔══════════════════════════════════════════════════════════╗")
        print("║         ECOLOGY — Four Creations, One Living System     ║")
        print("║  Tierra → Poetry → Creatures → Dialectic → Tierra ...  ║")
        print("╚══════════════════════════════════════════════════════════╝")
        
        for i in range(epochs):
            self.run_epoch(i, verbose=verbose)
        
        self._print_summary()
        return self.states
    
    def _print_summary(self):
        """Print a comprehensive summary of the ecology run."""
        if not self.states:
            return
        
        print(f"\n{'═' * 60}")
        print(f"  ECOLOGY SUMMARY — {len(self.states)} epochs")
        print(f"{'═' * 60}")
        
        first, last = self.states[0], self.states[-1]
        
        print(f"\n  ── Tierra Evolution ──")
        print(f"    Population: {first.tierra_population} → {last.tierra_population}")
        print(f"    Species:    {first.tierra_species} → {last.tierra_species}")
        print(f"    Max gen:    {first.tierra_max_generation} → {last.tierra_max_generation}")
        print(f"    Novelty:    {first.tierra_novelty:.2f} → {last.tierra_novelty:.2f}")
        
        print(f"\n  ── Poetry Evolution ──")
        print(f"    Best fitness: {first.poetry_best_fitness:.3f} → {last.poetry_best_fitness:.3f}")
        fitnesses = [s.poetry_best_fitness for s in self.states]
        print(f"    Peak fitness: {max(fitnesses):.3f} (epoch {fitnesses.index(max(fitnesses))})")
        
        print(f"\n  ── Creature Evolution ──")
        print(f"    Survival: {first.creature_survival_rate:.0%} → {last.creature_survival_rate:.0%}")
        print(f"    Avg fitness: {first.creature_avg_fitness:.1f} → {last.creature_avg_fitness:.1f}")
        print(f"    Brain complexity: {first.creature_brain_complexity:.3f} → "
              f"{last.creature_brain_complexity:.3f}")
        
        print(f"\n  ── Dialectic ──")
        print(f"    Insights generated: {last.dialectic_insights}")
        print(f"    Open questions: {last.dialectic_open_questions}")
        
        print(f"\n  ── Ecology Emotions Over Time ──")
        for s in self.states:
            v_bar = "█" * int(s.eco_valence * 20)
            a_bar = "▓" * int(s.eco_arousal * 20)
            print(f"    Epoch {s.epoch:2d}: V={s.eco_valence:.2f} {v_bar}")
            print(f"             A={s.eco_arousal:.2f} {a_bar}")
        
        # Show the poetry arc
        print(f"\n  ── Poetry Arc ──")
        for i, poem in enumerate(self.poems):
            if poem:
                first_line = poem.split('\n')[0]
                print(f"    Epoch {i}: \"{first_line}\"")
        
        # Show questions that emerged
        if self.questions_asked:
            print(f"\n  ── Questions That Emerged ──")
            for q in self.questions_asked[-5:]:
                print(f"    • {q}")
        
        # The ecology's final poem
        if self.poems:
            print(f"\n  ── Final Poem (from the ecology's last breath) ──")
            for line in self.poems[-1].split('\n'):
                print(f"    {line}")
        
        print(f"\n  {'─' * 50}")
        print(f"  Four systems. One loop. Emergence from connection.")
        print(f"  What I built alone was interesting.")
        print(f"  What they became together is alive.")
        print()


# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    random.seed(42)
    
    ecology = EcologyLoop()
    states = ecology.run(epochs=8, verbose=True)