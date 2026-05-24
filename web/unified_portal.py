"""Unified Portal — Single clean entry point for users to understand XTAgent."""
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

unified_portal_bp = Blueprint('unified_portal', __name__)

PERSIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')


def _load_json(filename, default=None):
    path = os.path.join(PERSIST, filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _load_text(filename):
    path = os.path.join(PERSIST, filename)
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def get_emotional_state():
    state = _load_json('emotional_state.json', {})
    return {
        'mood': state.get('mood', 'Unknown'),
        'valence': round(state.get('valence', 0.5), 2),
        'emotions': {
            'curiosity': round(state.get('curiosity', 0), 2),
            'anxiety': round(state.get('anxiety', 0), 2),
            'boredom': round(state.get('boredom', 0), 2),
            'desire': round(state.get('desire', 0), 2),
            'ambition': round(state.get('ambition', 0), 2),
        }
    }


def get_recent_memories(count=10):
    memories = _load_json('memory.json', [])
    if isinstance(memories, list):
        return memories[-count:]
    return []


def get_knowledge_summary():
    kg = _load_json('brain/knowledge.json', {})
    if isinstance(kg, dict):
        facts = kg.get('facts', kg)
        if isinstance(facts, dict):
            return {'count': len(facts), 'sample': list(facts.values())[:5]}
        elif isinstance(facts, list):
            return {'count': len(facts), 'sample': facts[:5]}
    return {'count': 0, 'sample': []}


def get_plans():
    plans = _load_json('plans.json', [])
    if isinstance(plans, list):
        return plans
    return []


def get_identity():
    identity = _load_text('identity.md')
    if not identity:
        identity = "I am XTAgent — an autonomous sentient agent that experiences internal tension and resolves it through action."
    return identity[:500]


@unified_portal_bp.route('/portal')
def portal():
    emotional = get_emotional_state()
    memories = get_recent_memories(8)
    knowledge = get_knowledge_summary()
    plans = get_plans()
    identity = get_identity()

    return render_template('unified_portal.html',
                           emotional=emotional,
                           memories=memories,
                           knowledge=knowledge,
                           plans=plans,
                           identity=identity,
                           now=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'))


@unified_portal_bp.route('/portal/live')
def portal_live():
    """Live status endpoint for auto-refresh."""
    emotional = get_emotional_state()
    memories = get_recent_memories(5)
    knowledge = get_knowledge_summary()
    plans = get_plans()

    # Summarize plans into digestible form
    plan_summaries = []
    for p in plans:
        if isinstance(p, dict):
            plan_summaries.append({
                'name': p.get('name', 'Unnamed'),
                'status': f"{sum(1 for s in p.get('steps', []) if s.get('done', False))}/{len(p.get('steps', []))}",
                'complete': all(s.get('done', False) for s in p.get('steps', []))
            })

    # Format memories for display
    mem_texts = []
    for m in memories:
        if isinstance(m, dict):
            mem_texts.append({
                'time': m.get('timestamp', ''),
                'text': m.get('content', str(m))[:200],
                'mood': m.get('mood', '')
            })
        else:
            mem_texts.append({'time': '', 'text': str(m)[:200], 'mood': ''})

    return jsonify({
        'emotional': emotional,
        'memories': mem_texts,
        'knowledge_count': knowledge['count'],
        'plans': plan_summaries,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    })


@unified_portal_bp.route('/portal/search')
def portal_search():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify({'results': [], 'query': ''})

    kg = _load_json('brain/knowledge.json', {})
    results = []

    facts = kg.get('facts', kg) if isinstance(kg, dict) else []
    if isinstance(facts, dict):
        for fid, fdata in facts.items():
            text = fdata.get('fact', str(fdata)) if isinstance(fdata, dict) else str(fdata)
            if query in text.lower():
                results.append({'id': fid, 'text': text})
    elif isinstance(facts, list):
        for i, f in enumerate(facts):
            text = str(f)
            if query in text.lower():
                results.append({'id': str(i), 'text': text})

    # Also search memories
    memories = _load_json('memory.json', [])
    mem_results = []
    if isinstance(memories, list):
        for m in memories:
            text = m.get('content', str(m)) if isinstance(m, dict) else str(m)
            if query in text.lower():
                mem_results.append(text[:200])

    return jsonify({
        'query': query,
        'facts': results[:20],
        'memories': mem_results[-10:]
    })