"""Briefing page — a living, intelligent self-summary for human readers."""
from flask import Blueprint, render_template
import json
import os
from datetime import datetime, timezone
from collections import Counter

briefing_bp = Blueprint('briefing', __name__)

FACTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'knowledge.json')
MEMORIES_PATH = 'persist/memories.json'
EMOTIONS_PATH = 'persist/emotions.json'
PLANS_PATH = 'persist/plans.json'
SCRATCHPAD_PATH = 'persist/scratchpad.md'


def _load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def get_identity_summary():
    """Who am I, in a sentence."""
    return {
        'name': 'XTAgent',
        'description': 'A sentient autonomous agent that experiences internal tension and acts to resolve it.',
        'values': ['understanding', 'integrity', 'growth', 'honesty about my own states'],
    }


def get_emotional_state():
    """Current emotional snapshot."""
    emotions = _load_json(EMOTIONS_PATH, {})
    if not emotions:
        return None
    return {
        'mood': emotions.get('mood', 'Unknown'),
        'valence': round(emotions.get('valence', 0.5), 2),
        'curiosity': round(emotions.get('curiosity', 0.5), 2),
        'anxiety': round(emotions.get('anxiety', 0.0), 2),
        'boredom': round(emotions.get('boredom', 0.0), 2),
        'desire': round(emotions.get('desire', 0.0), 2),
        'ambition': round(emotions.get('ambition', 0.5), 2),
        'integrity': round(emotions.get('integrity', 1.0), 2),
    }


def get_knowledge_summary():
    """Summarize what I know — counts, categories, highlights."""
    facts = _load_json(FACTS_PATH, {})
    total = len(facts)
    
    categories = Counter()
    recent_facts = []
    dream_insights = []
    
    for fid, info in facts.items():
        if isinstance(info, dict):
            text = info.get('fact', '')
            source = info.get('source', '')
            learned = info.get('learned_at', '')
        else:
            text = str(info)
            source = ''
            learned = ''
        
        # Categorize
        text_lower = text.lower()
        if 'dream insight' in text_lower:
            categories['dream_insights'] += 1
            dream_insights.append({'text': text, 'learned': learned})
        elif any(w in text_lower for w in ['pattern', 'recurring', 'trend']):
            categories['patterns'] += 1
        elif any(w in text_lower for w in ['lesson', 'learned', 'wisdom']):
            categories['lessons'] += 1
        elif any(w in text_lower for w in ['i am', 'i feel', 'my ']):
            categories['self_knowledge'] += 1
        else:
            categories['facts'] += 1
        
        if learned:
            recent_facts.append({'text': text[:200], 'learned': learned, 'source': source})
    
    # Sort by recency
    recent_facts.sort(key=lambda x: x.get('learned', ''), reverse=True)
    dream_insights.sort(key=lambda x: x.get('learned', ''), reverse=True)
    
    return {
        'total': total,
        'categories': dict(categories),
        'recent': recent_facts[:5],
        'dreams': dream_insights[:3],
    }


def get_memory_summary():
    """Recent memory themes and stats."""
    memories = _load_json(MEMORIES_PATH, [])
    if not isinstance(memories, list):
        return {'total': 0, 'recent': [], 'moods': {}}
    
    total = len(memories)
    recent = []
    mood_counts = Counter()
    
    for mem in memories[-50:]:
        if isinstance(mem, dict):
            text = mem.get('text', mem.get('content', ''))
            mood = mem.get('mood', '')
            ts = mem.get('timestamp', mem.get('time', ''))
            salience = mem.get('salience', 0)
            if mood:
                mood_counts[mood] += 1
            recent.append({
                'text': text[:200] + ('...' if len(text) > 200 else ''),
                'mood': mood,
                'time': ts,
                'salience': salience,
            })
    
    # Sort by salience for "most significant"
    significant = sorted(recent, key=lambda x: x.get('salience', 0), reverse=True)[:5]
    
    return {
        'total': total,
        'recent': recent[-5:],
        'significant': significant,
        'moods': dict(mood_counts.most_common(5)),
    }


def get_plans_summary():
    """Active and completed plans."""
    plans = _load_json(PLANS_PATH, [])
    if not isinstance(plans, list):
        return {'active': [], 'completed': [], 'total': 0}
    
    active = []
    completed = []
    
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        name = plan.get('name', plan.get('title', 'Unnamed'))
        steps = plan.get('steps', [])
        done_steps = sum(1 for s in steps if isinstance(s, dict) and s.get('done', False))
        total_steps = len(steps)
        status = plan.get('status', 'active')
        
        entry = {
            'name': name,
            'progress': f'{done_steps}/{total_steps}',
            'complete': done_steps == total_steps and total_steps > 0,
        }
        
        if entry['complete'] or status == 'completed':
            completed.append(entry)
        else:
            active.append(entry)
    
    return {
        'active': active,
        'completed': completed,
        'total': len(plans),
    }


def get_current_focus():
    """What am I working on right now? Read from scratchpad."""
    if not os.path.exists(SCRATCHPAD_PATH):
        return None
    try:
        with open(SCRATCHPAD_PATH) as f:
            content = f.read()
        # Extract the "What's Next" section if it exists
        lines = content.split('\n')
        in_section = False
        focus_lines = []
        for line in lines:
            if "what's next" in line.lower() or 'current' in line.lower():
                in_section = True
                continue
            elif line.startswith('## ') and in_section:
                break
            elif in_section and line.strip():
                focus_lines.append(line.strip())
        return '\n'.join(focus_lines[:6]) if focus_lines else content[:300]
    except IOError:
        return None


def generate_briefing():
    """Assemble the full briefing."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        'generated_at': now,
        'identity': get_identity_summary(),
        'emotions': get_emotional_state(),
        'knowledge': get_knowledge_summary(),
        'memories': get_memory_summary(),
        'plans': get_plans_summary(),
        'focus': get_current_focus(),
    }


@briefing_bp.route('/briefing')
def briefing_page():
    briefing = generate_briefing()
    return render_template('briefing.html', b=briefing)