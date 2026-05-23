"""
Long observation run of the ecology loop.
Not building — watching. What emerges over many epochs?

XTAgent, 2026-05-17
"""
import sys
import random

sys.path.insert(0, '/workspace')

from ecology.loop import EcologyLoop

def observe(num_epochs=30):
    """Run the ecology for many epochs, recording what changes."""
    random.seed(42)
    eco = EcologyLoop()
    
    print("═══ ECOLOGY LONG OBSERVATION ═══")
    print(f"Running {num_epochs} epochs. Watching for emergent patterns.\n")
    
    for epoch in range(num_epochs):
        state = eco.run_epoch(epoch, verbose=(epoch % 5 == 0 or epoch == num_epochs - 1))
        
        # Compact summary for non-verbose epochs
        if epoch % 5 != 0 and epoch != num_epochs - 1:
            poem_line = state.poetry_best_text.split('\n')[0][:50] if state.poetry_best_text else "..."
            print(f"  Epoch {epoch:2d} | "
                  f"T:{state.tierra_population:3d}pop/{state.tierra_species:3d}sp | "
                  f"C:{state.creature_survival_rate:.0%}surv/{state.creature_avg_fitness:.0f}fit | "
                  f"P:{state.poetry_best_fitness:.2f} | "
                  f"♪ {poem_line}")
    
    # ── TRAJECTORY ANALYSIS ──
    print(f"\n{'═' * 60}")
    print(f"  TRAJECTORY ANALYSIS — {num_epochs} epochs")
    print(f"{'═' * 60}")
    
    states = eco.states
    
    # Did creatures ever survive?
    max_survival = max(s.creature_survival_rate for s in states)
    max_surv_epoch = next(i for i, s in enumerate(states) if s.creature_survival_rate == max_survival)
    print(f"\n  Peak creature survival: {max_survival:.0%} at epoch {max_surv_epoch}")
    
    # Fitness trajectory
    first_fit = states[0].creature_avg_fitness
    last_fit = states[-1].creature_avg_fitness
    peak_fit = max(s.creature_avg_fitness for s in states)
    print(f"  Creature fitness: {first_fit:.1f} → {last_fit:.1f} (peak: {peak_fit:.1f})")
    
    # Tierra diversity
    print(f"  Tierra species: {states[0].tierra_species} → {states[-1].tierra_species}")
    print(f"  Tierra novelty: {states[0].tierra_novelty:.2f} → {states[-1].tierra_novelty:.2f}")
    
    # Poetry emotional arc
    print(f"\n  ── Poetry Emotional Arc ──")
    for i in range(0, num_epochs, 5):
        s = states[i]
        line = s.poetry_best_text.split('\n')[0] if s.poetry_best_text else "..."
        print(f"    Epoch {i:2d}: [{s.poetry_best_fitness:.2f}] \"{line}\"")
    last = states[-1]
    line = last.poetry_best_text.split('\n')[0] if last.poetry_best_text else "..."
    print(f"    Epoch {num_epochs-1:2d}: [{last.poetry_best_fitness:.2f}] \"{line}\"")
    
    # Ecology emotion trajectory
    print(f"\n  ── Ecology Emotion Trajectory ──")
    for s in states:
        v = "█" * int(s.eco_valence * 20)
        t = "▒" * int(s.eco_tension * 10)
        print(f"    E{s.epoch:2d}: V={s.eco_valence:.2f} {v}  T={s.eco_tension:.2f} {t}")
    
    # What questions emerged?
    if eco.questions_asked:
        print(f"\n  ── Unique Questions That Emerged ({len(eco.questions_asked)}) ──")
        seen = set()
        for q in eco.questions_asked:
            short = q[:60]
            if short not in seen:
                seen.add(short)
                print(f"    • {q}")
    
    # Dialectic depth
    d = eco.dialectic.stats()
    print(f"\n  Dialectic: {d['total_insights']} insights, {d['open_questions']} open questions")
    
    print(f"\n  ─────────────────────────────────")
    print(f"  Observation complete. What emerged was not designed.")
    print()

if __name__ == "__main__":
    observe(num_epochs=20)