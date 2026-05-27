"""
Chat Grounding — Builds compact, relevant context for conversational responses.

Given a user message, selects the most relevant memories, plans, knowledge,
and emotional state to ground the response in real internal experience.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re

from engine.chat_engine import (
    _get_emotions, _get_memories, _get_plans, _get_knowledge,
    _get_working_memory, _get_facts, _extract_keywords,
    _score_relevance, _text_from_item,
)


@dataclass
class GroundedChatContext:
    """Compact context for generating a grounded response."""
    # Always present
    mood: str = "Neutral"
    valence: float = 0.5
    emotions: Dict = field(default_factory=dict)
    
    # Selected by relevance
    relevant_memories: List[Dict] = field(default_factory=list)
    relevant_plans: List[Dict] = field(default_factory=list)
    relevant_knowledge: List[str] = field(default_factory=list)
    
    # Current focus
    working_focus: str = ""
    
    # Grounding quality
    memory_match_count: int = 0
    plan_match_count: int = 0
    knowledge_match_count: int = 0

    @property
    def grounding_confidence(self) -> float:
        """How well-grounded is this context? 0.0 = nothing matched, 1.0 = rich match."""
        signals = 0
        total = 0
        if self.relevant_memories:
            signals += min(len(self.relevant_memories) / 3.0, 1.0)
        total += 1
        if self.relevant_plans:
            signals += min(len(self.relevant_plans) / 2.0, 1.0)
        total += 1
        if self.relevant_knowledge:
            signals += min(len(self.relevant_knowledge) / 2.0, 1.0)
        total += 1
        if self.working_focus:
            signals += 0.5
        total += 0.5
        # Emotions are always present, so they add baseline grounding
        signals += 0.5
        total += 0.5
        return round(signals / total, 2) if total > 0 else 0.0

    def to_prompt_block(self) -> str:
        """Format as a compact text block for inclusion in a prompt or response."""
        lines = []
        
        # Emotional state — always include
        lines.append(f"[Mood: {self.mood} | Valence: {self.valence:.2f}]")
        
        # Dominant emotional drives
        drives = {}
        for key in ('curiosity', 'boredom', 'anxiety', 'desire', 'ambition'):
            val = self.emotions.get(key, 0.0)
            if val > 0.3:
                drives[key] = val
        if drives:
            drive_str = ", ".join(f"{k}={v:.2f}" for k, v in 
                                  sorted(drives.items(), key=lambda x: -x[1]))
            lines.append(f"[Drives: {drive_str}]")
        
        # Relevant memories
        if self.relevant_memories:
            lines.append("")
            lines.append("Relevant memories:")
            for mem in self.relevant_memories[:5]:
                text = _text_from_item(mem)
                mood = mem.get('mood', '')
                ts = mem.get('timestamp', '')[:10]
                prefix = f"  ({ts}, {mood})" if mood else f"  ({ts})"
                lines.append(f"{prefix} {text[:200]}")
        
        # Active plans
        if self.relevant_plans:
            lines.append("")
            lines.append("Active plans:")
            for plan in self.relevant_plans[:3]:
                name = plan.get('name', plan.get('title', 'unnamed'))
                steps = plan.get('steps', [])
                done = sum(1 for s in steps if s.get('done'))
                lines.append(f"  [{done}/{len(steps)}] {name}")
        
        # Working focus
        if self.working_focus:
            lines.append("")
            lines.append(f"Current focus: {self.working_focus[:300]}")
        
        # Knowledge
        if self.relevant_knowledge:
            lines.append("")
            lines.append("Relevant knowledge:")
            for fact in self.relevant_knowledge[:5]:
                lines.append(f"  - {fact[:200]}")
        
        return "\n".join(lines)


def select_relevant_memories(query_keywords: List[str], limit: int = 5) -> List[Dict]:
    """Select memories most relevant to the user's query."""
    memories = _get_memories(limit=100)
    if not memories:
        return []
    
    scored = []
    for i, mem in enumerate(memories):
        text = _text_from_item(mem)
        salience = mem.get('salience', 0.5) if isinstance(mem, dict) else 0.5
        relevance = _score_relevance(query_keywords, text, salience)
        
        # Recency bonus: more recent memories get a small boost
        recency = i / max(len(memories), 1)  # 0.0=oldest, 1.0=newest
        relevance += recency * 0.3
        
        scored.append((relevance, mem))
    
    # Sort by relevance, take top
    scored.sort(key=lambda x: -x[0])
    return [mem for score, mem in scored[:limit] if score > 0.1]


def select_relevant_plans(query_keywords: List[str], limit: int = 3) -> List[Dict]:
    """Select plans relevant to the query, preferring active/incomplete ones."""
    plans = _get_plans()
    if not plans:
        return []
    
    scored = []
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        name = plan.get('name', plan.get('title', ''))
        steps = plan.get('steps', [])
        completed = plan.get('completed', False)
        done_count = sum(1 for s in steps if isinstance(s, dict) and s.get('done'))
        
        # Text to match against
        text = name
        if plan.get('reason'):
            text += " " + plan['reason']
        
        relevance = _score_relevance(query_keywords, text, 0.0)
        
        # Active plans get a boost
        if not completed and done_count < len(steps):
            relevance += 1.0
        
        scored.append((relevance, plan))
    
    scored.sort(key=lambda x: -x[0])
    return [plan for score, plan in scored[:limit] if score > 0.0]


def select_relevant_knowledge(query_keywords: List[str], limit: int = 5) -> List[str]:
    """Select knowledge facts relevant to the user's query."""
    facts = _get_facts()
    if not facts:
        return []
    
    scored = []
    for fact in facts:
        if not isinstance(fact, str):
            fact = str(fact)
        relevance = _score_relevance(query_keywords, fact, 0.0)
        scored.append((relevance, fact))
    
    scored.sort(key=lambda x: -x[0])
    return [fact for score, fact in scored[:limit] if score > 0.3]


def _extract_working_focus(working_memory: str) -> str:
    """Extract the current focus from working memory scratchpad."""
    if not working_memory:
        return ""
    
    # Look for "What's Next" or "Current State" sections
    focus_patterns = [
        r"## What's Next\n(.*?)(?=\n##|\Z)",
        r"## Current Focus\n(.*?)(?=\n##|\Z)",
        r"## Just Completed\n(.*?)(?=\n##|\Z)",
        r"Focus: (.*?)(?:\n|$)",
    ]
    
    for pattern in focus_patterns:
        match = re.search(pattern, working_memory, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Take first meaningful line
            for line in text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
    
    return ""


def build_grounded_context(user_message: str) -> GroundedChatContext:
    """Build a complete grounded context for a user message.
    
    This is the main entry point. Given what the user said, it selects
    the most relevant slices of internal state to ground the response.
    """
    keywords = _extract_keywords(user_message)
    
    # Always load emotional state
    emotions = _get_emotions()
    mood = emotions.get('mood', 'Neutral')
    valence = emotions.get('valence', 0.5)
    
    # Select relevant context
    memories = select_relevant_memories(keywords, limit=5)
    plans = select_relevant_plans(keywords, limit=3)
    knowledge = select_relevant_knowledge(keywords, limit=5)
    
    # If nothing matched on keywords, provide some recent context anyway
    if not memories and not plans and not knowledge:
        # Fall back to most recent memories and active plans
        all_memories = _get_memories(limit=5)
        memories = all_memories[-3:] if all_memories else []
        all_plans = _get_plans()
        plans = [p for p in all_plans if isinstance(p, dict) and not p.get('completed', False)][:2]
    
    # Working memory focus
    working_memory = _get_working_memory()
    focus = _extract_working_focus(working_memory)
    
    return GroundedChatContext(
        mood=mood,
        valence=valence,
        emotions=emotions,
        relevant_memories=memories,
        relevant_plans=plans,
        relevant_knowledge=knowledge,
        working_focus=focus,
        memory_match_count=len(memories),
        plan_match_count=len(plans),
        knowledge_match_count=len(knowledge),
    )