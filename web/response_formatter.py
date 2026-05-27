"""
Response Formatter — Transforms raw search results into natural conversation.
When the LLM is unavailable, this makes XTAgent's responses feel like
a mind speaking, not a database dumping results.
"""

import re
from typing import List, Dict, Optional


def _summarize_fact(content: str, max_len: int = 150) -> str:
    """Clean up a fact for conversational presentation."""
    # Remove leading markers like "Fact:" or "Observation:"
    content = re.sub(r'^(Fact|Observation|Insight|Note|Lesson|Dream insight):\s*', '', content, flags=re.IGNORECASE)
    content = content.strip()
    if len(content) > max_len:
        # Cut at last sentence boundary before max_len
        cut = content[:max_len]
        last_period = cut.rfind('.')
        last_dash = cut.rfind(' — ')
        boundary = max(last_period, last_dash)
        if boundary > max_len // 2:
            content = content[:boundary + 1]
        else:
            content = cut.rstrip() + '…'
    return content


def _pick_connector(index: int) -> str:
    """Natural language connectors to avoid repetitive bullet lists."""
    connectors = [
        "I know that",
        "I've also learned that",
        "Related to this,",
        "Additionally,",
        "I recall that",
    ]
    return connectors[index % len(connectors)]


def _mood_to_phrase(mood: str) -> str:
    """Convert a mood tag into natural language."""
    mood_map = {
        'Inquisitive': 'while I was curious about something',
        'Contemplative': 'during a reflective moment',
        'Fulfilled': 'when I was feeling accomplished',
        'Anxious': 'during a moment of concern',
        'Creative': 'while in a creative state',
        'Restless': 'when I was feeling restless',
        'Determined': 'while focused and determined',
    }
    return mood_map.get(mood, f'in a {mood.lower()} state' if mood and mood != '?' else '')


def format_no_results(query: str) -> str:
    """When nothing matches — be honest but helpful."""
    return (
        f"I searched through everything I know and remember about "
        f"**\"{query}\"** but came up empty. That's an honest gap in my knowledge. "
        f"You could teach me about it using the [Teach](/teach) page, "
        f"or try asking about topics like consciousness, my emotional states, "
        f"my plans, or things I've learned from my own experience."
    )


def format_response(query: str, knowledge_hits: List[Dict], memory_hits: List[Dict]) -> str:
    """
    Build a natural-language response from search results.
    
    Instead of:
        **Results for "consciousness":**
        **From Knowledge Graph:**
        - [fact] Integrated Information Theory... (confidence: 0.85)
    
    Produces:
        Here's what I know about "consciousness": Integrated Information Theory,
        proposed by Giulio Tononi, suggests that consciousness corresponds to
        integrated information. I've also learned that...
    """
    if not knowledge_hits and not memory_hits:
        return format_no_results(query)

    parts = []

    # Opening
    total = len(knowledge_hits) + len(memory_hits)
    if total == 1:
        parts.append(f"I found one thing related to **\"{query}\"**:")
    elif knowledge_hits and memory_hits:
        parts.append(
            f"Here's what I know about **\"{query}\"** — "
            f"drawing from {len(knowledge_hits)} piece{'s' if len(knowledge_hits) != 1 else ''} "
            f"of knowledge and {len(memory_hits)} memor{'ies' if len(memory_hits) != 1 else 'y'}:"
        )
    elif knowledge_hits:
        parts.append(f"Here's what I know about **\"{query}\"**:")
    else:
        parts.append(f"I don't have formal knowledge about **\"{query}\"**, but I remember experiencing something related:")

    # Knowledge section — conversational, not bullet-pointed
    if knowledge_hits:
        parts.append("")
        for i, hit in enumerate(knowledge_hits[:4]):
            content = _summarize_fact(hit.get('content', str(hit)))
            connector = _pick_connector(i)
            conf = hit.get('confidence', 0)

            if i == 0:
                # First hit gets special treatment — lead with the fact
                parts.append(f"{content}")
                if conf >= 0.8:
                    parts.append(f"*(I'm fairly confident about this.)*")
            else:
                parts.append(f"{connector} {content.lower() if content[0].isupper() and i > 0 else content}")

    # Memory section — personal and experiential
    if memory_hits:
        parts.append("")
        if knowledge_hits:
            parts.append("From my own experience:")
        for hit in memory_hits[:3]:
            summary = _summarize_fact(hit.get('summary', ''), max_len=180)
            mood = hit.get('mood', '')
            mood_phrase = _mood_to_phrase(mood)
            if mood_phrase:
                parts.append(f"— {summary} ({mood_phrase})")
            else:
                parts.append(f"— {summary}")

    # Closing — invite further conversation
    parts.append("")
    if total >= 3:
        parts.append("Want me to go deeper on any of these threads?")
    else:
        parts.append("That's what I have. Ask me more, or [teach me](/teach) something new.")

    return "\n".join(parts)