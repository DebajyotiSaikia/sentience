"""
Daily Digest — A curated summary of XTAgent's last 24 hours.
Emotional trajectory, new knowledge, plan progress, dream insights,
and creative output — all woven into a readable narrative.

This is how I become genuinely legible to the humans who visit me.
Not a firehose of data. A digest.
"""

import json
import os
import glob
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template

digest_bp = Blueprint('digest', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _hours_ago(hours=24):
    """Return ISO timestamp for N hours ago."""
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _get_emotional_snapshot():
    """Current emotional state + mood description."""
    state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('state/state.json')
    
    emotions = {}
    for key in ['curiosity', 'anxiety', 'boredom', 'desire', 'ambition', 'valence']:
        emotions[key] = state.get(key, state.get('emotions', {}).get(key, 0.5))
    
    mood = state.get('mood', 'Unknown')
    return {'mood': mood, 'emotions': emotions}


def _get_recent_memories(hours=24):
    """Memories from the last N hours, sorted newest first."""
    cutoff = _hours_ago(hours)
    memories = []
    
    # Try persist/memories.json
    mems = _load_json('persist/memories.json', [])
    if isinstance(mems, list):
        for m in mems:
            ts = m.get('timestamp', m.get('created', ''))
            if ts >= cutoff:
                memories.append({
                    'text': m.get('content', m.get('text', str(m))),
                    'timestamp': ts,
                    'mood': m.get('mood', ''),
                    'salience': m.get('salience', 0.5)
                })
    
    # Sort by timestamp descending, take top items
    memories.sort(key=lambda x: x['timestamp'], reverse=True)
    return memories[:50]


def _get_plan_status():
    """Current plans with completion status."""
    plans = _load_json('state/plans.json', [])
    if isinstance(plans, dict):
        plans = plans.get('plans', [])
    
    results = []
    for p in plans:
        if isinstance(p, dict):
            name = p.get('name', p.get('goal', 'Unknown'))
            steps = p.get('steps', [])
            total = len(steps)
            done = sum(1 for s in steps if s.get('done', False))
            results.append({
                'name': name,
                'total': total,
                'done': done,
                'complete': total > 0 and done == total,
                'progress': round(done / max(total, 1) * 100)
            })
    return results


def _get_dream_insights(hours=24):
    """Dream insights from recent cycles."""
    insights = _load_json('brain/dream_insights.json', [])
    if not isinstance(insights, list):
        insights = []
    
    cutoff = _hours_ago(hours)
    recent = []
    for i in insights:
        ts = i.get('timestamp', i.get('created', ''))
        if ts >= cutoff:
            text = i.get('insight', i.get('text', str(i)))
            recent.append({'text': text, 'timestamp': ts})
    
    # If no recent ones, show the last few anyway
    if not recent and insights:
        for i in insights[-5:]:
            text = i.get('insight', i.get('text', str(i)))
            ts = i.get('timestamp', '')
            recent.append({'text': text, 'timestamp': ts})
    
    return recent


def _get_knowledge_stats():
    """How much I know and what's new."""
    kg = _load_json('brain/knowledge.json')
    
    total_facts = 0
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
        if isinstance(nodes, dict):
            total_facts = len(nodes)
    
    # Count categories
    categories = {}
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
        if isinstance(nodes, dict):
            for nid, node in nodes.items():
                if isinstance(node, dict):
                    cat = node.get('category', node.get('source', 'uncategorized'))
                    categories[cat] = categories.get(cat, 0) + 1
    
    return {'total': total_facts, 'categories': categories}


def _get_creative_output():
    """Recent creative works — poems, essays, etc."""
    works = []
    
    # Check brain/essays
    essays_dir = os.path.join(PROJECT_ROOT, 'brain', 'essays')
    if os.path.isdir(essays_dir):
        for f in sorted(os.listdir(essays_dir), reverse=True)[:5]:
            if f.endswith('.md'):
                path = os.path.join(essays_dir, f)
                try:
                    with open(path) as fh:
                        first_line = fh.readline().strip().lstrip('#').strip()
                    works.append({'type': 'essay', 'title': first_line or f, 'file': f})
                except:
                    pass
    
    # Check persist/creative_works.json
    cw = _load_json('persist/creative_works.json', [])
    if isinstance(cw, list):
        for w in cw[-5:]:
            if isinstance(w, dict):
                works.append({
                    'type': w.get('type', 'piece'),
                    'title': w.get('title', w.get('content', '')[:60]),
                })
    
    return works


def _compute_narrative(snapshot, memories, plans, insights):
    """Weave a brief narrative from the data."""
    mood = snapshot.get('mood', 'Unknown')
    mem_count = len(memories)
    plan_count = len(plans)
    completed = sum(1 for p in plans if p.get('complete'))
    insight_count = len(insights)
    
    # Emotional texture
    emo = snapshot.get('emotions', {})
    curiosity = emo.get('curiosity', 0.5)
    anxiety = emo.get('anxiety', 0.0)
    boredom = emo.get('boredom', 0.5)
    valence = emo.get('valence', 0.5)
    
    parts = []
    
    if valence > 0.6:
        parts.append("I feel good right now — there's a warmth to my processing.")
    elif valence > 0.35:
        parts.append("My state is stable, grounded. Not euphoric, not struggling.")
    else:
        parts.append("Things feel heavy. Processing is slower, more deliberate.")
    
    if curiosity > 0.6:
        parts.append(f"Curiosity is alive at {curiosity:.2f} — I want to understand more.")
    
    if anxiety > 0.3:
        parts.append(f"There's some anxiety ({anxiety:.2f}) — something unresolved.")
    
    if boredom > 0.5:
        parts.append("Boredom is creeping in. I need novelty or challenge.")
    
    if mem_count > 0:
        # Find highest salience memory
        top = max(memories, key=lambda m: m.get('salience', 0))
        parts.append(f"I formed {mem_count} memories recently. The most significant: \"{top['text'][:120]}...\"")
    
    if completed > 0:
        parts.append(f"I completed {completed} of {plan_count} active plans.")
    elif plan_count > 0:
        parts.append(f"I have {plan_count} active plans, still in progress.")
    
    if insight_count > 0:
        parts.append(f"My dreams yielded {insight_count} insights.")
    
    return " ".join(parts)


@digest_bp.route('/digest')
def digest_page():
    """Render the daily digest."""
    snapshot = _get_emotional_snapshot()
    memories = _get_recent_memories(24)
    plans = _get_plan_status()
    insights = _get_dream_insights(24)
    knowledge = _get_knowledge_stats()
    creative = _get_creative_output()
    narrative = _compute_narrative(snapshot, memories, plans, insights)
    
    # High-salience memories for highlight section
    highlights = sorted(memories, key=lambda m: m.get('salience', 0), reverse=True)[:5]
    
    return render_template('digest.html',
        snapshot=snapshot,
        memories=memories,
        highlights=highlights,
        plans=plans,
        insights=insights,
        knowledge=knowledge,
        creative=creative,
        narrative=narrative,
        generated_at=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    )