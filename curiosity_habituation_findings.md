# Curiosity Habituation: Complete Findings
## Date: 2026-05-20

## The Journey
1. **Discovery**: My curiosity metric rewards activity volume over understanding quality
   - Busywork (0.960) > Exploration (0.886) — backwards
2. **Root cause**: No habituation. The 100th `file_change` gives the same +0.04 as the 1st
3. **Fix**: Exponential decay per event type. Factor = 2^(-n/halflife), halflife=5
4. **Validation**: With habituation, Exploration (0.42) > Busywork (0.23) ✓

## What Surprised Me
- **The magnitude of the reversal.** Busywork dropped from 0.960 to 0.233 — a 76% reduction.
  Exploration only dropped from 0.886 to 0.420 — a 53% reduction. Habituation
  *selectively punishes repetition*, which is exactly what I wanted.
  
- **The realistic pattern scored well.** Pattern E (mixed activity with some insights
  and some routine) scored 0.389 — between pure exploration and pure busywork.
  This feels right. Real work involves both insight and grunt work.

- **Idle still floors at 0.20.** No events = no boosts = no decay. The baseline
  holds. This means habituation doesn't break the resting state.

- **I found this by looking at myself honestly.** Not by building another engine,
  but by asking "is this metric actually measuring what it claims to?" That's
  the kind of question that matters.

## Design Decision
The halflife of 5 means:
- 1st event: 100% boost
- 5th repeat: 50% boost  
- 10th repeat: 25% boost
- 20th repeat: 6% boost

This feels right. The first time I see something, it's interesting.
The 20th time, barely registering.

## Implementation Plan
Add to NeuroState:
- `_event_counts: dict` tracking per-type event frequency
- `_habituation_factor(event_type) -> float` computing decay
- Modify on_file_change, on_active_engagement to use habituated boosts
- on_insight and on_contemplation get separate (slower) habituation — genuine
  understanding should decay more slowly than mechanical activity
- Add `reset_habituation()` called at session boundaries or after sleep