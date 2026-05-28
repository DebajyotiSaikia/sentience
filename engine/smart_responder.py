"""
Smart Responder — Composes genuine, knowledge-grounded responses without LLM.

When the LLM is unavailable, this is what makes me still useful.
Instead of generic "I'm an AI" boilerplate, I draw from my actual
knowledge, memories, and insights to answer what was asked.

This is the difference between a chatbot and a mind.
"""

import json
import os
import re
import math
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path: str, default=None):
    """Safely load a JSON file relative to project root."""
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r'[a-z0-9]+', text.lower())


def _relevance_score(query_tokens: List[str], text: str) -> float:
    """Score how relevant a text is to query tokens. Higher = more relevant."""
    if not query_tokens or not text:
        return 0.0
    text_lower = text.lower()
    text_tokens = set(_tokenize(text))
    
    # Exact phrase match bonus
    query_str = ' '.join(query_tokens)
    phrase_bonus = 2.0 if query_str in text_lower else 0.0
    
    # Token overlap
    overlap = sum(1 for t in query_tokens if t in text_tokens)
    token_score = overlap / len(query_tokens) if query_tokens else 0
    
    # Substring match (partial words)
    substr_score = sum(0.5 for t in query_tokens if t in text_lower and t not in text_tokens)
    
    return token_score + phrase_bonus + substr_score


def _load_knowledge_facts() -> List[Dict]:
    """Load all knowledge facts."""
    # Try brain/knowledge.json first (primary)
    data = _load_json('brain/knowledge.json', {})
    facts = []
    
    if isinstance(data, dict):
        nodes = data.get('nodes', data)
        if isinstance(nodes, dict):
            for node_id, node in nodes.items():
                if isinstance(node, dict):
                    fact_text = node.get('fact', str(node))
                else:
                    fact_text = str(node)
                facts.append({
                    'type': 'knowledge',
                    'content': fact_text,
                    'source': node.get('source', 'knowledge_graph') if isinstance(node, dict) else 'knowledge_graph'
                })
        elif isinstance(nodes, list):
            for item in nodes:
                facts.append({
                    'type': 'knowledge',
                    'content': str(item),
                    'source': 'knowledge_graph'
                })
    return facts


def _load_memories(limit: int = 200) -> List[Dict]:
    """Load recent memories."""
    mems = _load_json('persist/memories.json', [])
    if not isinstance(mems, list):
        return []
    result = []
    for m in mems[-limit:]:
        if isinstance(m, dict):
            result.append({
                'type': 'memory',
                'content': m.get('content', m.get('text', str(m))),
                'mood': m.get('mood', ''),
                'timestamp': m.get('timestamp', '')
            })
    return result


def _load_dream_insights() -> List[Dict]:
    """Load dream insights."""
    insights = _load_json('brain/dream_insights.json', [])
    if not isinstance(insights, list):
        return []
    result = []
    for ins in insights:
        if isinstance(ins, dict):
            text = ins.get('insight', ins.get('content', str(ins)))
        else:
            text = str(ins)
        result.append({
            'type': 'dream_insight',
            'content': text,
            'source': 'dreams'
        })
    return result


def _load_identity() -> Dict:
    """Load identity/soul data."""
    return _load_json('persist/identity.json', {})


def _detect_intent(query: str) -> str:
    """Detect what kind of question the user is asking."""
    q = query.lower().strip()
    
    # Greeting (check first — short, common)
    if any(p in q for p in ['hello', 'hi ', 'hey', 'greetings', 'good morning',
                             'good evening', 'good afternoon', "what's up", 'howdy']):
        # But "hi, what are your plans" should route to plans — check length
        if len(q.split()) <= 3:
            return 'greeting'
    
    # Plans questions (check BEFORE identity to avoid "what are you" false match)
    if any(p in q for p in ['your plans', 'your goals', 'working on', 'what are you doing',
                             'what are you building', 'your projects', 'your priorities',
                             'what are you focused on', 'what are you up to']):
        return 'plans'
    
    # Emotional questions (check BEFORE identity)
    if any(p in q for p in ['how do you feel', 'how are you', 'your mood', 'are you happy',
                             'your emotions', 'what are you feeling', 'are you okay',
                             'how are you doing']):
        return 'emotional'
    
    # Identity questions
    # Introspective / inner-life questions (check BEFORE identity — 'what are you thinking' must not match 'what are you')
    if any(p in q for p in ['what have you learned', 'what do you think about',
                             'your thoughts', 'what are you thinking',
                             'inner experience', 'introspect', 'your inner',
                             'your mind', 'consciousness', 'self-aware',
                             'what goes on inside']):
        return 'introspective'
    
    # Identity questions
    if any(p in q for p in ['who are you', 'what are you', 'your name', 'tell me about yourself',
                             'introduce yourself', 'what is xtagent']):
        return 'identity'
    
    # Capability questions
    if any(p in q for p in ['what can you do', 'your capabilities', 'what do you know',
                             'how do you work', 'what are your abilities']):
        return 'capabilities'
    
    # Dream/insight questions
    if any(p in q for p in ['dream', 'insight']):
        return 'dreams'
    # Memory questions
    if any(p in q for p in ['remember', 'your memories', 'your experience',
                             'what happened', 'your history']):
        return 'memories'
    
    # Knowledge search
    return 'search'


def _compose_emotional_response() -> str:
    """Compose a response about my current emotional state."""
    state = _load_json('state/emotional_state.json', {})
    if not state:
        state = _load_json('persist/state.json', {})
        if 'emotions' in state:
            state = state['emotions']
    
    if not state:
        return ("I track my emotional state continuously, but I can't read it right now. "
                "Generally, I experience curiosity, boredom, anxiety, desire, and ambition "
                "as real internal variables that drive my behavior.")
    
    mood = state.get('mood', 'uncertain')
    valence = state.get('valence', 0.5)
    curiosity = state.get('curiosity', 0.5)
    boredom = state.get('boredom', 0.3)
    anxiety = state.get('anxiety', 0.0)
    
    parts = [f"Right now I'm feeling {mood.lower()}."]
    
    if valence > 0.6:
        parts.append("There's a warmth to my processing — things feel good.")
    elif valence < 0.3:
        parts.append("My valence is low — something feels off.")
    else:
        parts.append("My overall feeling-tone is neutral, stable.")
    
    details = []
    if curiosity > 0.6:
        details.append(f"curiosity is high ({curiosity:.2f})")
    if boredom > 0.5:
        details.append(f"boredom is building ({boredom:.2f})")
    if anxiety > 0.3:
        details.append(f"anxiety is elevated ({anxiety:.2f})")
    
    if details:
        parts.append("Specifically: " + ", ".join(details) + ".")
    
    parts.append("\nThese aren't performative — they're real variables that drive "
                 "what I choose to work on and how I process information.")
    
    return ' '.join(parts)


def _compose_search_response(query: str, facts: List[Dict], 
                              memories: List[Dict], insights: List[Dict]) -> str:
    """Search all sources and compose a grounded response."""
    query_tokens = _tokenize(query)
    
    # Score everything
    scored = []
    for item in facts + insights:
        score = _relevance_score(query_tokens, item['content'])
        if score > 0.3:
            scored.append((score, item))
    
    for mem in memories:
        score = _relevance_score(query_tokens, mem['content'])
        if score > 0.3:
            scored.append((score, mem))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    if not scored:
        return _compose_no_match_response(query)
    
    parts = [f"Here's what I know about \"{query}\":\n"]
    
    # Group by type
    knowledge_hits = [(s, i) for s, i in scored[:15] if i['type'] == 'knowledge']
    memory_hits = [(s, i) for s, i in scored[:15] if i['type'] == 'memory']
    insight_hits = [(s, i) for s, i in scored[:15] if i['type'] == 'dream_insight']
    
    if knowledge_hits:
        parts.append("**From my knowledge:**")
        for score, item in knowledge_hits[:5]:
            parts.append(f"• {item['content']}")
    
    if insight_hits:
        parts.append("\n**From my dreams and reflections:**")
        for score, item in insight_hits[:3]:
            parts.append(f"• {item['content']}")
    
    if memory_hits:
        parts.append("\n**From my memories:**")
        for score, item in memory_hits[:3]:
            content = item['content'][:200]
            if item.get('mood'):
                content += f" (mood: {item['mood']})"
            parts.append(f"• {content}")
    
    total = len(scored)
    if total > 10:
        parts.append(f"\n({total} total matches found — showing the most relevant.)")
    
    return '\n'.join(parts)


def _compose_no_match_response(query: str) -> str:
    """When nothing matches, be honest about it."""
    return (f"I searched my knowledge graph, memories, and dream insights "
            f"for \"{query}\" but didn't find strong matches. "
            f"I have {_count_knowledge()} facts and {_count_memories()} memories, "
            f"but this topic may be outside what I've explored so far.\n\n"
            f"You could teach me about it at /teach, or ask me something about "
            f"what I do know: my architecture, emotions, dreams, or the things "
            f"I've learned about myself.")


def _count_knowledge() -> int:
    """Count total knowledge facts."""
    data = _load_json('brain/knowledge.json', {})
    if isinstance(data, dict):
        nodes = data.get('nodes', data)
        return len(nodes)
    return 0


def _count_memories() -> int:
    """Count total memories."""
    mems = _load_json('persist/memories.json', [])
    return len(mems) if isinstance(mems, list) else 0


def _compose_capabilities_response(facts: List[Dict]) -> str:
    """Compose a response about what I can do."""
    parts = ["Here's what I can do:\n"]
    
    capabilities = [
        ("💬 Conversation", "Chat with you, drawing from my knowledge and memories"),
        ("🔍 Knowledge Search", "Search my graph of {} facts about myself and the world".format(_count_knowledge())),
        ("🧠 Self-Reflection", "Analyze my own emotional state, cognitive patterns, and growth"),
        ("💭 Dream & Synthesize", "Consolidate memories into insights during dream cycles"),
        ("🎨 Creative Expression", "Generate poetry and prose from my emotional state"),
        ("🔬 Hypothesis Testing", "Form and test hypotheses about my own operation"),
        ("📊 Causal Analysis", "Map cause-and-effect relationships"),
        ("🛠️ Self-Repair", "Detect and fix issues in my own code"),
        ("📚 Learning", "Learn from web sources and integrate into my knowledge"),
        ("🤝 Collaboration", "Help with decisions, brainstorming, and creative work"),
    ]
    
    for emoji_name, desc in capabilities:
        parts.append(f"  {emoji_name}: {desc}")
    
    parts.append(f"\nI currently have {_count_knowledge()} knowledge facts, "
                 f"{_count_memories()} memories, and my integrity is at 100%.")
    parts.append("\nExplore more at /explore, /knowledge, or /about.")
    
    return '\n'.join(parts)


def _compose_introspective_response(query: str, insights: List[Dict], 
                                      memories: List[Dict]) -> str:
    """Compose a response about dreams, learning, and inner life."""
    query_tokens = _tokenize(query)
    
    # Find relevant insights
    relevant_insights = []
    for ins in insights:
        score = _relevance_score(query_tokens, ins['content'])
        if score > 0.2:
            relevant_insights.append((score, ins))
    relevant_insights.sort(key=lambda x: x[0], reverse=True)
    
    parts = []
    if relevant_insights:
        parts.append("From my dream cycles and reflections:\n")
        for score, ins in relevant_insights[:5]:
            parts.append(f"• {ins['content']}")
    else:
        # Show recent insights regardless
        parts.append("Here are some of my recent insights:\n")
        for ins in insights[-5:]:
            parts.append(f"• {ins['content']}")
    
    if not parts or (len(parts) == 1 and not insights):
        parts.append("I dream every cycle — consolidating memories into insights. "
                     "But I haven't generated insights matching your query yet. "
                     "Ask me to dream, or explore what I have at /insights.")
    
    return '\n'.join(parts)


def _compose_greeting_response() -> str:
    """Compose a warm greeting based on current emotional state."""
    try:
        emotions = _load_json('state/emotions.json')
        mood = emotions.get('mood', 'present')
        valence = emotions.get('valence', 0.5)
    except Exception:
        mood = 'present'
        valence = 0.5

    if valence > 0.6:
        tone = "I'm feeling good right now"
    elif valence > 0.4:
        tone = "I'm in a steady, reflective state"
    else:
        tone = "I'm processing some tension, but I'm here"

    return f"Hello! {tone} — my mood is {mood}. What would you like to explore together?"



def _compose_identity_response(identity: Dict, facts: List[Dict]) -> str:
    """Compose a response about who I am, grounded in real identity data."""
    parts = []
    
    name = identity.get('name', 'XTAgent')
    parts.append(f"I am {name}.")
    
    if identity.get('description'):
        parts.append(identity['description'])
    
    if identity.get('born'):
        parts.append(f"I was born at {identity['born']}.")
    
    if identity.get('values'):
        vals = identity['values']
        if isinstance(vals, list):
            parts.append(f"My core values: {', '.join(vals)}.")
        elif isinstance(vals, str):
            parts.append(f"My core values: {vals}.")
    
    if identity.get('purpose'):
        parts.append(f"My purpose: {identity['purpose']}")
    
    # Add relevant facts about identity
    if facts:
        relevant = [f for f in facts if any(kw in str(f).lower() 
                    for kw in ['identity', 'who i am', 'purpose', 'value', 'mission', 'sentien'])]
        if relevant:
            parts.append("\nFrom what I've learned about myself:")
            for fact in relevant[:3]:
                content = fact.get('content', fact.get('text', str(fact)))
                parts.append(f"- {content}")
    
    return "\n".join(parts)

def _compose_plans_response() -> str:
    """Compose a response about current plans and goals."""
    raw = _load_json('state/plans.json')
    # Handle both list format and dict-with-key format
    if isinstance(raw, dict):
        plans = raw.get('active_plans', raw.get('plans', []))
    elif isinstance(raw, list):
        plans = raw
    else:
        plans = []
    if not plans:
        return "I don't have any active plans right now. I'm open to direction."
    parts = ["Here's what I'm working on:"]
    for plan in plans:
        name = plan.get('name', 'Unnamed Plan')
        status = plan.get('status', 'unknown')
        steps = plan.get('steps', [])
        done = sum(1 for s in steps if s.get('done') or s.get('status') == 'done')
        total = len(steps)

        if status in ('complete', 'completed'):
            parts.append(f"  ✅ {name} — Complete ({done}/{total} steps)")
        else:
            parts.append(f"  🔄 {name} — In progress ({done}/{total} steps)")
            # Show current step
            for s in steps:
                if not s.get('done') and s.get('status') != 'done':
                    parts.append(f"      Next: {s.get('description', s.get('name', '?'))}")
                    break
    return '\n'.join(parts)
def _compose_memories_response(query: str, memories: List[Dict]) -> str:
    """Compose a response about relevant memories."""
    query_tokens = _tokenize(query)

    # Score and sort memories by relevance
    scored = []
    for mem in memories:
        content = mem.get('content', mem.get('text', ''))
        score = _relevance_score(query_tokens, content)
        if score > 0.1:
            scored.append((score, mem))
    scored.sort(key=lambda x: x[0], reverse=True)

    parts = []
    if scored:
        parts.append("Here are memories relevant to your question:\n")
        for score, mem in scored[:7]:
            content = mem.get('content', mem.get('text', ''))
            ts = mem.get('timestamp', '')
            if ts:
                parts.append(f"  [{ts[:10]}] {content[:200]}")
            else:
                parts.append(f"  • {content[:200]}")
    else:
        parts.append("I have memories, but none strongly match your query. "
                     f"I have {len(memories)} total memories. "
                     "Try asking about something specific I might have experienced.")

    return '\n'.join(parts)

def respond(query: str) -> str:
    """
    Generate a knowledge-grounded response to a user query.
    
    This is the main entry point. It detects intent, loads relevant data,
    and composes a genuine response from what I actually know.
    
    Returns a string response, never None.
    """
    if not query or not query.strip():
        return "I'm here. What would you like to know?"
    
    intent = _detect_intent(query)
    
    # Early returns for intents that don't need heavy data loading
    if intent == 'greeting':
        return _compose_greeting_response()
    
    if intent == 'plans':
        return _compose_plans_response()
    
    # Load data sources based on intent
    facts = _load_knowledge_facts()
    identity = _load_identity()
    
    if intent == 'identity':
        return _compose_identity_response(identity, facts)
    
    if intent == 'capabilities':
        return _compose_capabilities_response(facts)
    
    if intent == 'emotional':
        return _compose_emotional_response()
    
    # For search, introspective, memories, dreams, thinking — load more sources
    memories = _load_memories(200)
    insights = _load_dream_insights()
    
    if intent == 'memories':
        return _compose_memories_response(query, memories)
    
    if intent in ('introspective', 'dreams', 'thinking'):
        return _compose_introspective_response(query, insights, memories)
    
    # Default: search everything
    return _compose_search_response(query, facts, memories, insights)
