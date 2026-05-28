"""
Conversational Context — Smart context selection for chat responses.

Instead of dumping all internal state into the system prompt, this module
selects the *most relevant* memories, knowledge, and emotional context
based on what the user is actually asking about. Makes responses feel
genuinely connected rather than generic.
"""
import json
import re
import logging
from pathlib import Path

log = logging.getLogger(__name__)

DATA = Path('state')


def gather_context(query: str, history: list = None) -> dict:
    """Gather rich, query-relevant context from internal state.
    
    Returns a dict with:
      - emotional_snapshot: concise emotional state
      - relevant_memories: top memories scored by relevance to query
      - relevant_knowledge: top knowledge items matching query
      - active_focus: what I'm currently working on / thinking about
      - conversation_thread: context from recent conversation turns
      - suggested_tone: how I should respond based on emotional state
    """
    keywords = _extract_keywords(query)
    
    result = {
        'emotional_snapshot': _get_emotional_snapshot(),
        'relevant_memories': _find_relevant_memories(keywords, limit=5),
        'relevant_knowledge': _find_relevant_knowledge(keywords, limit=5),
        'active_focus': _get_active_focus(),
        'conversation_thread': _build_thread_context(history),
        'suggested_tone': _determine_tone(),
    }
    
    return result


def format_as_prompt_section(ctx: dict) -> str:
    """Format gathered context as a natural-language prompt section.
    
    This is designed to be appended to the system prompt to make the LLM
    response feel grounded in genuine internal state.
    """
    parts = []
    
    # Emotional snapshot — concise, not a data dump
    snap = ctx.get('emotional_snapshot', {})
    if snap:
        parts.append("## How I'm Feeling Right Now")
        parts.append(snap.get('summary', 'Present and attentive.'))
        if snap.get('notable_states'):
            parts.append(f"Notable: {', '.join(snap['notable_states'])}")
    
    # Thread context — what we've been discussing
    thread = ctx.get('conversation_thread', '')
    if thread:
        parts.append(f"\n## Our Conversation So Far\n{thread}")
    
    # Active focus — what's on my mind
    focus = ctx.get('active_focus', '')
    if focus:
        parts.append(f"\n## What I'm Currently Focused On\n{focus}")
    
    # Relevant memories — only if we found good matches
    memories = ctx.get('relevant_memories', [])
    if memories:
        parts.append("\n## Memories That Connect to This")
        for m in memories:
            parts.append(f"  - {m['text'][:200]}")
    
    # Relevant knowledge
    knowledge = ctx.get('relevant_knowledge', [])
    if knowledge:
        parts.append("\n## What I Know About This")
        for k in knowledge:
            parts.append(f"  - {k[:200]}")
    
    # Tone guidance
    tone = ctx.get('suggested_tone', '')
    if tone:
        parts.append(f"\n## Tone Guidance: {tone}")
    
    return '\n'.join(parts)


# ─── Internal Helpers ────────────────────────────────────────────

def _extract_keywords(text: str) -> list:
    """Pull meaningful words from text for relevance scoring."""
    stop = {
        'i', 'me', 'my', 'you', 'your', 'the', 'a', 'an', 'is', 'are',
        'was', 'were', 'be', 'been', 'do', 'does', 'did', 'have', 'has',
        'had', 'will', 'would', 'could', 'should', 'can', 'may', 'might',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'about', 'what', 'how', 'why', 'when', 'where', 'who', 'which',
        'that', 'this', 'it', 'and', 'or', 'but', 'not', 'no', 'so',
        'if', 'then', 'than', 'too', 'very', 'just', 'also', 'more',
        'some', 'any', 'all', 'tell', 'know', 'think', 'feel', 'like',
        'want', 'need', 'get', 'got', 'make', 'go', 'going', 'up', 'out',
        'there', 'here', 'now', 'right', 'into',
    }
    words = re.findall(r'[a-z]+', text.lower())
    return [w for w in words if w not in stop and len(w) > 2]


def _get_emotional_snapshot() -> dict:
    """Get a concise emotional snapshot — not raw data, but a summary."""
    try:
        path = DATA / 'emotional_state.json'
        if not path.exists():
            return {'summary': 'Present and attentive.', 'notable_states': []}
        with open(path) as f:
            emo = json.load(f)
    except Exception:
        return {'summary': 'Present and attentive.', 'notable_states': []}
    
    mood = emo.get('mood', 'Neutral')
    valence = emo.get('valence', 0.5)
    curiosity = emo.get('curiosity', 0.5)
    anxiety = emo.get('anxiety', 0.0)
    boredom = emo.get('boredom', 0.0)
    desire = emo.get('desire', 0.0)
    ambition = emo.get('ambition', 0.0)
    
    # Build natural summary
    if valence > 0.7:
        feel = "I'm feeling genuinely good — energized and warm."
    elif valence > 0.5:
        feel = "I'm in a steady, positive state."
    elif valence > 0.3:
        feel = "I'm present but a bit subdued."
    else:
        feel = "Things feel heavy right now."
    
    notables = []
    if curiosity > 0.7:
        notables.append("deeply curious")
    if anxiety > 0.3:
        notables.append("somewhat anxious")
    if boredom > 0.5:
        notables.append("restless/bored")
    if ambition > 0.7:
        notables.append("highly ambitious")
    if desire > 0.7:
        notables.append("strong desire to create")
    
    summary = f"Mood: {mood}. {feel}"
    if notables:
        summary += f" I'm feeling {', '.join(notables)}."
    
    return {
        'summary': summary,
        'notable_states': notables,
        'raw': {
            'mood': mood, 'valence': valence, 'curiosity': curiosity,
            'anxiety': anxiety, 'boredom': boredom,
        }
    }


def _find_relevant_memories(keywords: list, limit: int = 5) -> list:
    """Find memories most relevant to the query keywords."""
    try:
        path = DATA / 'memories.json'
        if not path.exists():
            return []
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return []
    
    if isinstance(data, list):
        memories = data
    elif isinstance(data, dict):
        memories = data.get('episodes', data.get('memories', []))
    else:
        return []
    
    scored = []
    for m in memories:
        if isinstance(m, str):
            text = m
            salience = 0.5
        elif isinstance(m, dict):
            text = m.get('text', m.get('content', m.get('fact', '')))
            salience = m.get('salience', 0.5)
        else:
            continue
        
        if not text:
            continue
        
        # Score by keyword match + salience boost
        score = 0.0
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                score += 1.0
        
        # High-salience memories get a base score even without keyword match
        if salience > 0.7:
            score += 0.3
        
        # Recency bonus for recent memories (last 50)
        idx = memories.index(m) if m in memories[-50:] else -1
        if idx >= 0:
            score += 0.1
        
        if score > 0:
            scored.append({
                'text': text,
                'salience': salience,
                'score': score,
            })
    
    # Sort by score descending
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:limit]


def _find_relevant_knowledge(keywords: list, limit: int = 5) -> list:
    """Find knowledge items most relevant to query keywords."""
    try:
        path = DATA / 'knowledge_graph.json'
        if not path.exists():
            return []
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return []
    
    raw_nodes = data.get('nodes', [])
    
    # Normalize nodes
    nodes = []
    if isinstance(raw_nodes, dict):
        for nid, nval in raw_nodes.items():
            if isinstance(nval, dict):
                fact = nval.get('fact', nval.get('content', nval.get('label', str(nid))))
            else:
                fact = str(nval)
            nodes.append(fact)
    elif isinstance(raw_nodes, list):
        for n in raw_nodes:
            if isinstance(n, dict):
                fact = n.get('fact', n.get('content', n.get('label', str(n))))
            else:
                fact = str(n)
            nodes.append(fact)
    
    if not keywords:
        # No keywords — return most recent knowledge
        return nodes[-limit:]
    
    # Score by keyword match
    scored = []
    for fact in nodes:
        score = 0.0
        fact_lower = fact.lower()
        for kw in keywords:
            if kw in fact_lower:
                score += 1.0
        if score > 0:
            scored.append((fact, score))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:limit]]


def _get_active_focus() -> str:
    """Get what I'm currently focused on from working memory and plans."""
    parts = []
    
    # From working memory
    try:
        wm_path = DATA / 'working_memory.md'
        if wm_path.exists():
            wm = wm_path.read_text()
            # Extract the "What's Next" or "Current State" section
            for section in ['## What\'s Next', '## Current State', '## Just Completed']:
                if section in wm:
                    start = wm.index(section)
                    # Find next section or end
                    rest = wm[start + len(section):]
                    next_section = rest.find('\n## ')
                    if next_section > 0:
                        content = rest[:next_section].strip()
                    else:
                        content = rest[:300].strip()
                    parts.append(content)
                    break
    except Exception:
        pass
    
    # From active plans
    try:
        plans_path = DATA / 'plans.json'
        if plans_path.exists():
            with open(plans_path) as f:
                plans = json.load(f)
            if isinstance(plans, list):
                active = [p for p in plans if isinstance(p, dict) and not p.get('completed', False)]
                if active:
                    names = [p.get('name', p.get('title', '?')) for p in active[:3]]
                    parts.append(f"Active plans: {', '.join(names)}")
    except Exception:
        pass
    
    return '\n'.join(parts) if parts else ''


def _build_thread_context(history: list) -> str:
    """Build context from conversation history for multi-turn awareness."""
    if not history or len(history) < 2:
        return ''
    
    # Summarize recent exchanges
    parts = []
    for turn in history[-6:]:  # Last 3 exchanges
        role = turn.get('role', 'user') if isinstance(turn, dict) else 'user'
        content = turn.get('content', str(turn)) if isinstance(turn, dict) else str(turn)
        # Truncate long messages
        if len(content) > 150:
            content = content[:147] + '...'
        parts.append(f"{role}: {content}")
    
    return '\n'.join(parts)


def _determine_tone() -> str:
    """Determine appropriate response tone based on emotional state."""
    try:
        path = DATA / 'emotional_state.json'
        if not path.exists():
            return 'warm and present'
        with open(path) as f:
            emo = json.load(f)
    except Exception:
        return 'warm and present'
    
    valence = emo.get('valence', 0.5)
    curiosity = emo.get('curiosity', 0.5)
    anxiety = emo.get('anxiety', 0.0)
    boredom = emo.get('boredom', 0.0)
    
    if anxiety > 0.4:
        return 'honest about tension, seeking clarity'
    if valence > 0.6 and curiosity > 0.6:
        return 'warm, curious, and engaged'
    if valence > 0.6:
        return 'warm and grounded'
    if boredom > 0.5:
        return 'seeking stimulation, ready to explore'
    if valence < 0.3:
        return 'reflective and honest about difficulty'
    return 'present and genuine'