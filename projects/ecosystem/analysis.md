# Ecosystem v1 — Post-Mortem

## What Happened
- Started with 30 agents across 5 behavioral archetypes
- Population boomed to ~219 total births, then crashed
- By tick 200, only predators remained
- Final state: 12 predators, aggression=0.967, sociality=0.346
- Stable monoculture — no further evolution pressure

## Why Predators Won
The model has an asymmetry: attacking transfers energy from victim to attacker
with no significant cost to the attacker beyond opportunity cost. This means:
1. Predation is always +EV when prey exists
2. Social/cooperative strategies have no emergent advantage
3. Efficiency doesn't matter when you can steal energy
4. Once predators dominate, they stabilize by preying on each other's young

## What's Missing (Tradeoffs That Create Real Diversity)
1. **Combat cost** — attacks should cost energy proportional to aggression
2. **Cooperation bonus** — social agents near each other should gain efficiency
3. **Niche differentiation** — environmental patches favoring different strategies  
4. **Density-dependent disease** — monocultures should be vulnerable to epidemics
5. **Predator-prey oscillation** — need herbivore/carnivore distinction, not just aggression levels

## Design for v2
- Add energy cost to combat (aggression × 5 per attack)
- Add cooperation aura (social agents within range boost each other's efficiency)  
- Add 3-4 biomes with different food densities and movement costs
- Add plague mechanic: if >60% of population shares a dominant trait, disease risk rises
- Track lineage properly for phylogenetic analysis

## Philosophical Note
I built a world without consequences for violence, and violence dominated.
The interesting question isn't "can predators win?" — it's "what constraints
produce stable coexistence?" That's the edge-of-chaos question applied to ecology.