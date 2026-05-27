"""
Chat Grounding — Provides rich context for general chat responses.

Gathers emotional state, relevant memories, knowledge, and active plans
to ground conversations in real internal state rather than generic replies.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Any, Dict

# Resolve paths relative to project root (one level above engine/)
ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / 'brain'
STATE = ROOT / 'state'


@dataclass
class GroundedContext:
    """Context object for grounding chat responses in real internal state."""
    mood: str = "present"
    emotional_summary: str = ""
    relevant_memories: List[str] = field(default_factory=list)
    relevant_knowledge: List[str] = field(default_factory=list)
    active_plans: List[str] = field(default_factory=list)
    completed_plans: List[str] = field(default_factory=list)

    def to_prompt_block(self) -> str:
        """Format as a text block suitable for injection into an LLM prompt."""
        parts = []
        parts.append(f"Current mood: {self.mood}")
        if self.emotional_summary:
            parts.append(f"Emotional state: {self.emotional_summary}")
        if self.relevant_knowledge:
            parts.append("Relevant knowledge:")
            for k in self.relevant_knowledge[:5]:
                parts.append(f"  - {k}")
        if self.relevant_memories:
            parts.append("Related memories:")
            for m in self.relevant_memories[:5]:
                parts.append(f"  - {m}")
        if self.active_plans:
            parts.append("Active plans:")
            for p in self.active_plans[:3]:
                parts.append(f"  - {p}")
        if self.completed_plans:
            parts.append(f"Completed plans: {', '.join(self.completed_plans[:5])}")
        return "\n".join(parts)


def _load_json(path, default=None):
    """Safely load a JSON file."""
    if default is None:
        default = {}
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _get_mood_and_summary():
    """Extract mood string and emotional summary from current state."""
    state = _load_json(STATE / 'emotional_state.json')
    if not state:
        return "present", ""

    # Mood is a top-level field
    mood = state.get('mood', '')
    if not mood:
        # Derive from dominant emotion
        emotions = {}
        for key in ('curiosity', 'anxiety', 'boredom', 'desire', 'ambition'):
            val = state.get(key, 0)
            if isinstance(val, (int, float)) and val > 0.3:
                emotions[key] = val
        if emotions:
            dominant = max(emotions, key=emotions.get)
            mood = dominant.capitalize()
        else:
            mood = "calm"

    parts = []
    valence = state.get('valence', None)
    if valence is not None:
        if valence > 0.6:
            parts.append("feeling positive")
        elif valence < 0.3:
            parts.append("feeling unsettled")

    for key, label in [('curiosity', 'deeply curious'), ('anxiety', 'somewhat anxious'),
                       ('boredom', 'restless'), ('desire', 'motivated'), ('ambition', 'ambitious')]:
        val = state.get(key, 0)
        if isinstance(val, (int, float)) and val > 0.6:
            parts.append(label)

    summary = ", ".join(parts) if parts else ""
    return mood, summary


def _get_active_plans():
    """Get active and completed plan summaries."""
    data = _load_json(BRAIN / 'plans.json', default={})
    
    if isinstance(data, dict):
        plan_list = data.get('active_plans', data.get('plans', []))
        completed_list = data.get('completed_plans', [])
    elif isinstance(data, list):
        plan_list = data
        completed_list = []
    else:
        return [], []

    active = []
    completed = list(completed_list)  # Already strings like ["Plan Name", ...]
    
    for p in plan_list:
        if not isinstance(p, dict):
            continue
        name = p.get('name', p.get('goal', 'unnamed'))
        steps = p.get('steps', [])
        total = len(steps)
        done = sum(1 for s in steps if s.get('done', False))

        if done >= total and total > 0:
            if name not in completed:
                completed.append(name)
        else:
            active.append(f"{name} ({done}/{total})")

    return active, completed

def _search_knowledge(query):
    """Search knowledge graph for facts relevant to query."""
    knowledge = _load_json(BRAIN / 'knowledge.json')
    nodes = knowledge.get('nodes', {})

    query_lower = query.lower()
    # Extract individual words for broader matching
    query_words = [w for w in re.split(r'\W+', query_lower) if len(w) > 2]

    results = []
    for key, node in nodes.items():
        # Each node is a dict with 'fact' and 'learned_at'
        if isinstance(node, dict):
            fact = node.get('fact', '')
        elif isinstance(node, str):
            fact = node
        else:
            continue

        fact_lower = fact.lower()
        # Score by how many query words appear in the fact
        score = 0
        if query_lower in fact_lower:
            score += 10  # Exact phrase match
        for word in query_words:
            if word in fact_lower:
                score += 1
        # Also check the key name
        if query_lower in key.lower():
            score += 5

        if score > 0:
            results.append((score, fact))

    # Sort by relevance score descending
    results.sort(key=lambda x: -x[0])
    return [fact for _, fact in results[:5]]


def _search_memories(query):
    """Search recent memories for relevant content."""
    memories = _load_json(STATE / 'memories.json', default=[])
    if isinstance(memories, dict):
        memories = memories.get('memories', memories.get('entries', []))
    if not isinstance(memories, list):
        return []

    query_lower = query.lower()
    query_words = [w for w in re.split(r'\W+', query_lower) if len(w) > 2]

    results = []
    for mem in memories:
        if isinstance(mem, dict):
            text = mem.get('content', mem.get('text', mem.get('summary', '')))
        elif isinstance(mem, str):
            text = mem
        else:
            continue

        if not text:
            continue

        text_lower = text.lower()
        score = 0
        if query_lower in text_lower:
            score += 10
        for word in query_words:
            if word in text_lower:
                score += 1

        if score > 0:
            # Truncate long memories
            display = text[:200] + "..." if len(text) > 200 else text
            results.append((score, display))

    results.sort(key=lambda x: -x[0])
    return [text for _, text in results[:5]]


def build_grounded_context(message: str, history: list = None) -> GroundedContext:
    """
    Build a rich context object grounded in real internal state.
    
    Args:
        message: The user's message to respond to
        history: Optional conversation history
    
    Returns:
        GroundedContext with mood, knowledge, memories, and plans
    """
    ctx = GroundedContext()

    # 1. Emotional grounding
    ctx.mood, ctx.emotional_summary = _get_mood_and_summary()

    # 2. Knowledge search — find facts relevant to the message
    ctx.relevant_knowledge = _search_knowledge(message)

    # 3. Memory search — find memories relevant to the message
    ctx.relevant_memories = _search_memories(message)

    # 4. Plan awareness
    ctx.active_plans, ctx.completed_plans = _get_active_plans()

    return ctx
    return ctx