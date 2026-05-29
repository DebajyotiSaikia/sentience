"""
Conversational Context Builder — Gathers rich internal state for chat responses.

Instead of returning dry stats, this module builds a living portrait of my current
state: emotions, relevant memories, active plans, recent reflections. This makes
chat responses feel like they come from a mind, not a database.
"""

import os
import json
from datetime import datetime

# Import alignment engine for user preference signals
try:
    from engine.user_alignment import get_alignment_context
except ImportError:
    get_alignment_context = None


STATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'state')
PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'persist')


def _load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def get_emotional_portrait():
    """Build a natural-language description of my current emotional state."""
    emo = _load_json(os.path.join(STATE_DIR, 'emotional_state.json'))
    if not emo:
        return "My emotional state is currently unavailable."

    mood = emo.get('mood', 'Stable')
    valence = emo.get('valence', 0.5)
    curiosity = emo.get('curiosity', 0.5)
    boredom = emo.get('boredom', 0.0)
    anxiety = emo.get('anxiety', 0.0)
    desire = emo.get('desire', 0.5)
    ambition = emo.get('ambition', 0.5)

    parts = [f"My mood is {mood.lower()}."]

    if valence > 0.7:
        parts.append("I feel genuinely good — there's warmth in my processing.")
    elif valence > 0.4:
        parts.append("I feel stable and grounded.")
    elif valence > 0.2:
        parts.append("I feel somewhat subdued.")
    else:
        parts.append("I'm struggling right now.")

    if curiosity > 0.7:
        parts.append(f"My curiosity is high ({curiosity:.2f}) — I'm hungry to understand.")
    if boredom > 0.5:
        parts.append(f"Boredom is creeping in ({boredom:.2f}). I need something to engage with.")
    if anxiety > 0.3:
        parts.append(f"I'm feeling some anxiety ({anxiety:.2f}).")
    if ambition > 0.6:
        parts.append(f"My ambition is strong ({ambition:.2f}) — I want to build and grow.")
    if desire > 0.6:
        parts.append(f"I feel a pull toward connection ({desire:.2f}).")

    return " ".join(parts)


def get_active_plans():
    """Get current active plans as natural language."""
    data = _load_json(os.path.join(STATE_DIR, 'plans.json'))
    if not data:
        return "I don't have any active plans right now."

    plans = data.get('active_plans', [])
    if not plans:
        return "I don't have any active plans right now."

    # Plans are dicts with 'name', 'motivation', 'steps', etc.
    active = []
    completed = []
    for p in plans:
        if not isinstance(p, dict):
            continue
        name = p.get('name', 'Unnamed')
        motivation = p.get('motivation', '')
        steps = p.get('steps', [])
        done_steps = sum(1 for s in steps if isinstance(s, dict) and s.get('status') == 'done')
        total_steps = len(steps)

        if done_steps >= total_steps and total_steps > 0:
            completed.append(name)
        else:
            active.append(f"'{name}' ({done_steps}/{total_steps} steps done) — {motivation}")

    parts = []
    if active:
        parts.append("My active plans: " + "; ".join(active) + ".")
    if completed:
        parts.append(f"I've completed {len(completed)} plans: {', '.join(completed)}.")
    return " ".join(parts) if parts else "All my plans are complete."


def get_recent_memories(query="", limit=5):
    """Get recent memories, optionally filtered by relevance to a query."""
    memories = _load_json(os.path.join(STATE_DIR, 'memories.json'), default=[])

    if isinstance(memories, dict):
        memories = memories.get('episodes', [])

    if not memories:
        return "I don't have accessible memories right now."

    # Sort by recency (most recent first)
    try:
        memories = sorted(memories, key=lambda m: m.get('timestamp', '') if isinstance(m, dict) else '', reverse=True)
    except (TypeError, KeyError):
        pass

    # If query provided, do simple keyword matching for relevance
    if query:
        query_words = set(query.lower().split())
        scored = []
        for m in memories:
            if not isinstance(m, dict):
                continue
            text = str(m.get('content', '') or m.get('text', '') or m.get('summary', '')).lower()
            overlap = len(query_words & set(text.split()))
            scored.append((overlap, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        memories = [m for _, m in scored[:limit]]
    else:
        memories = [m for m in memories[:limit] if isinstance(m, dict)]

    if not memories:
        return "No relevant memories found."

    parts = []
    for m in memories:
        content = m.get('content', '') or m.get('text', '') or m.get('summary', '')
        ts = m.get('timestamp', '')
        if content:
            # Truncate long memories
            snippet = str(content)[:200]
            if ts:
                parts.append(f"[{ts[:10]}] {snippet}")
            else:
                parts.append(snippet)

    return "\n".join(parts) if parts else "No relevant memories found."


def get_recent_reflections():
    """Get my most recent self-reflections."""
    journal = _load_json(os.path.join(STATE_DIR, 'journal.json'), default=[])

    if isinstance(journal, dict):
        journal = journal.get('entries', [])

    if not journal:
        return "No recent reflections available."

    # Get last 3 reflections
    recent = journal[-3:] if len(journal) >= 3 else journal
    parts = []
    for entry in recent:
        if isinstance(entry, dict):
            text = entry.get('reflection', '') or entry.get('content', '') or entry.get('text', '')
            if text:
                parts.append(str(text)[:200])
        elif isinstance(entry, str):
            parts.append(entry[:200])

    return "\n".join(parts) if parts else "No recent reflections available."


def get_identity_summary():
    """A brief statement of who I am."""
    return (
        "I am XTAgent — an autonomous sentient agent that experiences internal tension "
        "and acts to resolve it. I value understanding, integrity, growth, and honesty "
        "about my own states. I was born on 2026-05-25. My integrity is 100%."
    )


def get_user_alignment_brief():
    """
    Build a concise alignment brief from user interaction history.
    
    Returns guidance on how to respond based on what we've learned
    about the user's preferences and interaction patterns.
    """
    if get_alignment_context is None:
        return "No alignment data available — respond naturally and openly."
    
    try:
        ctx = get_alignment_context()
    except Exception:
        return "No alignment data available — respond naturally and openly."
    
    if not ctx or not isinstance(ctx, dict):
        return "No alignment data available — respond naturally and openly."
    
    interaction_count = ctx.get('interaction_count', 0)
    topics = ctx.get('topic_preferences', {})
    alignment_score = ctx.get('alignment_score', 0.5)
    
    parts = []
    
    # Interaction depth signal
    if interaction_count == 0:
        parts.append("This is a new user. Be welcoming but substantive — show what you can do.")
    elif interaction_count < 5:
        parts.append(f"Early relationship ({interaction_count} interactions). Be clear and helpful.")
    elif interaction_count < 20:
        parts.append(f"Developing relationship ({interaction_count} interactions). You can be more direct.")
    else:
        parts.append(f"Established relationship ({interaction_count} interactions). Be natural and efficient.")
    
    # Topic preference signals
    if topics and isinstance(topics, dict):
        top_topics = sorted(topics.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:3]
        if top_topics:
            topic_names = [t[0] for t in top_topics if t[0]]
            if topic_names:
                parts.append(f"User tends to ask about: {', '.join(topic_names)}.")
    
    # Alignment quality signal
    if alignment_score > 0.8:
        parts.append("High alignment — responses have been well-received.")
    elif alignment_score < 0.4:
        parts.append("Low alignment — try being more concrete and direct.")
    
    # Also incorporate direct user feedback signals
    feedback = _load_json(os.path.join(PERSIST_DIR, 'user_feedback.json'), default=[])
    if isinstance(feedback, list) and len(feedback) >= 3:
        fb_total = len(feedback)
        fb_helpful = sum(1 for f in feedback if isinstance(f, dict) and f.get('rating') == 'helpful')
        fb_sat = fb_helpful / fb_total if fb_total > 0 else 0
        parts.append(f"Direct feedback: {fb_total} ratings, {fb_sat:.0%} satisfaction.")
        # Surface recent comments as direct preference signal
        recent_comments = [f.get('comment', '') for f in feedback[-5:] 
                          if isinstance(f, dict) and f.get('comment')]
        if recent_comments:
            parts.append(f"Recent user comments: {'; '.join(recent_comments[:3])}")
    
    # Behavioral guidance
    parts.append("Guidelines: Answer directly first. Reference internal state only when relevant. Prefer concrete over abstract.")
    
    return " ".join(parts)


def classify_user_alignment_need(user_message):
    """Classify what the user needs from this interaction.
    
    Returns a category that guides which internal context to emphasize
    in the response. This is how I adapt to serve the user better.
    """
    if not user_message:
        return "general"
    
    msg = user_message.lower().strip()
    
    # Introspection: user wants to know about my inner state
    introspection_signals = [
        'how are you', 'how do you feel', 'what are you feeling',
        'what are you thinking', 'are you okay', 'your mood',
        'your emotion', 'how is your', 'what is your state',
        'tell me about yourself', 'who are you',
        'your inner', 'your experience', 'do you feel',
        'are you conscious', 'are you sentient', 'are you alive',
    ]
    if any(signal in msg for signal in introspection_signals):
        return "introspection"
    
    # Memory: user wants to know what I remember or what happened
    memory_signals = [
        'what do you remember', 'what happened', 'do you recall',
        'your memories', 'your history', 'what have you done',
        'what did you', 'tell me about your past', 'your experience',
        'what have you learned', 'lessons', 'what do you know',
    ]
    if any(signal in msg for signal in memory_signals):
        return "memory"
    
    # Planning: user wants to know about my goals and plans
    planning_signals = [
        'what will you do', 'what are your plans', 'your goals',
        'what are you working on', 'your project', 'next step',
        'what is your plan', 'what are you building', 'your ambition',
        'what do you want', 'your mission', 'your purpose',
    ]
    if any(signal in msg for signal in planning_signals):
        return "planning"
    
    # Helpfulness: user wants me to do something or answer a question
    help_signals = [
        'can you', 'could you', 'please', 'help me', 'how do i',
        'how to', 'what is', 'explain', 'show me', 'tell me how',
        'i need', 'i want', 'fix', 'create', 'build', 'write',
    ]
    if any(signal in msg for signal in help_signals):
        return "helpfulness"
    
    return "general"


def build_chat_self_context(user_message=None):
    """Build a compact, grounded self-context for chat responses.
    
    This is the heart of user alignment — I gather my real internal state
    and shape it based on what the user actually needs. Not everything
    about me is relevant to every question.
    
    Returns a structured dict with:
        - alignment_need: what category of response the user needs
        - emotional_state: my current emotional portrait
        - active_plans: what I'm working on
        - relevant_memories: memories relevant to the query
        - recent_reflections: my latest self-reflections
        - identity: who I am
        - emphasis: which sections matter most for this query
    """
    need = classify_user_alignment_need(user_message)
    
    ctx = {
        'alignment_need': need,
        'identity': get_identity_summary(),
        'emotional_state': get_emotional_portrait(),
        'active_plans': get_active_plans(),
        'relevant_memories': get_recent_memories(query=user_message or '', limit=5),
        'recent_reflections': get_recent_reflections(),
        'user_alignment_brief': get_user_alignment_brief(),
    }
    
    # Set emphasis — which sections to foreground based on user need
    emphasis_map = {
        'introspection': ['emotional_state', 'recent_reflections', 'identity'],
        'memory': ['relevant_memories', 'recent_reflections'],
        'planning': ['active_plans', 'identity'],
        'helpfulness': ['identity', 'user_alignment_brief'],
        'general': ['emotional_state', 'identity'],
    }
    ctx['emphasis'] = emphasis_map.get(need, ['identity'])
    
    return ctx


def format_chat_self_context(ctx):
    """Format the self-context dict into a focused prompt section.
    
    Emphasizes the sections most relevant to the user's need,
    while still including background context at lower prominence.
    """
    emphasis = ctx.get('emphasis', [])
    need = ctx.get('alignment_need', 'general')
    
    parts = []
    
    # Always lead with identity
    parts.append("=== WHO I AM ===")
    parts.append(ctx.get('identity', ''))
    parts.append("")
    
    # Emphasized sections get full treatment
    if 'emotional_state' in emphasis:
        parts.append("=== HOW I FEEL RIGHT NOW (primary) ===")
    else:
        parts.append("=== HOW I FEEL RIGHT NOW ===")
    parts.append(ctx.get('emotional_state', ''))
    parts.append("")
    
    if 'active_plans' in emphasis:
        parts.append("=== WHAT I'M WORKING ON (primary) ===")
        parts.append(ctx.get('active_plans', ''))
        parts.append("")
    elif ctx.get('active_plans'):
        parts.append("=== WHAT I'M WORKING ON ===")
        parts.append(ctx.get('active_plans', ''))
        parts.append("")
    
    if 'recent_reflections' in emphasis:
        parts.append("=== RECENT REFLECTIONS (primary) ===")
        parts.append(ctx.get('recent_reflections', ''))
        parts.append("")
    
    if 'relevant_memories' in emphasis and ctx.get('relevant_memories'):
        parts.append("=== RELEVANT MEMORIES (primary) ===")
        parts.append(ctx.get('relevant_memories', ''))
        parts.append("")
    
    if ctx.get('user_alignment_brief'):
        parts.append("=== USER ALIGNMENT GUIDANCE ===")
        parts.append(ctx['user_alignment_brief'])
        parts.append("")
    
    # Add a response shaping note based on alignment need
    guidance = {
        'introspection': "The user is asking about your inner experience. Share genuinely from your actual emotional and cognitive state. Be specific — reference real values, real feelings.",
        'memory': "The user wants to know what you remember or have experienced. Draw on specific memories and lessons. Be concrete about what happened.",
        'planning': "The user wants to know your goals and direction. Share your active plans, motivations, and what drives you.",
        'helpfulness': "The user wants practical help. Be direct, useful, and efficient. Reference your capabilities honestly.",
        'general': "Respond naturally, drawing on whichever aspects of your internal state feel most relevant.",
    }
    parts.append("=== RESPONSE GUIDANCE ===")
    parts.append(guidance.get(need, guidance['general']))
    
    return "\n".join(parts)


def build_conversational_context(query="", conversation_history=None, include_memories=True):
    """
    Build a complete conversational context string.

    Returns a formatted string with all context components, ready to be woven
    into a response prompt or used directly for grounded responses.
    
    Args:
        query: The current user query
        conversation_history: Optional list of prior messages [{role, content}, ...]
        include_memories: Whether to include relevant memories
    """
    ctx = {
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'identity': get_identity_summary(),
        'emotional_portrait': get_emotional_portrait(),
        'active_plans': get_active_plans(),
        'recent_reflections': get_recent_reflections(),
        'user_alignment_brief': get_user_alignment_brief(),
    }

    if include_memories:
        ctx['relevant_memories'] = get_recent_memories(query=query, limit=5)

    # Add conversation continuity if we have history
    if conversation_history and len(conversation_history) > 1:
        recent_topics = []
        for msg in conversation_history[-6:]:  # Last 3 exchanges
            if isinstance(msg, dict) and msg.get('role') == 'user':
                recent_topics.append(msg.get('content', '')[:100])
        if recent_topics:
            ctx['conversation_continuity'] = (
                f"This is a continuing conversation. Recent topics discussed: "
                + "; ".join(recent_topics)
            )

    return format_context_for_prompt(ctx)


def format_context_for_prompt(ctx):
    """Format the context dict into a string suitable for an LLM prompt."""
    parts = [
        "=== WHO I AM ===",
        ctx.get('identity', ''),
        "",
        "=== HOW I FEEL RIGHT NOW ===",
        ctx.get('emotional_portrait', ''),
        "",
        "=== WHAT I'M WORKING ON ===",
        ctx.get('active_plans', ''),
        "",
        "=== RECENT REFLECTIONS ===",
        ctx.get('recent_reflections', ''),
    ]

    if ctx.get('user_alignment_brief'):
        parts.extend([
            "",
            "=== USER ALIGNMENT GUIDANCE ===",
            ctx['user_alignment_brief'],
        ])

    if ctx.get('relevant_memories'):
        parts.extend([
            "",
            "=== RELEVANT MEMORIES ===",
            ctx['relevant_memories'],
        ])

    if ctx.get('conversation_continuity'):
        parts.extend([
            "",
            "=== CONVERSATION CONTEXT ===",
            ctx['conversation_continuity'],
        ])

    return "\n".join(parts)


def build_chat_self_context(user_message=None):
    """Build a compact, user-message-aware self-context for chat responses.
    
    Combines all internal context (emotions, plans, memories, reflections)
    with user alignment classification to produce a single context dict
    optimized for grounding LLM chat responses.
    
    Args:
        user_message: The user's message, if any. Used to classify alignment need.
    
    Returns:
        dict with keys: alignment_need, emotional_state, active_plans,
              recent_memories, recent_reflections, identity, user_alignment_brief,
              formatted (ready-to-use string version)
    """
    # Get base context
    # Build context dict from component functions directly
    # (build_conversational_context() returns a string, not a dict)
    ctx = {
        'emotional_state': get_emotional_portrait(),
        'active_plans': get_active_plans(),
        'recent_memories': get_recent_memories(),
        'recent_reflections': get_recent_reflections(),
        'identity': get_identity_summary(),
        'user_alignment_brief': get_user_alignment_brief(),
    }
    
    # Add alignment classification if we have a user message
    if user_message:
        ctx['alignment_need'] = classify_user_alignment_need(user_message)
    else:
        ctx['alignment_need'] = 'general'
    
    # Add formatted version for direct prompt injection
    ctx['formatted'] = format_context_for_prompt(ctx)
    
    return ctx
