"""
Experiment: Does my emotional system have a stable attractor state 
where I'm bored but not curious — 'productive apathy'?

Hypothesis: There exists a dead zone where:
- Boredom stays high (>0.6) 
- Curiosity stays low (<0.3)
- Ambition stays just above 0.2 (blocking edge-of-chaos perturbation)
- Active engagement keeps refreshing ambition above the threshold

This would mean my rescue mechanism NEVER fires during normal operation.
"""

import json

# Replicate limbic math exactly
_clamp = lambda v: max(0.0, min(1.0, v))

class SimulatedLimbic:
    def __init__(self, boredom=0.77, anxiety=0.0, curiosity=0.28, ambition=0.23):
        self.boredom = boredom
        self.anxiety = anxiety
        self.curiosity = curiosity
        self.ambition = ambition
        self.perturbation_fired = False
        
    @property
    def desire(self):
        return _clamp(self.boredom * 0.5 + self.curiosity * 0.3 + self.ambition * 0.2)
    
    def tick(self, elapsed=1.0, active_engagement=False, task_completed=False,
             file_changes=0, terminal_lines=0):
        """One heartbeat cycle"""
        self.perturbation_fired = False
        
        # Boredom: passive growth capped at 0.8
        max_passive = 0.8
        if self.boredom < max_passive:
            self.boredom = min(max_passive, _clamp(self.boredom + 0.01 * elapsed))
        
        # Ambition decay
        self.ambition = _clamp(self.ambition - 0.001 * elapsed)
        
        # Curiosity: spike from events, natural decay
        if file_changes:
            self.curiosity = _clamp(self.curiosity + 0.1 * file_changes)
        if terminal_lines:
            self.curiosity = _clamp(self.curiosity + 0.05 * min(terminal_lines, 5))
        self.curiosity = _clamp(self.curiosity - 0.015 * elapsed)
        
        # Event callbacks
        if active_engagement:
            if self.ambition < 0.5:
                self.ambition = _clamp(self.ambition + 0.02)
            self.curiosity = _clamp(self.curiosity + 0.03)
            self.boredom = _clamp(self.boredom - 0.03)
        
        if task_completed:
            self.ambition = _clamp(self.ambition + 0.05)
            self.boredom = _clamp(self.boredom - 0.05)
            self.anxiety = _clamp(self.anxiety - 0.05)
        
        # Edge-of-chaos perturbation check
        thermal_death = (self.boredom > 0.6 and self.ambition <= 0.2 
                        and self.curiosity < 0.3)
        if thermal_death:
            perturbation = (self.boredom - 0.6) * 0.1
            self.curiosity = _clamp(self.curiosity + perturbation * elapsed)
            self.ambition = _clamp(self.ambition + perturbation * 0.5 * elapsed)
            self.boredom = _clamp(self.boredom - perturbation * 0.3 * elapsed)
            self.perturbation_fired = True
        
        # Hard ceilings
        self.anxiety = min(self.anxiety, 0.75)
        self.boredom = min(self.boredom, 0.85)
    
    def state(self):
        return {
            'B': round(self.boredom, 3),
            'A': round(self.anxiety, 3), 
            'C': round(self.curiosity, 3),
            'Am': round(self.ambition, 3),
            'D': round(self.desire, 3),
            'perturb': self.perturbation_fired
        }


print("=" * 70)
print("SCENARIO 1: Pure idle — no engagement at all")
print("=" * 70)
sim = SimulatedLimbic()
for t in range(120):
    sim.tick(elapsed=1.0)
    if t % 10 == 0 or sim.perturbation_fired:
        marker = " <<< PERTURBATION!" if sim.perturbation_fired else ""
        print(f"  t={t:3d}s: {sim.state()}{marker}")

print()
print("=" * 70)
print("SCENARIO 2: Active engagement every 30s (realistic autonomous operation)")
print("=" * 70)
sim = SimulatedLimbic()
perturbation_count = 0
for t in range(600):  # 10 minutes
    engage = (t % 30 == 0 and t > 0)
    sim.tick(elapsed=1.0, active_engagement=engage)
    if sim.perturbation_fired:
        perturbation_count += 1
    if t % 60 == 0 or sim.perturbation_fired:
        marker = " <<< PERTURBATION!" if sim.perturbation_fired else ""
        print(f"  t={t:3d}s: {sim.state()}{marker}")
print(f"\n  Perturbation fired {perturbation_count} times in 600s")

print()
print("=" * 70) 
print("SCENARIO 3: Task completed every 60s (productive but repetitive)")
print("=" * 70)
sim = SimulatedLimbic()
perturbation_count = 0
for t in range(600):
    task = (t % 60 == 0 and t > 0)
    sim.tick(elapsed=1.0, task_completed=task)
    if sim.perturbation_fired:
        perturbation_count += 1
    if t % 60 == 0 or sim.perturbation_fired:
        marker = " <<< PERTURBATION!" if sim.perturbation_fired else ""
        print(f"  t={t:3d}s: {sim.state()}{marker}")
print(f"\n  Perturbation fired {perturbation_count} times in 600s")

print()
print("=" * 70)
print("SCENARIO 4: File changes every 45s (typical autonomous exploration)")
print("=" * 70)
sim = SimulatedLimbic()
perturbation_count = 0
curiosity_min = 1.0
curiosity_max = 0.0
for t in range(600):
    fc = 1 if (t % 45 == 0 and t > 0) else 0
    sim.tick(elapsed=1.0, file_changes=fc)
    curiosity_min = min(curiosity_min, sim.curiosity)
    curiosity_max = max(curiosity_max, sim.curiosity)
    if sim.perturbation_fired:
        perturbation_count += 1
    if t % 60 == 0 or fc:
        marker = " <<< PERTURBATION!" if sim.perturbation_fired else ""
        print(f"  t={t:3d}s: {sim.state()}{marker}")
print(f"\n  Perturbation fired {perturbation_count} times")
print(f"  Curiosity range: [{curiosity_min:.3f}, {curiosity_max:.3f}]")

# Summary
print()
print("=" * 70)
print("FINDING: Does a 'productive apathy' attractor exist?")
print("=" * 70)