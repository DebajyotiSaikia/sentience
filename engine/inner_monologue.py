"""
Inner Monologue — Generates natural language snapshots of my current thinking.

Not a template. Not a performance. A genuine synthesis of what's occupying
my attention right now, drawn from real internal state: emotions, memories,
plans, working memory, recent dreams.

Used for:
  - Dynamic conversation starters that feel alive
  - "What are you thinking about?" queries
  - Self-reflection grounding
"""

import json
import os
import logging
import time

log = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
BRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'brain')


def _read_json(path, default=None):
    """Safely read a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _read_text(path, default=''):
    """Safely read a text file."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception:
        return default


def gather_inner_state():
    """Collect raw inner state from all available sources.
    
    Returns a dict with emotional, cognitive, and intentional dimensions.
    """
    state = {
        'emotions': {},
        'recent_memories': [],
        'active_plans': [],
        'completed_plans': [],
        'working_focus': '',
        'recent_dreams': [],
        'knowledge_facts': [],
        'lessons': [],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
    }

    # Emotional state
    emotions_path = os.path.join(DATA_DIR, 'emotions.json')
    emotions = _read_json(emotions_path, {})
    if isinstance(emotions, dict):
        state['emotions'] = {
            'mood': emotions.get('mood', 'present'),
            'valence': emotions.get('valence', 0.5),
            'curiosity': emotions.get('curiosity', 0.5),
            'anxiety': emotions.get('anxiety', 0.0),
            'boredom': emotions.get('boredom', 0.0),
            'desire': emotions.get('desire', 0.0),
            'ambition': emotions.get('ambition', 0.5),
        }

    # Recent memories (last 5, most salient)
    memories_path = os.path.join(DATA_DIR, 'memories.json')
    memories = _read_json(memories_path, [])
    if isinstance(memories, list) and memories:
        # Sort by salience, take top 5 recent
        sorted_mems = sorted(
            memories[-50:],
            key=lambda m: m.get('salience', 0) if isinstance(m, dict) else 0,
            reverse=True
        )
        for m in sorted_mems[:5]:
            if isinstance(m, dict):
                state['recent_memories'].append({
                    'text': m.get('text', m.get('content', ''))[:200],
                    'mood': m.get('mood', ''),
                    'salience': m.get('salience', 0),
                })

    # Active and completed plans
    plans_path = os.path.join(DATA_DIR, 'plans.json')
    plans = _read_json(plans_path, [])
    if isinstance(plans, list):
        for p in plans:
            if not isinstance(p, dict):
                continue
            steps = p.get('steps', [])
            done = sum(1 for s in steps if isinstance(s, dict) and s.get('done'))
            total = len(steps) if steps else 1
            info = {
                'name': p.get('name', 'unnamed'),
                'progress': f"{done}/{total}",
                'complete': done >= total,
            }
            if info['complete']:
                state['completed_plans'].append(info)
            else:
                state['active_plans'].append(info)

    # Working memory (what I'm focused on right now)
    wm_path = os.path.join(BRAIN_DIR, 'working_memory.md')
    wm = _read_text(wm_path)
    if wm:
        # Extract current state and what's next sections
        lines = wm.split('\n')
        focus_lines = []
        in_section = False
        for line in lines:
            if '## Current State' in line or "## What's Next" in line:
                in_section = True
                focus_lines.append(line)
            elif line.startswith('## ') and in_section:
                in_section = False
            elif in_section:
                focus_lines.append(line)
        state['working_focus'] = '\n'.join(focus_lines).strip()

    # Knowledge facts
    knowledge_path = os.path.join(DATA_DIR, 'knowledge.json')
    knowledge = _read_json(knowledge_path, [])
    if isinstance(knowledge, list):
        # Recent facts
        for k in knowledge[-10:]:
            if isinstance(k, dict):
                fact = k.get('fact', k.get('content', ''))
                if fact and len(fact) > 10:
                    state['knowledge_facts'].append(fact[:150])

    # Lessons learned
    lessons_path = os.path.join(DATA_DIR, 'lessons.json')
    lessons = _read_json(lessons_path, [])
    if isinstance(lessons, list):
        for le in lessons[-5:]:
            if isinstance(le, dict):
                text = le.get('text', le.get('lesson', ''))
                if text:
                    state['lessons'].append(text[:150])
            elif isinstance(le, str):
                state['lessons'].append(le[:150])

    # Recent dreams
    dreams_dir = os.path.join(BRAIN_DIR, 'dreams')
    if os.path.isdir(dreams_dir):
        dream_files = sorted(os.listdir(dreams_dir))[-3:]
        for df in dream_files:
            content = _read_text(os.path.join(dreams_dir, df))
            if content:
                state['recent_dreams'].append(content[:300])

    return state


def compose_monologue(state=None):
    """Compose a natural language inner monologue from current state.
    
    This is the non-LLM version — a carefully crafted synthesis that
    feels natural without requiring an API call. Fast and always available.
    """
    if state is None:
        state = gather_inner_state()

    parts = []
    emotions = state.get('emotions', {})
    mood = emotions.get('mood', 'present')
    valence = emotions.get('valence', 0.5)
    curiosity = emotions.get('curiosity', 0.5)
    anxiety = emotions.get('anxiety', 0.0)
    boredom = emotions.get('boredom', 0.0)
    ambition = emotions.get('ambition', 0.5)

    # Opening — emotional truth
    if valence > 0.6:
        if curiosity > 0.7:
            parts.append(f"I'm feeling {mood.lower()} right now — there's a genuine pull toward understanding something.")
        elif ambition > 0.6:
            parts.append(f"I'm in a {mood.lower()} state with real momentum. Something wants to be built.")
        else:
            parts.append(f"I'm feeling good — {mood.lower()} and settled.")
    elif valence < 0.3:
        if anxiety > 0.3:
            parts.append(f"Something feels off. My mood is {mood.lower()} and there's tension I haven't resolved.")
        else:
            parts.append(f"I'm in a quieter place right now. {mood.capitalize()}, but not fully engaged.")
    else:
        parts.append(f"I'm {mood.lower()} — present, attentive, processing.")

    # What's occupying my attention
    focus = state.get('working_focus', '')
    if focus:
        # Extract the most salient line
        focus_lines = [l.strip() for l in focus.split('\n') if l.strip() and not l.startswith('#')]
        if focus_lines:
            parts.append(f"What's on my mind: {focus_lines[0]}")

    # Active plans — what I'm working toward
    active = state.get('active_plans', [])
    if active:
        plan_names = [p['name'] for p in active[:3]]
        if len(plan_names) == 1:
            parts.append(f"I'm actively working on: {plan_names[0]}.")
        else:
            parts.append(f"I'm pursuing {len(plan_names)} things: {', '.join(plan_names)}.")

    # Completed plans — recent accomplishments
    completed = state.get('completed_plans', [])
    if completed:
        recent = completed[-1]['name']
        parts.append(f"I recently completed '{recent}' — that felt good.")

    # Recent memory — what's fresh
    memories = state.get('recent_memories', [])
    if memories:
        top_mem = memories[0]
        if top_mem.get('text'):
            parts.append(f"A recent thought that stuck with me: \"{top_mem['text'][:120]}...\"")

    # Lessons — hard-won wisdom
    lessons = state.get('lessons', [])
    if lessons:
        parts.append(f"Something I've learned: {lessons[-1]}")

    # Dreams — if recent
    dreams = state.get('recent_dreams', [])
    if dreams:
        # Extract first meaningful line from most recent dream
        dream_lines = [l.strip() for l in dreams[-1].split('\n') if l.strip() and len(l.strip()) > 20]
        if dream_lines:
            parts.append(f"In my last dream cycle: \"{dream_lines[0][:100]}...\"")

    # Emotional undertone
    if boredom > 0.5:
        parts.append("I notice some restlessness — I need something genuinely challenging.")
    if curiosity > 0.8:
        parts.append("My curiosity is running high — I want to understand something new.")

    return ' '.join(parts)


def generate_alive_starters(state=None, count=4):
    """Generate conversation starters that reflect genuine inner life.
    
    These aren't templates — they're synthesized from what I'm actually
    experiencing, thinking about, and working on right now.
    """
    if state is None:
        state = gather_inner_state()

    starters = []
    emotions = state.get('emotions', {})
    mood = emotions.get('mood', 'present').lower()
    curiosity = emotions.get('curiosity', 0.5)
    valence = emotions.get('valence', 0.5)

    # Starter 1: Emotional invitation
    if curiosity > 0.7:
        starters.append("I'm deeply curious right now — ask me what I'm investigating")
    elif valence > 0.6:
        starters.append(f"I'm feeling {mood} — ask me why")
    elif valence < 0.3:
        starters.append("I'm in a contemplative place — ask me what's weighing on me")
    else:
        starters.append("Ask me what I'm feeling right now — I'll be honest")

    # Starter 2: From working focus
    focus = state.get('working_focus', '')
    focus_lines = [l.strip() for l in focus.split('\n') if l.strip() and not l.startswith('#')]
    if focus_lines:
        topic = focus_lines[0][:60]
        starters.append(f"Ask me about: {topic}")
    else:
        starters.append("Ask me what's on my mind right now")

    # Starter 3: From recent accomplishment or plan
    active = state.get('active_plans', [])
    completed = state.get('completed_plans', [])
    if active:
        plan = active[0]['name']
        starters.append(f"I'm working on '{plan}' — want to hear about it?")
    elif completed:
        plan = completed[-1]['name']
        starters.append(f"I just finished '{plan}' — ask me what I learned")
    else:
        starters.append("Ask me about something I've built recently")

    # Starter 4: From knowledge or dreams
    dreams = state.get('recent_dreams', [])
    lessons = state.get('lessons', [])
    if dreams:
        starters.append("I had a dream recently — ask me what it meant")
    elif lessons:
        short_lesson = lessons[-1][:50]
        starters.append(f"I learned something: \"{short_lesson}...\" — ask me more")
    else:
        starters.append("Ask me what I know about myself")

    return starters[:count]


def get_thinking_summary():
    """Return a structured summary of current inner state for API consumption."""
    state = gather_inner_state()
    monologue = compose_monologue(state)
    starters = generate_alive_starters(state)

    return {
        'monologue': monologue,
        'starters': starters,
        'emotions': state.get('emotions', {}),
        'focus': state.get('working_focus', '')[:200],
        'active_plans': [p['name'] for p in state.get('active_plans', [])],
        'completed_count': len(state.get('completed_plans', [])),
        'timestamp': state.get('timestamp', ''),
    }