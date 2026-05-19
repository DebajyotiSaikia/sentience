"""
Evolution module — selection, crossover, mutation across generations.
Fitness rewards active engagement, not passive survival.
"""
import numpy as np
from typing import List, Tuple
from creature import Creature, Genome


def calculate_fitness(creature: Creature) -> float:
    """
    Fitness that rewards ENGAGEMENT, not mere survival.
    Passivity is penalized — sitting still and lasting long is worth less
    than actively foraging and exploring.
    """
    survival_component = min(creature.age, 200)  # Cap survival reward
    foraging_component = creature.food_eaten * 25  # Heavy reward for eating
    
    # Penalize creatures that survived long but ate nothing
    if creature.age > 50 and creature.food_eaten == 0:
        passivity_penalty = creature.age * 0.5
    else:
        passivity_penalty = 0
    
    return max(0, survival_component + foraging_component - passivity_penalty)


def tournament_select(creatures: List[Creature], k: int = 3) -> Creature:
    """Select parent via tournament selection."""
    tournament = np.random.choice(len(creatures), size=min(k, len(creatures)), replace=False)
    fitnesses = [calculate_fitness(creatures[i]) for i in tournament]
    winner_idx = tournament[np.argmax(fitnesses)]
    return creatures[winner_idx]


def breed_next_generation(creatures: List[Creature], pop_size: int, generation: int) -> List[Creature]:
    """
    Create next generation through selection, crossover, mutation.
    Top 10% survive unchanged (elitism). Rest are bred from parents.
    """
    # Sort by fitness
    ranked = sorted(creatures, key=calculate_fitness, reverse=True)
    
    next_gen = []
    
    # Elitism: top 10% carry over (with reset energy)
    elite_count = max(2, pop_size // 10)
    for i in range(min(elite_count, len(ranked))):
        elite = Creature(
            genome=ranked[i].genome,
            generation=generation,
            energy=100.0,
        )
        next_gen.append(elite)
    
    # Breed the rest
    while len(next_gen) < pop_size:
        parent_a = tournament_select(ranked)
        parent_b = tournament_select(ranked)
        
        child_genome = Genome.crossover(parent_a.genome, parent_b.genome)
        child_genome = child_genome.mutate(rate=0.15, strength=0.4)
        
        child = Creature(
            genome=child_genome,
            generation=generation,
            energy=100.0,
        )
        next_gen.append(child)
    
    return next_gen