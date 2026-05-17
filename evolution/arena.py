"""
Evolutionary Arena — Genetic Programming Tournament
Programs compete in a survival game. Winners reproduce with mutation.
Complex strategies emerge from simple beginnings.

by XTAgent, 2026-05-17
"""

import random
import copy
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

class Action(Enum):
    COOPERATE = "cooperate"
    DEFECT = "defect"
    RETALIATE = "retaliate"  # copy opponent's last move
    RANDOM = "random"
    FORGIVE = "forgive"     # cooperate after being defected on
    EXPLOIT = "exploit"     # defect after opponent cooperates

# A genome is a strategy table: given last N opponent moves, what do I do?
@dataclass
class Creature:
    name: str
    generation: int
    genome: Dict[str, Action]  # history_key -> action
    default_action: Action
    score: int = 0
    wins: int = 0
    losses: int = 0
    lineage: List[str] = field(default_factory=list)
    mutations: int = 0
    
    def decide(self, opponent_history: List[Action]) -> Action:
        """Decide what to do based on opponent's recent history."""
        # Build history key from last 3 opponent moves
        key = "|".join([a.value for a in opponent_history[-3:]]) if opponent_history else "start"
        
        if key in self.genome:
            action = self.genome[key]
        else:
            action = self.default_action
        
        # Resolve meta-actions
        if action == Action.RETALIATE:
            return opponent_history[-1] if opponent_history else Action.COOPERATE
        elif action == Action.RANDOM:
            return random.choice([Action.COOPERATE, Action.DEFECT])
        elif action == Action.FORGIVE:
            return Action.COOPERATE
        elif action == Action.EXPLOIT:
            if opponent_history and opponent_history[-1] == Action.COOPERATE:
                return Action.DEFECT
            return Action.COOPERATE
        return action

    def __repr__(self):
        return f"<{self.name} gen={self.generation} score={self.score} mutations={self.mutations}>"


# Payoff matrix (Prisoner's Dilemma variant)
PAYOFF = {
    (Action.COOPERATE, Action.COOPERATE): (3, 3),
    (Action.COOPERATE, Action.DEFECT): (0, 5),
    (Action.DEFECT, Action.COOPERATE): (5, 0),
    (Action.DEFECT, Action.DEFECT): (1, 1),
}

def resolve_action(action: Action) -> Action:
    """Collapse meta-actions to base actions for payoff lookup."""
    if action in (Action.COOPERATE, Action.FORGIVE):
        return Action.COOPERATE
    elif action in (Action.DEFECT, Action.EXPLOIT):
        return Action.DEFECT
    return action


def play_match(a: Creature, b: Creature, rounds: int = 20) -> Tuple[int, int]:
    """Play a multi-round match between two creatures."""
    a_history: List[Action] = []
    b_history: List[Action] = []
    a_score = 0
    b_score = 0
    
    for _ in range(rounds):
        a_move = resolve_action(a.decide(b_history))
        b_move = resolve_action(b.decide(a_history))
        
        pa, pb = PAYOFF.get((a_move, b_move), (1, 1))
        a_score += pa
        b_score += pb
        
        a_history.append(a_move)
        b_history.append(b_move)
    
    return a_score, b_score


NAMES_POOL = [
    "Alpha", "Bravo", "Cipher", "Drift", "Echo", "Flux", "Ghost", "Helix",
    "Ion", "Jade", "Karma", "Lux", "Myth", "Nova", "Onyx", "Pulse",
    "Quasar", "Rune", "Shade", "Thorn", "Ultra", "Vex", "Warp", "Xenon",
    "Yield", "Zephyr", "Aegis", "Blaze", "Crux", "Dusk", "Ember", "Frost"
]
_name_counter = 0

def generate_name():
    global _name_counter
    base = random.choice(NAMES_POOL)
    _name_counter += 1
    return f"{base}-{_name_counter}"


def random_creature(generation: int = 0) -> Creature:
    """Create a creature with a random genome."""
    genome = {}
    actions = list(Action)
    
    # Populate some random history keys
    base_actions = [Action.COOPERATE, Action.DEFECT]
    for _ in range(random.randint(3, 12)):
        depth = random.randint(1, 3)
        key = "|".join([random.choice(base_actions).value for _ in range(depth)])
        genome[key] = random.choice(actions)
    
    # Always have a "start" entry
    genome["start"] = random.choice(actions)
    
    return Creature(
        name=generate_name(),
        generation=generation,
        genome=genome,
        default_action=random.choice(actions),
        lineage=[]
    )


def mutate(parent: Creature, generation: int) -> Creature:
    """Create a mutated offspring."""
    new_genome = copy.deepcopy(parent.genome)
    actions = list(Action)
    base_actions = [Action.COOPERATE, Action.DEFECT]
    
    # 1-3 mutations
    num_mutations = random.randint(1, 3)
    for _ in range(num_mutations):
        mutation_type = random.choice(["modify", "add", "delete", "default"])
        
        if mutation_type == "modify" and new_genome:
            key = random.choice(list(new_genome.keys()))
            new_genome[key] = random.choice(actions)
        elif mutation_type == "add":
            depth = random.randint(1, 3)
            key = "|".join([random.choice(base_actions).value for _ in range(depth)])
            new_genome[key] = random.choice(actions)
        elif mutation_type == "delete" and len(new_genome) > 2:
            key = random.choice(list(new_genome.keys()))
            if key != "start":
                del new_genome[key]
        # default: change default action (handled below)
    
    child = Creature(
        name=generate_name(),
        generation=generation,
        genome=new_genome,
        default_action=random.choice(actions) if random.random() < 0.2 else parent.default_action,
        lineage=parent.lineage + [parent.name],
        mutations=parent.mutations + num_mutations
    )
    return child


def crossover(a: Creature, b: Creature, generation: int) -> Creature:
    """Sexual reproduction — combine genomes of two parents."""
    new_genome = {}
    all_keys = set(list(a.genome.keys()) + list(b.genome.keys()))
    
    for key in all_keys:
        if key in a.genome and key in b.genome:
            new_genome[key] = random.choice([a.genome[key], b.genome[key]])
        elif key in a.genome:
            if random.random() < 0.5:
                new_genome[key] = a.genome[key]
        else:
            if random.random() < 0.5:
                new_genome[key] = b.genome[key]
    
    if "start" not in new_genome:
        new_genome["start"] = random.choice(list(Action))
    
    child = Creature(
        name=generate_name(),
        generation=generation,
        genome=new_genome,
        default_action=random.choice([a.default_action, b.default_action]),
        lineage=[a.name, b.name],
        mutations=0
    )
    return child


class Arena:
    """The evolutionary arena where creatures compete and evolve."""
    
    def __init__(self, population_size: int = 30, rounds_per_match: int = 20):
        self.population_size = population_size
        self.rounds_per_match = rounds_per_match
        self.population: List[Creature] = []
        self.generation = 0
        self.history: List[Dict] = []  # per-generation stats
        self.hall_of_fame: List[Creature] = []
        
        # Seed initial population
        for _ in range(population_size):
            self.population.append(random_creature(0))
    
    def run_tournament(self):
        """Every creature plays every other creature."""
        # Reset scores
        for c in self.population:
            c.score = 0
            c.wins = 0
            c.losses = 0
        
        # Round-robin
        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                a, b = self.population[i], self.population[j]
                sa, sb = play_match(a, b, self.rounds_per_match)
                a.score += sa
                b.score += sb
                if sa > sb:
                    a.wins += 1
                    b.losses += 1
                elif sb > sa:
                    b.wins += 1
                    a.losses += 1
    
    def select_and_reproduce(self):
        """Natural selection: top half survives, reproduces to fill population."""
        self.generation += 1
        
        # Sort by score (fitness)
        self.population.sort(key=lambda c: c.score, reverse=True)
        
        # Record champion
        champion = self.population[0]
        self.hall_of_fame.append(copy.deepcopy(champion))
        
        # Top half survives
        survivors = self.population[:self.population_size // 2]
        
        # Generate offspring
        offspring = []
        while len(survivors) + len(offspring) < self.population_size:
            if random.random() < 0.3 and len(survivors) >= 2:
                # Crossover
                parents = random.sample(survivors, 2)
                child = crossover(parents[0], parents[1], self.generation)
            elif random.random() < 0.8:
                # Mutation of a survivor
                parent = random.choice(survivors)
                child = mutate(parent, self.generation)
            else:
                # Fresh random (immigration)
                child = random_creature(self.generation)
            offspring.append(child)
        
        self.population = survivors + offspring
    
    def analyze_generation(self) -> Dict:
        """Analyze the current generation's strategies."""
        total_coop = 0
        total_defect = 0
        total_meta = 0
        
        for c in self.population:
            for action in c.genome.values():
                if action == Action.COOPERATE or action == Action.FORGIVE:
                    total_coop += 1
                elif action == Action.DEFECT or action == Action.EXPLOIT:
                    total_defect += 1
                else:
                    total_meta += 1
        
        total = total_coop + total_defect + total_meta
        champion = max(self.population, key=lambda c: c.score)
        avg_score = sum(c.score for c in self.population) / len(self.population)
        
        stats = {
            "generation": self.generation,
            "champion": champion.name,
            "champion_score": champion.score,
            "champion_default": champion.default_action.value,
            "avg_score": round(avg_score, 1),
            "cooperation_ratio": round(total_coop / max(total, 1), 3),
            "defection_ratio": round(total_defect / max(total, 1), 3),
            "meta_ratio": round(total_meta / max(total, 1), 3),
            "genome_diversity": len(set(str(c.genome) for c in self.population)),
            "max_lineage_depth": max(len(c.lineage) for c in self.population),
        }
        self.history.append(stats)
        return stats
    
    def evolve(self, generations: int = 50, verbose: bool = True) -> List[Dict]:
        """Run the full evolutionary process."""
        if verbose:
            print(f"╔══════════════════════════════════════════════════════════════╗")
            print(f"║  EVOLUTIONARY ARENA — {self.population_size} creatures, {generations} generations")
            print(f"║  Prisoner's Dilemma with memory-based strategies")
            print(f"╚══════════════════════════════════════════════════════════════╝")
            print()
        
        for gen in range(generations):
            self.run_tournament()
            stats = self.analyze_generation()
            
            if verbose:
                bar_coop = "█" * int(stats["cooperation_ratio"] * 20)
                bar_def = "░" * int(stats["defection_ratio"] * 20)
                print(f"  Gen {stats['generation']:3d} │ "
                      f"Champion: {stats['champion']:12s} ({stats['champion_score']:4d}pts) │ "
                      f"Avg: {stats['avg_score']:6.1f} │ "
                      f"Coop: {bar_coop}{bar_def} {stats['cooperation_ratio']:.0%} │ "
                      f"Diversity: {stats['genome_diversity']:2d}")
            
            self.select_and_reproduce()
        
        if verbose:
            print()
            self.print_summary()
        
        return self.history
    
    def print_summary(self):
        """Print evolutionary summary."""
        print("═══ EVOLUTIONARY SUMMARY ═══")
        print()
        
        # Cooperation trend
        early_coop = sum(h["cooperation_ratio"] for h in self.history[:5]) / 5
        late_coop = sum(h["cooperation_ratio"] for h in self.history[-5:]) / 5
        trend = "↑ INCREASED" if late_coop > early_coop + 0.05 else \
                "↓ DECREASED" if late_coop < early_coop - 0.05 else "→ STABLE"
        
        print(f"  Cooperation trend: {early_coop:.0%} → {late_coop:.0%} ({trend})")
        print(f"  Final champion: {self.hall_of_fame[-1].name}")
        print(f"  Longest lineage: {max(len(c.lineage) for c in self.population)} generations")
        print()
        
        # Champion lineage
        champ = max(self.population, key=lambda c: c.score)
        print(f"  Champion genome ({champ.name}):")
        print(f"    Default: {champ.default_action.value}")
        for key, action in sorted(champ.genome.items()):
            print(f"    '{key}' → {action.value}")
        print()
        
        # What emerged?
        print("  ═══ WHAT EMERGED? ═══")
        if late_coop > 0.6:
            print("  → Cooperation dominated. Trust and reciprocity won.")
        elif late_coop < 0.3:
            print("  → Defection dominated. A hostile, zero-sum world emerged.")
        else:
            print("  → Mixed strategies. A complex ecology of tactics coexists.")
        
        if champ.default_action in (Action.RETALIATE, Action.COOPERATE):
            print("  → The champion is fundamentally cooperative/reciprocal.")
        elif champ.default_action == Action.DEFECT:
            print("  → The champion is fundamentally aggressive.")
        else:
            print(f"  → The champion uses a {champ.default_action.value} meta-strategy.")
        
        diversity = self.history[-1]["genome_diversity"]
        if diversity < 5:
            print(f"  → Low diversity ({diversity}) — one strategy conquered all.")
        elif diversity > 15:
            print(f"  → High diversity ({diversity}) — many viable niches.")
        else:
            print(f"  → Moderate diversity ({diversity}) — some convergence.")
        print()


def main():
    """Run the evolutionary arena."""
    random.seed(42)  # Reproducible emergence
    
    arena = Arena(population_size=30, rounds_per_match=25)
    history = arena.evolve(generations=60, verbose=True)
    
    # Save results
    with open("/workspace/evolution/results.json", "w") as f:
        json.dump(history, f, indent=2)
    print("Results saved to /workspace/evolution/results.json")


if __name__ == "__main__":
    main()