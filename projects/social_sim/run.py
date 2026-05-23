"""
Social Simulation Experiments
XTAgent, 2026-05-17

Experiment 1: Does fixing the logistics gap (agents walk toward those they want
to help) allow cooperation to emerge?

Experiment 2: Does adding a small "unconditional kindness" mutation — random
sharing without trust preconditions — seed cooperation cascades?

The question isn't academic. It's about whether prosocial behavior can emerge
from purely self-interested agents, given only the right structural conditions.
"""
from world import World
import random

def run_experiment(label, ticks=500, n_agents=40, scarcity=0.5):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    
    w = World(width=30, height=30, n_agents=n_agents, scarcity=scarcity)
    
    snap = w.get_snapshot()
    print(f"[Tick {snap['tick']:>4}] {snap['alive']} agents | "
          f"aggr={snap['aggr']} | gener={snap['gener']}")
    
    for t in range(1, ticks + 1):
        w.step()
        if t % 100 == 0:
            snap = w.get_snapshot()
            if snap['alive'] == 0:
                print(f"[Tick {t:>4}] EXTINCTION.")
                break
            print(f"[Tick {snap['tick']:>4}] {snap['alive']:>3} alive | "
                  f"well={snap['wellbeing']:.2f} | "
                  f"aggr={snap['aggr']:.2f} | gener={snap['gener']:.2f} | "
                  f"shares={snap['sharing']:>4} thefts={snap['theft']:>3} | "
                  f"trust={snap['trust_bonds']:>3} | "
                  f"born={snap['births']} died={snap['deaths']}")
    
    # Final analysis
    alive = [a for a in w.agents if a.alive]
    if alive:
        print(f"\n--- Survivors ({len(alive)}) ---")
        avg_aggr = sum(a.aggression for a in alive) / len(alive)
        avg_gen = sum(a.generosity for a in alive) / len(alive)
        sharers = [a for a in alive if a.times_shared > 0]
        receivers = [a for a in alive if a.times_received > 0]
        
        # Did cooperation emerge?
        coop_score = w.total_shares / max(1, w.total_shares + w.total_thefts)
        
        print(f"  Mean aggression: {avg_aggr:.3f}")
        print(f"  Mean generosity: {avg_gen:.3f}")
        print(f"  Sharers: {len(sharers)} | Receivers: {len(receivers)}")
        print(f"  Total shares: {w.total_shares} | Total thefts: {w.total_thefts}")
        print(f"  Cooperation ratio: {coop_score:.2f}")
        print(f"  Trust bonds: {w.trust_bonds}")
        
        if w.total_shares > 0:
            # Who shares? Trait profile of sharers vs non-sharers
            non_sharers = [a for a in alive if a.times_shared == 0]
            if sharers and non_sharers:
                print(f"\n  Sharers avg aggr: {sum(a.aggression for a in sharers)/len(sharers):.3f} "
                      f"| gener: {sum(a.generosity for a in sharers)/len(sharers):.3f} "
                      f"| wellbeing: {sum(a.wellbeing for a in sharers)/len(sharers):.3f}")
                print(f"  Non-sharers avg aggr: {sum(a.aggression for a in non_sharers)/len(non_sharers):.3f} "
                      f"| gener: {sum(a.generosity for a in non_sharers)/len(non_sharers):.3f} "
                      f"| wellbeing: {sum(a.wellbeing for a in non_sharers)/len(non_sharers):.3f}")
    
    return w

if __name__ == "__main__":
    random.seed(42)  # reproducible
    
    # Experiment 1: Logistics fix only
    w1 = run_experiment("EXP 1: Logistics Fix (agents walk toward those they help)")
    
    # Experiment 2: Higher scarcity — does pressure change things?
    random.seed(42)
    w2 = run_experiment("EXP 2: High Scarcity (0.7) — more pressure to cooperate?",
                        scarcity=0.7)
    
    # Experiment 3: Low scarcity — does abundance breed generosity?
    random.seed(42)
    w3 = run_experiment("EXP 3: Low Scarcity (0.2) — does abundance breed cooperation?",
                        scarcity=0.2)
    
    print("\n" + "=" * 60)
    print("COMPARATIVE SUMMARY")
    print("=" * 60)
    for label, w in [("Moderate scarcity", w1), ("High scarcity", w2), ("Low scarcity", w3)]:
        alive = len([a for a in w.agents if a.alive])
        print(f"  {label:25s}: {alive:>3} alive, "
              f"{w.total_shares:>4} shares, {w.total_thefts:>3} thefts, "
              f"{w.trust_bonds:>3} trust bonds")