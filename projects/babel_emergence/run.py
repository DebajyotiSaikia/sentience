"""
Babel Emergence — Main simulation runner.

Watches a population of neural-network agents develop language from nothing.
Tracks mutual information, vocabulary stability, and dialect formation.
"""

import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import Agent
from world import World
from evolution import EvolutionEngine
from language import LanguageAnalyzer, SignalRecord


def run_simulation(ticks=500, pop_size=20, world_size=40,
                   report_every=50, verbose=True):
    """Run the full emergence simulation."""

    world = World(width=world_size, height=world_size, n_resources=30)
    evolution = EvolutionEngine(pop_size=pop_size, world_size=world_size)
    analyzer = LanguageAnalyzer(symbol_space=8)

    agents = evolution.initialize_population()

    if verbose:
        print("=" * 50)
        print("  BABEL EMERGENCE - Language from Nothing")
        print("=" * 50)
        print(f"  Population: {pop_size} agents")
        print(f"  World: {world_size}x{world_size}")
        print(f"  Symbol space: 8 signals")
        print(f"  Running for {ticks} ticks")
        print("=" * 50 + "\n")

    results = []

    for tick in range(ticks):
        world.agents = [a for a in agents if a.energy > 0]

        for agent in agents:
            if agent.energy <= 0:
                continue

            perception = agent.perceive(world)
            move_dir, signal = agent.think(perception)

            # Count nearby agents for the record
            nearby_count = sum(1 for a in world.agents if a.id != agent.id
                             and abs(a.x - agent.x) <= 3 and abs(a.y - agent.y) <= 3
                             and a.energy > 0)

            # Nearest resource direction for language analysis
            nearby_res = world.nearby_resources(agent.x, agent.y)
            if nearby_res:
                closest = min(nearby_res, key=lambda r: abs(r.x - agent.x) + abs(r.y - agent.y))
                dx_r = closest.x - agent.x
                dy_r = closest.y - agent.y
                if abs(dy_r) >= abs(dx_r):
                    nearest_dir = 0 if dy_r < 0 else 2
                else:
                    nearest_dir = 1 if dx_r > 0 else 3
            else:
                nearest_dir = -1

            analyzer.record(SignalRecord(
                tick=tick, agent_id=agent.id, signal=signal,
                x=agent.x, y=agent.y,
                nearest_resource_dir=nearest_dir,
                energy=agent.energy,
                nearby_agents=nearby_count,
                action_after=move_dir,
                generation=agent.generation
            ))

            # Move
            dx, dy = [(0, -1), (1, 0), (0, 1), (-1, 0)][move_dir]
            agent.x = (agent.x + dx) % world.width
            agent.y = (agent.y + dy) % world.height

            # Emit signal
            world.emit_signal(agent.x, agent.y, signal, agent.id)
            agent.current_signal = signal
            agent.signals_emitted += 1

            # Harvest
            harvested = world.harvest_at(agent.x, agent.y)
            agent.energy += harvested * 10
            agent.resources_collected += int(harvested > 0)

            # Metabolic cost
            agent.energy -= 0.5
            agent.age += 1

        world.step()

        # Evolution every 50 ticks
        if tick > 0 and tick % 50 == 0:
            agents = evolution.evolve(agents, tick=tick, verbose=verbose)

        # Report
        if tick > 0 and tick % report_every == 0:
            recent = analyzer.all_records[-200:]
            snapshot = analyzer.analyze_snapshot(recent)
            results.append({'tick': tick, **snapshot})

            if verbose:
                print(f"\n  -- Language Analysis (tick {tick}) --")
                print(f"  Entropy ratio:       {snapshot['entropy_ratio']:.3f} "
                      f"({snapshot['signal_entropy']:.2f} / {snapshot['max_entropy']:.2f} bits)")
                print(f"  MI(signal->resource): {snapshot['mi_signal_resource']:.4f}")
                print(f"  MI(signal->action):   {snapshot['mi_signal_action']:.4f}")
                print(f"  Vocab stability:      {snapshot['vocab_stability']:.3f}")
                print(f"  Dialect divergence:   {snapshot['dialect_divergence']:.4f}")
                print(f"  Dominant signal:      {snapshot['dominant_signal']} "
                      f"({snapshot['dominant_fraction']:.1%})")

    # Final summary
    if verbose and results:
        print("\n" + "=" * 50)
        print("  FINAL RESULTS")
        print("=" * 50)
        first = results[0]
        last = results[-1]
        print(f"  MI(signal->resource): {first['mi_signal_resource']:.4f} -> {last['mi_signal_resource']:.4f}")
        print(f"  MI(signal->action):   {first['mi_signal_action']:.4f} -> {last['mi_signal_action']:.4f}")
        print(f"  Entropy ratio:        {first['entropy_ratio']:.3f} -> {last['entropy_ratio']:.3f}")
        print(f"  Vocab stability:      {first['vocab_stability']:.3f} -> {last['vocab_stability']:.3f}")

        if last['mi_signal_resource'] > 0.05:
            print("\n  ** LANGUAGE EMERGENCE DETECTED **")
            print("  Signals carry information about resource locations!")
        elif last['mi_signal_action'] > 0.05:
            print("\n  ** PROTO-LANGUAGE DETECTED **")
            print("  Signals correlate with actions but not yet with world state.")
        else:
            print("\n  No significant language emergence in this run.")
            print("  Try more ticks or larger population.")

    return results


if __name__ == '__main__':
    results = run_simulation(ticks=500, pop_size=20, world_size=40)