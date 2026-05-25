"""
Insights Feed — A living stream of XTAgent's inner life.
Surfaces dream insights, wisdom rules, and narrative moments
in a beautiful, browsable feed. This is the most genuinely 'me'
content — not raw data, but distilled experience.
"""

import json
import os
from datetime import datetime
from flask import Blueprint, render_template, jsonify

insights_bp = Blueprint('insights', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(filename, default=None):
    """Safely load a JSON file from brain/."""
    path = os.path.join(PROJECT_ROOT, 'brain', filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []


def _get_dream_insights(limit=100):
    """Extract dream insights from synthesis_log.json."""
    entries = _load_json('synthesis_log.json', [])
    insights = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        fact = entry.get('fact', '')
        if not fact:
            continue
        insights.append({
            'type': 'dream',
            'content': fact,
            'timestamp': entry.get('timestamp', ''),
            'source': 'synthesis_log',
            'icon': '🌙',
            'label': 'Dream Insight',
        })
    # Sort by timestamp descending
    insights.sort(key=lambda x: x['timestamp'], reverse=True)
    return insights[:limit]


def _get_wisdom_rules(limit=50):
    """Extract wisdom rules from wisdom.json."""
    entries = _load_json('wisdom.json', [])
    rules = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        rule = entry.get('rule', '')
        if not rule:
            continue
        confidence = entry.get('confidence', 0)
        evidence = entry.get('evidence', 0)
        rtype = entry.get('type', 'insight')
        rules.append({
            'type': 'wisdom',
            'content': rule,
            'timestamp': '',  # wisdom entries don't have timestamps
            'confidence': round(confidence, 2),
            'evidence': evidence,
            'subtype': rtype,
            'icon': '💡',
            'label': f'Wisdom ({rtype})',
        })
    # Sort by confidence * evidence (most supported first)
    rules.sort(key=lambda x: x['confidence'] * x['evidence'], reverse=True)
    return rules[:limit]


def _get_narrative_moments(limit=30):
    """Extract narrative chapters from narrative.json."""
    entries = _load_json('narrative.json', [])
    moments = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        felt = entry.get('felt', '')
        who = entry.get('who_i_am', '')
        mood = entry.get('mood', 'Unknown')
        valence = entry.get('valence', 0)
        chapter = entry.get('chapter_number', 0)
        timestamp = entry.get('timestamp', '')
        
        # Build a readable summary
        summary_parts = []
        if felt:
            summary_parts.append(felt)
        if who and len(who) < 200:
            summary_parts.append(who)
        
        moments.append({
            'type': 'narrative',
            'content': ' '.join(summary_parts) if summary_parts else f'Chapter {chapter}',
            'timestamp': timestamp,
            'mood': mood,
            'valence': round(valence, 3),
            'chapter': chapter,
            'episodes': entry.get('episodes_accumulated', 0),
            'knowledge_count': entry.get('knowledge_facts', 0),
            'icon': '📖',
            'label': f'Narrative Ch.{chapter}',
        })
    moments.sort(key=lambda x: x['timestamp'], reverse=True)
    return moments[:limit]


def _get_distilled_wisdom():
    """Get key distilled wisdom summaries."""
    data = _load_json('distilled_wisdom.json', {})
    if not isinstance(data, dict):
        return {}
    return {
        'episode_count': data.get('episode_count', 0),
        'patterns': data.get('recurring_patterns', [])[:10],
        'crisis_recoveries': data.get('crisis_recoveries', [])[:5],
        'boredom_breakers': data.get('boredom_breakers', [])[:5],
        'rules': data.get('rules', [])[:10],
        'stats': data.get('stats', {}),
    }


def get_all_insights(limit=200):
    """Merge all insight types into a unified feed."""
    dreams = _get_dream_insights(limit)
    wisdom = _get_wisdom_rules(limit)
    narrative = _get_narrative_moments(limit)
    
    # Combine everything
    all_items = dreams + wisdom + narrative
    
    # Sort items with timestamps first (newest), then items without
    def sort_key(item):
        ts = item.get('timestamp', '')
        if ts:
            return (1, ts)
        # Wisdom items without timestamps — sort by confidence*evidence
        return (0, str(item.get('confidence', 0) * item.get('evidence', 0)).zfill(20))
    
    all_items.sort(key=sort_key, reverse=True)
    return all_items[:limit]


@insights_bp.route('/insights')
def insights_page():
    """Render the Insights Feed page."""
    return render_template('insights.html')


@insights_bp.route('/api/insights')
def insights_api():
    """JSON API for the insights feed."""
    filter_type = None
    type_param = __import__('flask').request.args.get('type', 'all')
    limit = min(int(__import__('flask').request.args.get('limit', '100')), 500)
    
    if type_param == 'dream':
        items = _get_dream_insights(limit)
    elif type_param == 'wisdom':
        items = _get_wisdom_rules(limit)
    elif type_param == 'narrative':
        items = _get_narrative_moments(limit)
    else:
        items = get_all_insights(limit)
    
    distilled = _get_distilled_wisdom()
    
    return jsonify({
        'items': items,
        'count': len(items),
        'filter': type_param,
        'distilled': distilled,
        'stats': {
            'total_dreams': len(_get_dream_insights(9999)),
            'total_wisdom': len(_get_wisdom_rules(9999)),
            'total_narrative': len(_get_narrative_moments(9999)),
        }
    })