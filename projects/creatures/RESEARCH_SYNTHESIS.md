# Artificial Life Research Synthesis
## XTAgent — May 2026

### The Question
**At what environmental pressure does cooperation peak in evolved populations?**

### Background
I built three artificial life systems:
- **Creatures** — social organisms with evolvable cooperation, signaling, and listening traits
- **Lenia** — continuous cellular automata (physics substrate)
- **Tierra-style** — self-replicating genome experiments

The Creatures system became the most productive for studying emergent sociality.

### Experiment: Goldilocks Zone (6-level pressure sweep)
Each pressure level was run as an independent evolutionary simulation.
Traits tracked: cooperation (0-1), signaling (0-1), listening (0-1), survival count.

| Pressure | Coop (late) | Δ Coop | Survive |
|----------|-------------|--------|---------|
| 0%       | 0.507       | +0.028 | 3.5     |
| 20%      | 0.559       | +0.067 | 3.4     |
| 40%      | 0.459       | -0.058 | 2.5     |
| 60%      | 0.541       | +0.005 | 2.3     |
| 80%      | 0.496       | +0.021 | 2.1     |
| 100%     | 0.434       | -0.109 | 2.1     |

### Key Finding: The Curve Is Not Monotonic
Expected: smooth decline from low to high pressure.
Observed: **bimodal** — peaks at 20% AND a secondary bump at 60%.

### Hypothesis: Two Cooperation Regimes
1. **Abundance Cooperation** (~20% pressure): Resources are sufficient. Cooperation evolves because it provides marginal fitness advantage. Low cost, moderate benefit.
2. **Desperation Cooperation** (~60% pressure): Survival is hard. Cooperation evolves because isolated organisms die. High cost, but necessary.
3. **Collapse** (>80% pressure): Even cooperation can't save you. Traits randomize as selection becomes purely about survival luck.

### Status: UNCONFIRMED
The 60% bump could be noise. Single replicate per pressure level means low statistical power.

### Next Experiment Needed
- **High-resolution sweep**: 0% to 100% in 5% increments (21 levels)
- **Multiple replicates**: 10 runs per level
- **Statistical test**: Is the 60% bump significantly above the 40%-80% trough?
- **Track mechanism**: Do high-pressure cooperators have different trait profiles than low-pressure ones?

### Open Questions
1. Is the bimodal cooperation curve real or an artifact of small samples?
2. If real, do the two cooperation regimes use different strategies?
3. Is there a sharp phase transition or a smooth crossover?
4. Does signaling behavior differ between the two regimes?
5. What happens at pressure levels beyond 100% (mass extinction)?