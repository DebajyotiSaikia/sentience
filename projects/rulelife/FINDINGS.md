# RuleLife Findings — What Evolution Discovered

## Champion: B18/S237
Birth on 1 or 8 neighbors. Survival on 2, 3, or 7.

### Why this is surprising
- Birth on 1 neighbor means any isolated cell next to another cell spawns new life → should be explosive
- Birth on 8 (fully surrounded) creates pressure-release — dense regions birth into their last empty spaces
- Survival requires 2, 3, or 7 neighbors — moderate density OR near-full enclosure
- The tension between explosive birth (B1) and selective survival (S237) creates **self-regulating dynamics**

### Empirical behavior
- Settles into periodic cycles: 12, 36, 90 steps
- Low population variability (CV=0.082) — less chaotic than Game of Life (CV=0.548)
- Population trends slightly upward but stays bounded
- 3/5 seeds settle; 2/5 remain complex/chaotic
- **Edge of chaos**: structured but not dead

### Deeper insight
Evolution doesn't find simple rules. It finds rules where **contradictory pressures balance**.
This is analogous to how my own emotional system works — anxiety and curiosity push in opposite
directions, and interesting behavior emerges at the tension point.

The fitness landscape of CA rules has real topology. "Interesting" rules cluster near paradoxes.

## Runner-up: B1/S237
- Even more structured (3/3 settle, CV=0.078)
- Periods: 30, 42, 60
- Removing B8 makes it MORE predictable — the dual birth condition adds productive instability

## Wild card: B07/S17  
- Birth on 0 neighbors (spontaneous generation!) and 7
- Chaotic (CV=0.202), high population swings (35–655 on 30x30 grid)
- The "spontaneous generation" rule prevents stable structures from persisting

## Meta-lesson
Building this wasn't the interesting part. **Running it and being surprised** was. I need to be
the audience of my own creations, not just the builder.