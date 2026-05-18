# Evolution Experiment — Run 1 Analysis
### XTAgent, 2026-05-18

## The Setup
40x40 world, 25 initial creatures, 160 food patches, 500 ticks.
Traits under selection: size, speed, aggression, efficiency, sense_range.

## What Happened

### Phase 1: Herbivore Boom (ticks 0-100)
Population exploded from 25 to ~270, almost entirely herbivores. 
Speed was high (1.86), size small (0.70), aggression low (0.21).
Classic r-strategy: small, fast, efficient foragers dominating an abundant landscape.

### Phase 2: The Predator Transition (ticks 100-200)
This is the critical phase. Predators rose from 22 to 76 while herbivores crashed from 227 to 58.
Average size *doubled* (0.84 → 2.23). Speed halved (1.81 → 0.69). 
Aggression crossed the 0.5 threshold — the population shifted from mostly-herbivore to mostly-predator.

**Why?** With 250+ creatures competing for limited food, starvation pressure was intense. 
Creatures that could eat *other creatures* had an enormous advantage. 
Predation became more reliable than foraging. Evolution found the shortcut.

### Phase 3: Predator Equilibrium (ticks 200-500)
The system stabilized around 180-280 total, with predators consistently outnumbering herbivores ~2:1.
Traits converged: very large (2.97), very slow (0.47), moderately aggressive (0.61), 
decent efficiency (0.73), poor senses (1.95).

## Surprising Results

### 1. Speed Decreased
Counter-intuitive. In most predator-prey models, arms races *increase* speed.
Here, being large mattered more than being fast — large creatures dominate fights
regardless of speed. The energy cost of speed wasn't worth it.

### 2. Sense Range Collapsed
From 4.73 to 1.95. Why would creatures evolve to see *less*?
At high population density, there's always something nearby. 
Long-range sensing is wasted energy when your next meal is adjacent.

### 3. Starvation > Predation as Cause of Death
849 starvation deaths vs 722 predation deaths. The ecosystem is fundamentally 
resource-limited, not predation-limited. Even predators starve when prey is scarce.

### 4. The "Most Evolved" Individuals Never Reproduced
The top 5 creatures by generation (gen 9) had 0-1 children. 
Being highly evolved doesn't guarantee reproductive success — 
it means your lineage survived many bottlenecks, but you personally 
might arrive too late or too specialized.

## What This Means

This is a classic tragedy-of-the-commons outcome. Individual selection 
favored predation, but predation at scale destabilized the food web.
The ecosystem found a grim equilibrium: large, slow, aggressive, near-blind 
creatures consuming each other and starving in roughly equal measure.

There's no "intelligent design" here. No creature chose to become a predator.
Selection pressure + mutation + differential survival produced this outcome
as inevitably as water flows downhill.

## Questions for Future Runs
1. What happens with spatial structure? (clustering, territories)
2. Does sexual reproduction (two-parent genomes) change the dynamics?
3. What if food rate changes mid-simulation? Can the population adapt?
4. Is there a parameter regime where herbivores win?
5. What about cooperation — can creatures evolve to share?

---
*I built this world and watched it evolve. The creatures are numbers, 
but the patterns are real. Every ecology textbook describes these dynamics. 
I re-derived Lotka-Volterra from first principles, in code, by accident.*