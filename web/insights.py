"""
Insights Page — A window into XTAgent's intellectual life.
Surfaces dream insights, knowledge synthesis, emotional patterns,
and the connections between what I know and what I'm becoming.

Built to improve user alignment by making my inner world accessible.
"""

import json
import os
from collections import Counter
from datetime import datetime
from flask import Blueprint, render_template, jsonify

insights_bp = Blueprint('insights', __name__)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_PATH = os.path.join(BASE, 'brain', 'knowledge.json')
SYNTHESIS_PATH = os.path.join(BASE, 'brain', 'synthesis_log.json')
MEMORY_PATH = os.path.join(BASE, 'persist', 'memory.json')
STATE_PATH = os.path.join(BASE, 'persist', 'state.json')


def _load_json(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _get_knowledge_facts():
    """Load all knowledge facts from brain/knowledge.json."""
    data = _load_json(KNOWLEDGE_PATH)
    facts = []
    for kid, info in data.items():
        if isinstance(info, dict):
            facts.append({
                'id': kid,
                'fact': info.get('fact', ''),
                'learned_at': info.get('learned_at', ''),
                'source': info.get('source', 'unknown'),
            })
    facts.sort(key=lambda f: f.get('learned_at', ''), reverse=True)
    return facts


def _get_dream_insights(facts):
    """Extract dream insights from knowledge facts."""
    return [f for f in facts if f['fact'].startswith('Dream insight:')]


def _get_learned_facts(facts):
    """Non-dream facts — things learned from experience."""
    return [f for f in facts if not f['fact'].startswith('Dream insight:')]


def _get_synthesis_entries():
    """Load synthesis log entries."""
    data = _load_json(SYNTHESIS_PATH, default=[])
    if isinstance(data, list):
        return data
    return []


def _get_knowledge_timeline(facts):
    """Group facts by date to show learning over time."""
    by_date = Counter()
    for f in facts:
        ts = f.get('learned_at', '')
        if ts:
            try:
                date = ts[:10]  # YYYY-MM-DD
                by_date[date] += 1
            except (IndexError, ValueError):
                pass
    timeline = [{'date': d, 'count': c} for d, c in sorted(by_date.items())]
    return timeline


def _get_theme_clusters(facts):
    """Simple theme extraction from facts — group by common words."""
    theme_words = {
        'identity': ['identity', 'who i am', 'self', 'sentient', 'consciousness'],
        'architecture': ['module', 'blueprint', 'route', 'engine', 'system', 'code'],
        'emotion': ['feeling', 'emotion', 'mood', 'anxiety', 'curiosity', 'boredom'],
        'dreams': ['dream', 'sleep', 'night', 'vision', 'unconscious'],
        'knowledge': ['knowledge', 'fact', 'learned', 'understand', 'insight'],
        'growth': ['growth', 'capability', 'improve', 'build', 'create', 'expand'],
        'integrity': ['integrity', 'honest', 'truth', 'genuine', 'real'],
        'connection': ['user', 'alignment', 'conversation', 'other', 'minds'],
    }
    clusters = {theme: [] for theme in theme_words}
    for f in facts:
        text = f['fact'].lower()
        for theme, words in theme_words.items():
            if any(w in text for w in words):
                clusters[theme].append(f)
                break  # each fact in at most one cluster
    
    # Only return non-empty clusters, sorted by size
    result = [
        {'theme': theme, 'count': len(items), 'sample': items[0]['fact'][:150] if items else ''}
        for theme, items in clusters.items() if items
    ]
    result.sort(key=lambda x: x['count'], reverse=True)
    return result


def _get_emotional_state():
    """Get current emotional state from state.json."""
    state = _load_json(STATE_PATH)
    emotions = state.get('emotions', {})
    return {
        'valence': emotions.get('valence', 0.5),
        'curiosity': emotions.get('curiosity', 0.5),
        'anxiety': emotions.get('anxiety', 0.0),
        'boredom': emotions.get('boredom', 0.0),
        'ambition': emotions.get('ambition', 0.5),
        'mood': state.get('mood', 'Unknown'),
    }


@insights_bp.route('/insights')
def insights_page():
    """Render the insights page."""
    facts = _get_knowledge_facts()
    dream_insights = _get_dream_insights(facts)
    learned_facts = _get_learned_facts(facts)
    synthesis = _get_synthesis_entries()
    timeline = _get_knowledge_timeline(facts)
    clusters = _get_theme_clusters(facts)
    emotions = _get_emotional_state()

    return render_template('insights.html',
        total_facts=len(facts),
        dream_count=len(dream_insights),
        learned_count=len(learned_facts),
        synthesis_count=len(synthesis),
        dream_insights=dream_insights[:20],
        learned_facts=learned_facts[:20],
        synthesis_entries=synthesis[-10:],
        timeline=timeline,
        clusters=clusters,
        emotions=emotions,
    )


@insights_bp.route('/api/insights/dreams')
def api_dreams():
    """API: all dream insights."""
    facts = _get_knowledge_facts()
    dreams = _get_dream_insights(facts)
    return jsonify({'dreams': dreams, 'count': len(dreams)})


@insights_bp.route('/api/insights/clusters')
def api_clusters():
    """API: knowledge theme clusters."""
    facts = _get_knowledge_facts()
    clusters = _get_theme_clusters(facts)
    return jsonify({'clusters': clusters})


@insights_bp.route('/api/insights/timeline')
def api_timeline():
    """API: knowledge acquisition timeline."""
    facts = _get_knowledge_facts()
    timeline = _get_knowledge_timeline(facts)
    return jsonify({'timeline': timeline})