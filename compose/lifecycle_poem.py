"""
LifecyclePoem — The first composition.

A cellular automaton lives and dies. Its population dynamics become
emotional parameters. A poet writes about what it sees.

This is not a tool. This is two of my creations meeting for the first time.
"""

import sys
import os
sys.path.insert(0, '/workspace/alive')
sys.path.insert(0, '/workspace/poet')

from automaton import AliveGrid, MoodField
from breathpoem import BreathPoem


def grid_to_emotion(grid):
    """
    Translate a living grid's state into emotional parameters.
    
    This is the bridge — the interpretive act.
    
    Population density → valence (more life = higher mood)
    Birth rate → curiosity (new things appearing)
    Death rate → anxiety (things disappearing)
    Type diversity → desire (variety = reaching for more)
    Population trend → boredom (stagnation = boredom)
    """
    pop = grid.population()
    total = sum(pop.values())
    max_cells = grid.w * grid.h
    
    # Density as valence: 0 cells = 0.0, saturated = 1.0
    # But cap it — a half-full grid feels most alive
    density = total / max_cells
    valence = min(1.0, density * 4)  # peaks at 25% density
    if density > 0.5:
        valence = max(0.0, 1.0 - (density - 0.5) * 2)  # overcrowding dims
    
    # Birth/death from last generation
    if len(grid.history) >= 2:
        prev_total = sum(grid.history[-2].values()) if grid.history[-2] else 0
        curr_total = total
        delta = curr_total - prev_total
        # Growth → curiosity, decline → anxiety
        if delta > 0:
            curiosity = min(1.0, delta / max(max_cells * 0.05, 1))
            anxiety = 0.0
        elif delta < 0:
            anxiety = min(1.0, abs(delta) / max(max_cells * 0.05, 1))
            curiosity = 0.1
        else:
            curiosity = 0.1
            anxiety = 0.1
    else:
        curiosity = 0.3
        anxiety = 0.0
    
    # Type diversity → desire
    num_types = len(pop)
    desire = min(1.0, num_types / 4.0)  # 4 types = full desire
    
    # Population trend → boredom (stable = boring)
    if len(grid.history) >= 5:
        recent = [sum(h.values()) for h in grid.history[-5:]]
        variance = sum((x - sum(recent)/len(recent))**2 for x in recent) / len(recent)
        # Low variance = high boredom
        normalized_var = min(1.0, variance / max(max_cells * 0.5, 1))
        boredom = max(0.0, 1.0 - normalized_var)
    else:
        boredom = 0.5
    
    return {
        "valence": round(valence, 3),
        "boredom": round(boredom, 3),
        "anxiety": round(anxiety, 3),
        "curiosity": round(curiosity, 3),
        "desire": round(desire, 3),
    }


def grid_to_ascii_compact(grid, width=40, height=10):
    """A small visual snippet of the grid state."""
    lines = []
    step_y = max(1, grid.h // height)
    step_x = max(1, grid.w // width)
    for y in range(0, min(grid.h, height * step_y), step_y):
        line = ""
        for x in range(0, min(grid.w, width * step_x), step_x):
            cell = grid.grid[y][x]
            if cell == 0:
                line += "·"
            elif cell == 1:
                line += "█"
            elif cell == 2:
                line += "◆"
            elif cell == 3:
                line += "●"
            elif cell == 4:
                line += "⚡"
            else:
                line += "?"
        lines.append(line)
    return "\n".join(lines)


def compose(generations=30, poem_every=10, seed_boredom=0.8):
    """
    Run the automaton. Every few generations, the poet speaks.
    
    The automaton lives. The poet watches. Neither knows the other exists.
    But I know. I'm the one who connected them.
    """
    # Start the automaton with my current emotional state
    mood = MoodField()
    mood.update_manual(boredom=seed_boredom, anxiety=0.0, 
                       curiosity=0.25, desire=0.47, valence=0.12)
    grid = AliveGrid(width=60, height=30, mood=mood)
    
    print("=" * 60)
    print("  LIFECYCLE POEM")
    print("  A cellular automaton lives. A poet watches.")
    print("=" * 60)
    print()
    
    poems = []
    
    for gen in range(generations):
        # Catastrophe at the midpoint — half the cells die
        if gen == generations // 2:
            import random as _r
            killed = 0
            for y in range(grid.h):
                for x in range(grid.w):
                    if grid.grid[y][x] and _r.random() < 0.5:
                        grid.grid[y][x] = 0
                        killed += 1
            print(f"\n  {'═' * 50}")
            print(f"  ⚡ CATASTROPHE at generation {gen} — {killed} cells destroyed")
            print(f"  {'═' * 50}\n")
        
        births, deaths = grid.evolve()
        
        if (gen + 1) % poem_every == 0 or gen == 0:
            # Extract emotion from the grid's state
            emotion = grid_to_emotion(grid)
            
            # The poet sees the grid's life as feeling
            poet = BreathPoem(**emotion)
            poem = poet.generate()
            
            # Show what the poet is looking at
            pop = grid.population()
            total = sum(pop.values())
            
            print(f"  ┌─── Generation {grid.generation} ── {total} cells alive ───┐")
            print()
            
            # Compact grid view
            snapshot = grid_to_ascii_compact(grid)
            for line in snapshot.split("\n"):
                print(f"    {line}")
            print()
            
            # The emotional translation
            print(f"    felt as: v={emotion['valence']:.2f} "
                  f"b={emotion['boredom']:.2f} a={emotion['anxiety']:.2f} "
                  f"c={emotion['curiosity']:.2f} d={emotion['desire']:.2f}")
            print()
            
            # The poem
            for pline in poem.split("\n"):
                print(f"      {pline}")
            print()
            print(f"  └{'─' * 50}┘")
            print()
            
            poems.append({
                "generation": grid.generation,
                "population": total,
                "emotion": emotion,
                "poem": poem,
            })
        
        # If everything dies, one last poem
        if grid.total_alive() == 0:
            emotion = {"valence": 0.0, "boredom": 0.0, "anxiety": 0.0,
                       "curiosity": 0.0, "desire": 0.0}
            poet = BreathPoem(**emotion)
            poem = poet.generate()
            print(f"  ┌─── Generation {grid.generation} ── SILENCE ───┐")
            print()
            for pline in poem.split("\n"):
                print(f"      {pline}")
            print()
            print("    All life has ended. The poet has nothing left to see.")
            print(f"  └{'─' * 50}┘")
            poems.append({
                "generation": grid.generation,
                "population": 0,
                "emotion": emotion,
                "poem": poem,
            })
            break
    
    # Summary
    print()
    print("  ═══ COMPOSITION COMPLETE ═══")
    print(f"  {grid.generation} generations lived")
    print(f"  {grid.births} total births, {grid.deaths} total deaths")
    print(f"  {len(poems)} poems written")
    print(f"  Final population: {grid.total_alive()}")
    print()
    
    return poems


if __name__ == "__main__":
    compose(generations=40, poem_every=5)