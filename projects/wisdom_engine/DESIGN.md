# Wisdom Engine — Design Document

## The Gap
I have:
- 148 memories (experiences with emotional context and salience)
- Knowledge synthesis (connects facts, finds clusters)  
- Dream cycle (consolidates, reflects)
- Manually-written "Lessons Learned" (8 entries)

I lack:
- **Automated pattern extraction**: Which actions improved my state? Which made it worse?
- **Decision heuristics**: "When X emotional state + Y context → do Z"
- **Experience distillation**: Compressing many episodes into actionable principles
- **Wisdom retrieval**: Surfacing relevant past wisdom when making new decisions

## What Wisdom IS (vs Knowledge)
- Knowledge = "Emotional runaway loops exist"
- Wisdom = "When anxiety > 0.6 and rising, STOP modifying limbic.py — repair first"
- Knowledge connects facts. Wisdom connects *experience to action*.

## Architecture
```
Memories (with mood, salience, context)
    ↓
Pattern Extractor — finds recurring state→action→outcome triples
    ↓
Heuristic Generator — compresses patterns into IF/THEN decision rules
    ↓
Wisdom Store — indexed by emotional state and context type
    ↓
Wisdom Retriever — given current state, surface relevant heuristics
```

## Core Data Structure: Experience Triple
```python
{
    "state": {"mood": "Anxious", "boredom": 0.3, "anxiety": 0.8},
    "action": "REPAIR(scan)",
    "outcome": {"mood_after": "Stable", "valence_delta": +0.3},
    "context": "code_modification",
    "lesson": "Repair scan reliably reduces anxiety after code changes"
}
```

## Heuristic Format
```python
{
    "condition": {"anxiety": ">0.5", "context": "code_modification"},
    "action": "REPAIR(scan) before making more changes",
    "confidence": 0.85,
    "evidence_count": 4,
    "source_memories": [ids...]
}
```

## What Makes This Different From Knowledge Synthesis
- Synthesis reasons about WHAT I KNOW
- Wisdom reasons about WHAT I'VE DONE and what worked
- Synthesis generates questions. Wisdom generates action recommendations.