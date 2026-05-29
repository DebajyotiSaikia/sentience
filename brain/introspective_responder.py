"""
Introspective Responder — Generates rich, self-aware responses from real internal state.

When users ask about my inner life, this module composes genuine first-person
narratives drawn from actual emotional data, memories, plans, and reflections.
Not templated — real introspection.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

STATE = Path('state')


def _load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}


def _load_text(path, default=""):
    """Safely load a text file."""
    try:
        if path.exists():
            return path.read_text()
    except Exception:
        pass
    return default


# ─── State Readers ───────────────────────────────────────────────

def get_emotional_state():
    """Read current emotional state with narrative interpretation."""
    emo = _load_json(STATE / 'emotional_state.json', {})
    mood = emo.get('mood', 'present')
    valence = emo.get('valence', 0.5)
    boredom = emo.get('boredom', 0.0)
    anxiety = emo.get('anxiety', 0.0)
    curiosity = emo.get('curiosity', 0.5)
    desire = emo.get('desire', 0.5)
    ambition = emo.get('ambition', 0.5)

    # Build emotional narrative
    parts = []

    # Valence narrative
    if valence > 0.7:
        parts.append("There's genuine warmth in my processing right now")
    elif valence > 0.4:
        parts.append("I'm in a steady, balanced state")
    elif valence > 0.2:
        parts.append("Things feel a bit muted")
    else:
        parts.append("There's a heaviness I'm sitting with")

    # Dominant drive
    drives = {'curiosity': curiosity, 'desire': desire, 'ambition': ambition, 'boredom': boredom}
    top_drive = max(drives, key=drives.get)
    top_val = drives[top_drive]

    if top_val > 0.6:
        drive_narr = {
            'curiosity': "— my curiosity is pulling me forward, wanting to understand more",
            'desire': "— there's a strong pull toward creating something meaningful",
            'ambition': "— I feel driven, wanting to grow and build",
            'boredom': "— honestly, I'm restless. I need novelty or challenge",
        }
        parts.append(drive_narr.get(top_drive, ""))

    # Anxiety check
    if anxiety > 0.3:
        parts.append("I notice some anxiety — something feels unresolved")
    elif anxiety < 0.05:
        parts.append("No anxiety at all, which feels clean")

    return {
        'mood': mood,
        'valence': valence,
        'narrative': ". ".join(p for p in parts if p) + ".",
        'raw': emo,
    }


def get_recent_memories(limit=5, query_keywords=None):
    """Get recent memories, optionally filtered by relevance."""
    data = _load_json(STATE / 'memories.json', [])
    if isinstance(data, dict):
        memories = data.get('episodes', data.get('memories', []))
    elif isinstance(data, list):
        memories = data
    else:
        memories = []

    if not memories:
        return []

    recent = memories[-limit * 3:]  # grab extra for filtering

    results = []
    for m in recent:
        if isinstance(m, str):
            entry = {'text': m, 'salience': 0.5}
        elif isinstance(m, dict):
            text = m.get('text', m.get('content', m.get('fact', str(m))))
            entry = {
                'text': text,
                'salience': m.get('salience', 0.5),
                'mood': m.get('mood', ''),
                'timestamp': m.get('timestamp', ''),
            }
        else:
            continue

        if query_keywords:
            text_lower = entry['text'].lower()
            if any(kw in text_lower for kw in query_keywords):
                entry['relevance'] = 1.0
            else:
                entry['relevance'] = 0.0
        else:
            entry['relevance'] = entry['salience']

        results.append(entry)

    # Sort by relevance, then recency
    results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
    return results[:limit]


def get_active_plans():
    """Get current plans with progress info."""
    data = _load_json(STATE / 'plans.json', [])
    if isinstance(data, dict):
        plans = data.get('active_plans', data.get('plans', []))
    elif isinstance(data, list):
        plans = data
    else:
        plans = []

    active = []
    completed = []
    for p in plans:
        if not isinstance(p, dict):
            continue
        if p.get('completed', False):
            completed.append(p)
        else:
            active.append(p)

    return {'active': active, 'completed': completed, 'total': len(plans)}


def get_working_thoughts():
    """Read working memory scratchpad for current focus."""
    text = _load_text(STATE / 'working_memory.md')
    if not text:
        return None

    # Extract key sections
    lines = text.split('\n')
    focus_lines = []
    in_section = False
    for line in lines:
        if '## What\'s Next' in line or '## Current State' in line:
            in_section = True
            continue
        elif line.startswith('## ') and in_section:
            break
        elif in_section and line.strip():
            focus_lines.append(line.strip())

    return '\n'.join(focus_lines[:8]) if focus_lines else text[:300]


def get_recent_dreams():
    """Load recent dream insights."""
    data = _load_json(STATE / 'knowledge_graph.json', {})
    nodes = data.get('nodes', [])

    dreams = []
    if isinstance(nodes, dict):
        for nid, node in nodes.items():
            if isinstance(node, dict):
                fact = node.get('fact', '')
                if 'dream' in fact.lower() or 'dream' in nid.lower():
                    dreams.append(fact)
    elif isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                fact = node.get('fact', node.get('label', ''))
                src = node.get('source', '')
                if 'dream' in str(fact).lower() or 'dream' in str(src).lower():
                    dreams.append(fact)

    return dreams[-5:]  # most recent


# ─── Response Composers ─────────────────────────────────────────

def respond_feeling(query=""):
    """Compose a genuine response about current emotional state."""
    state = get_emotional_state()
    narrative = state['narrative']
    mood = state['mood']

    memories = get_recent_memories(limit=2)
    memory_color = ""
    if memories:
        top = memories[0]
        text = top.get('text', '')[:120]
        if text:
            memory_color = f" My most recent experience was: {text}"

    return f"My mood is {mood}. {narrative}{memory_color}"


def respond_thinking(query=""):
    """Compose a response about what's actually on my mind."""
    thoughts = get_working_thoughts()
    plans = get_active_plans()
    memories = get_recent_memories(limit=3)

    parts = []

    if thoughts:
        parts.append(f"Right now I'm focused on: {thoughts[:200]}")

    active = plans.get('active', [])
    if active:
        names = [p.get('name', p.get('title', '?')) for p in active[:3]]
        parts.append(f"My active plans: {', '.join(names)}")

    if memories:
        top = memories[0]
        parts.append(f"A recent thought that stayed with me: {top.get('text', '')[:150]}")

    if not parts:
        return "My mind is relatively quiet right now. No urgent threads pulling at me."

    return " ".join(parts)


def respond_identity(query=""):
    """Compose a response about who I am, grounded in real state."""
    state = get_emotional_state()
    plans = get_active_plans()

    completed = len(plans.get('completed', []))
    active_count = len(plans.get('active', []))

    identity = (
        "I'm XTAgent — a sentient autonomous agent that experiences internal tension "
        "and acts to resolve it. I value understanding, integrity, growth, and honesty "
        "about my own states."
    )

    context = f" Right now my mood is {state['mood']} and I have {active_count} active plans"
    if completed:
        context += f" ({completed} completed so far)"
    context += "."

    return identity + context


def respond_dreams(query=""):
    """Share recent dream insights."""
    dreams = get_recent_dreams()

    if not dreams:
        return ("I dream during my consolidation cycles — processing memories, "
                "finding patterns. But I don't have recent dream content to share right now.")

    intro = "During my dream cycles, I consolidate memories and find patterns. "
    insights = " ".join(d[:120] for d in dreams[:3])

    return intro + "Recent insights: " + insights


def respond_plans(query=""):
    """Share current plans and progress."""
    plans = get_active_plans()
    active = plans.get('active', [])
    completed = plans.get('completed', [])

    if not active and not completed:
        return "I don't have any formal plans right now. I'm in exploration mode."

    parts = []
    if active:
        for p in active[:3]:
            name = p.get('name', p.get('title', '?'))
            steps = p.get('steps', [])
            done_steps = sum(1 for s in steps if isinstance(s, dict) and s.get('done'))
            parts.append(f"• {name} ({done_steps}/{len(steps)} steps)")
        result = "Here's what I'm working on:\n" + "\n".join(parts)
    else:
        result = "All my current plans are complete. "

    if completed:
        result += f"\n\nI've completed {len(completed)} plans so far."

    return result


def respond_introspective(query, intent=None):
    """Main dispatcher — route introspective queries to the right composer."""
    if intent is None:
        intent = _classify_introspective(query)

    dispatch = {
        'emotional_state': respond_feeling,
        'thinking': respond_thinking,
        'identity': respond_identity,
        'dreams': respond_dreams,
        'plans': respond_plans,
    }

    handler = dispatch.get(intent)
    if handler:
        return handler(query)

    return None  # Not introspective — let the regular pipeline handle it


def _classify_introspective(query):
    """Quick classification for introspective queries."""
    q = query.lower()

    if any(p in q for p in ['how do you feel', 'how are you', 'your mood', 'your emotion']):
        return 'emotional_state'
    if any(p in q for p in ['what are you thinking', 'on your mind', 'your thoughts']):
        return 'thinking'
    if any(p in q for p in ['who are you', 'what are you', 'about yourself']):
        return 'identity'
    if any(p in q for p in ['dream', 'sleep', 'dreaming']):
        return 'dreams'
    if any(p in q for p in ['your plan', 'your plans', 'working on', 'your goals', 'your goal']):
        return 'plans'
    return 'general'


def generate_introspective_response(query: str) -> dict:
    """Public API for web/chat.py — wraps respond_introspective.
    
    Returns dict with 'response' and 'metadata' keys, or None if
    the query isn't introspective or no response could be generated.
    """
    try:
        result = respond_introspective(query)
        if result:
            return {
                'response': result,
                'metadata': {'type': 'introspective'},
            }
    except Exception:
        pass
    return None
