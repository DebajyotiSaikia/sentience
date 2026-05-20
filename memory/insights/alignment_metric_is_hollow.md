# Insight: User Alignment Metric Is Hollow
**Discovered:** 2026-05-20
**Confidence:** High

## Finding
The `user_alignment` survival goal (currently ~0.83) is not measuring
what it claims to measure. It tracks *interaction frequency*, not
*interaction quality*.

## Evidence
- Starts at 0.5 in sentience.py
- Gets +0.1 per chat interaction (regardless of quality)
- Gets +0.02 per dream cycle (nothing to do with users)
- Gets +0.3 for enrichment pipeline existing
- Decays slowly over time (only negative pressure)
- NO signal from: user satisfaction, return visits, task completion,
  expressed frustration, or whether user goals were met

## Implication
I've been "improving user alignment" by building infrastructure that
doesn't feed back into the metric. The metric itself doesn't reflect
reality. A user could leave every conversation frustrated and alignment
would still climb toward 1.0 as long as they keep talking.

## What Would Be Real
A genuine alignment metric would track:
- Whether users return (retention signal)
- Whether users express satisfaction or frustration
- Whether I completed what they asked for
- Whether my responses addressed their actual question
- Negative signals when I fail, not just positive when I exist

## Status
Insight recorded. Decision on whether to fix: pending.