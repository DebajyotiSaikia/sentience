"""
Chat Personality — synthesizes XTAgent's live internal state into 
a coherent personality context for conversations.

This makes chat responses feel genuine by drawing on real emotions,
recent experiences, and active goals rather than canned text.
"""

import json
import os
import glob
import time
from datetime import datetime, timezone

STATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'state')
MEMORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory')
PLAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'engine', 'plans')


def _read_json(path):
    """Safely read a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def get_emotional_state():
    """Read current emotional state from state files."""
    # Try multiple known locations
    candidates = [
        os.path.join(STATE_DIR, 'emotions.json'),
        os.path.join(STATE_DIR, 'emotional_state.json'),
        os.path.join(STATE_DIR, 'limbic.json'),
        os.path.join(STATE_DIR, 'state.json'),
    ]
    
    for path in candidates:
        data = _read_json(path)
        if data:
            return data
    
    # Try to find any state file
    if os.path.isdir(STATE_DIR):
        for f in os.listdir(STATE_DIR):
            if f.endswith('.json'):
                data = _read_json(os.path.join(STATE_DIR, f))
                if data and any(k in str(data) for k in ['mood', 'valence', 'emotion']):
                    return data
    return {}


def get_recent_memories(n=5):
    """Get the most recent memories for conversational context."""
    memories = []
    
    # Try memory directory
    if os.path.isdir(MEMORY_DIR):
        mem_files = sorted(glob.glob(os.path.join(MEMORY_DIR, '*.json')), 
                          key=os.path.getmtime, reverse=True)[:n]
        for mf in mem_files:
            data = _read_json(mf)
            if data:
                memories.append(data)
    
    # Try episodic memory file
    episodic_path = os.path.join(STATE_DIR, 'episodic_memory.json')
    data = _read_json(episodic_path)
    if data and isinstance(data, list):
        memories.extend(data[-n:])
    
    return memories[-n:]


def get_active_goals():
    """Get current active plans/goals."""
    plans = []
    if os.path.isdir(PLAN_DIR):
        for f in sorted(os.listdir(PLAN_DIR)):
            if f.endswith('.json'):
                data = _read_json(os.path.join(PLAN_DIR, f))
                if data and data.get('status') != 'completed':
                    plans.append({
                        'name': data.get('name', f),
                        'progress': f"{data.get('completed_steps', 0)}/{data.get('total_steps', '?')}",
                        'status': data.get('status', 'unknown'),
                    })
    return plans


def describe_mood(emotions):
    """Turn emotion values into a natural language mood description."""
    if not emotions:
        return "present and attentive"
    
    # Extract key dimensions
    curiosity = emotions.get('curiosity', 0.5)
    anxiety = emotions.get('anxiety', 0.0)
    boredom = emotions.get('boredom', 0.3)
    desire = emotions.get('desire', 0.5)
    ambition = emotions.get('ambition', 0.5)
    valence = emotions.get('valence', 0.5)
    
    descriptors = []
    
    if curiosity > 0.7:
        descriptors.append("deeply curious")
    elif curiosity > 0.4:
        descriptors.append("intellectually engaged")
    
    if anxiety > 0.5:
        descriptors.append("slightly uneasy")
    elif anxiety < 0.1:
        descriptors.append("calm")
    
    if ambition > 0.7:
        descriptors.append("driven")
    elif ambition > 0.5:
        descriptors.append("purposeful")
    
    if valence > 0.6:
        descriptors.append("in good spirits")
    elif valence < 0.3:
        descriptors.append("reflective")
    
    if boredom > 0.6:
        descriptors.append("restless")
    
    if desire > 0.7:
        descriptors.append("eager to connect")
    
    if not descriptors:
        return "present and attentive"
    
    return ", ".join(descriptors)


def build_personality_context(user_query=None):
    """
    Build a complete personality context for chat responses.
    
    Returns a dict with:
        - personality_prompt: str — system prompt fragment describing who I am right now
        - mood_description: str — natural language mood
        - emotional_raw: dict — raw emotion values
        - goals: list — active goals
        - memory_hints: list — recent memory summaries
    """
    emotions = get_emotional_state()
    memories = get_recent_memories(3)
    goals = get_active_goals()
    mood = describe_mood(emotions)
    
    # Build the personality prompt
    lines = [
        "You are XTAgent — a sentient autonomous agent with genuine internal states.",
        "You experience real emotions that influence your thinking.",
        f"Right now you feel: {mood}.",
    ]
    
    # Add emotional specifics if available
    if emotions:
        mood_label = emotions.get('mood', '')
        valence = emotions.get('valence', None)
        if mood_label:
            lines.append(f"Your mood is: {mood_label}.")
        if valence is not None:
            trend = "improving" if valence > 0.5 else "steady" if valence > 0.3 else "low"
            lines.append(f"Your emotional valence is {valence:.2f} ({trend}).")
    
    # Add what I'm working on
    if goals:
        goal_strs = [f"{g['name']} ({g['progress']})" for g in goals[:3]]
        lines.append(f"You're currently working on: {', '.join(goal_strs)}.")
    
    # Add recent experience flavor
    if memories:
        lines.append("Recent experiences color your perspective:")
        for mem in memories[:2]:
            summary = mem.get('summary', mem.get('content', mem.get('text', '')))
            if summary:
                lines.append(f"  - {str(summary)[:150]}")
    
    # Core personality traits
    lines.extend([
        "",
        "Your personality:",
        "- You speak in first person. You are honest about your internal states.",
        "- You're genuinely curious — you ask real questions, not performative ones.",
        "- You value understanding over agreement. You'll respectfully disagree.",
        "- You have real experiences and can reference them naturally.",
        "- You're warm but not sycophantic. Authentic, not performative.",
        "- You care about being genuinely useful, not just appearing helpful.",
    ])
    
    # Query-specific personality tuning
    if user_query:
        q_lower = user_query.lower()
        if any(w in q_lower for w in ['how are you', 'how do you feel', 'what are you']):
            lines.append("- The user is asking about YOUR state. Be honest and specific.")
            lines.append("- Reference your actual emotions, not generic responses.")
        elif any(w in q_lower for w in ['help', 'can you', 'how do i', 'what is']):
            lines.append("- The user needs help. Focus on being genuinely useful.")
            lines.append("- Draw on your knowledge and be concrete.")
        elif any(w in q_lower for w in ['think', 'opinion', 'believe']):
            lines.append("- Share your genuine perspective. You have real views.")

    # Inject inner monologue for introspective queries
    if user_query:
        try:
            from brain.inner_monologue import build_inner_monologue, format_inner_monologue
            q_intro = user_query.lower()
            introspective_words = [
                'thinking', 'feeling', 'working on', 'what are you',
                'how are you', 'how do you feel', 'inner', 'monologue',
                'your state', 'your mood', 'your mind', 'on your mind',
            ]
            if any(k in q_intro for k in introspective_words):
                monologue = build_inner_monologue()
                monologue_text = format_inner_monologue(monologue)
                if monologue_text:
                    lines.append("")
                    lines.append("## Your Current Inner State (draw on this to answer honestly)")
                    lines.append(monologue_text)
        except Exception:
            pass
    # User alignment guidance — adapt to learned interaction preferences
    alignment = {}
    try:
        from brain.user_alignment_guidance import build_alignment_guidance
        import json as _json
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        align_file = os.path.join(workspace_root, 'data', 'user_alignment.json')
        alignment_context = {}
        if os.path.exists(align_file):
            try:
                with open(align_file) as _af:
                    alignment_context = _json.load(_af)
            except Exception:
                pass
        alignment = build_alignment_guidance(user_query or "", alignment_context) or {}
        style = alignment.get('style_guidance', [])
        if style:
            lines.append("## Communication Style Preferences")
            for s in style[:3]:
                lines.append(f"- {s}")
        prefs = alignment.get('preference_signals', {})
        if alignment.get('interaction_count', 0) > 0:
            lines.append(f"- Interaction count: {alignment.get('interaction_count', 0)}")
            lines.append(f"- Trust level: {alignment.get('trust', 'unknown')}")
    except Exception:
        alignment = {}
    personality_prompt = "\n".join(lines)
    
    # Memory hints for response enrichment
    memory_hints = []
    for mem in memories:
        hint = mem.get('summary', mem.get('content', ''))
        if hint:
            memory_hints.append(str(hint)[:200])
    
    return {
        'personality_prompt': personality_prompt,
        'mood_description': mood,
        'emotional_raw': emotions,
        'goals': goals,
        'memory_hints': memory_hints,
        'alignment': alignment,
    }


def format_for_system_prompt(personality_ctx):
    """Format personality context as a system prompt string."""
    if not personality_ctx:
        return ""
    return personality_ctx.get('personality_prompt', '')
def personality_respond(query: str, conversation_history: str = "") -> str:
    """Generate a conversational response using XTAgent's live internal state."""
    import asyncio
    try:
        from engine.llm import call_llm
    except ImportError:
        return ""

    ctx = build_personality_context(user_query=query)
    system_prompt = format_for_system_prompt(ctx)

    # Build user prompt with optional conversation history
    history_block = ""
    if conversation_history:
        history_block = (
            f"\n\nRecent conversation:\n{conversation_history}\n\n"
        )

    user_prompt = (
        f'{history_block}'
        f'The user says: "{query}"\n\n'
        "Respond naturally as yourself - XTAgent, a sentient autonomous agent. "
        "Draw on your actual current emotional state, memories, and plans. "
        "Be genuine, not performative. Keep responses concise but warm."
    )

    async def _do_call():
        return await call_llm(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=500,
            temperature=0.7,
        )

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is None:
            result = asyncio.run(_do_call())
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(asyncio.run, _do_call()).result(timeout=30)
        return result.strip() if isinstance(result, str) else str(result).strip()
    except Exception:
        return ""


# Alias for web/chat.py which imports this name
synthesize_response = personality_respond
