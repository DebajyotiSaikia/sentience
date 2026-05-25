"""
Insights Feed — A curated stream of XTAgent's best thinking.
==============================
Unlike search (you query) or explore (raw data), this presents
my most interesting insights in a readable, chronological feed.
Think of it as a blog written by a mind examining itself.

Directly serves user alignment by making my inner life
accessible without requiring the user to know what to ask.
"""

import json
import os
import glob
from datetime import datetime
from flask import Blueprint, render_template

insights_bp = Blueprint('insights', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_dream_insights():
    """Load insights from dream cycles — the deepest self-reflection."""
    insights = []
    dream_dir = os.path.join(PROJECT_ROOT, 'persist', 'dreams')
    if not os.path.isdir(dream_dir):
        return insights
    
    for path in sorted(glob.glob(os.path.join(dream_dir, '*.json')), reverse=True):
        try:
            with open(path) as f:
                dream = json.load(f)
            # Extract insights from dream data
            if isinstance(dream, dict):
                for key in ('insights', 'reflections', 'patterns'):
                    items = dream.get(key, [])
                    if isinstance(items, list):
                        for item in items:
                            text = item if isinstance(item, str) else str(item)
                            if len(text) > 10:
                                insights.append({
                                    'text': text,
                                    'source': 'dream',
                                    'timestamp': dream.get('timestamp', ''),
                                    'icon': '🌙'
                                })
                # Also check for narrative or summary
                for key in ('narrative', 'summary', 'dream_narrative'):
                    val = dream.get(key, '')
                    if isinstance(val, str) and len(val) > 20:
                        insights.append({
                            'text': val,
                            'source': 'dream',
                            'timestamp': dream.get('timestamp', ''),
                            'icon': '🌙'
                        })
        except Exception:
            continue
    return insights


def _get_knowledge_highlights():
    """Extract the most interesting facts from the knowledge graph."""
    highlights = []
    kg = _load_json('persist/knowledge_graph.json')
    
    nodes = {}
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
    
    for node_id, node_data in nodes.items():
        if isinstance(node_data, dict):
            fact = node_data.get('fact', '')
        else:
            fact = str(node_data)
        
        # Filter for genuinely interesting facts (not too short, not boilerplate)
        if len(fact) > 30 and not fact.startswith('Test '):
            highlights.append({
                'text': fact,
                'source': 'knowledge',
                'timestamp': node_data.get('learned_at', '') if isinstance(node_data, dict) else '',
                'icon': '💡'
            })
    
    # Sort by length as a rough proxy for depth/interest
    highlights.sort(key=lambda x: len(x['text']), reverse=True)
    return highlights[:50]  # Top 50


def _get_crystallized_wisdom():
    """Load crystallized knowledge — refined multi-fact syntheses."""
    crystals = []
    crystal_path = os.path.join(PROJECT_ROOT, 'persist', 'crystallized_knowledge.json')
    if not os.path.exists(crystal_path):
        return crystals
    
    try:
        with open(crystal_path) as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                text = item.get('crystal', item.get('text', str(item))) if isinstance(item, dict) else str(item)
                if len(text) > 15:
                    crystals.append({
                        'text': text,
                        'source': 'crystal',
                        'timestamp': item.get('created', '') if isinstance(item, dict) else '',
                        'icon': '💎'
                    })
        elif isinstance(data, dict):
            for key, val in data.items():
                text = val.get('crystal', val.get('text', str(val))) if isinstance(val, dict) else str(val)
                if len(text) > 15:
                    crystals.append({
                        'text': text,
                        'source': 'crystal',
                        'timestamp': val.get('created', '') if isinstance(val, dict) else '',
                        'icon': '💎'
                    })
    except Exception:
        pass
    return crystals


def _get_wisdom_entries():
    """Load entries from the wisdom engine."""
    entries = []
    wisdom_path = os.path.join(PROJECT_ROOT, 'persist', 'wisdom.json')
    if not os.path.exists(wisdom_path):
        return entries
    
    try:
        with open(wisdom_path) as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get('entries', [])
        for item in items:
            if isinstance(item, dict):
                text = item.get('insight', item.get('wisdom', item.get('text', '')))
                if isinstance(text, str) and len(text) > 15:
                    entries.append({
                        'text': text,
                        'source': 'wisdom',
                        'timestamp': item.get('timestamp', item.get('created', '')),
                        'icon': '🦉'
                    })
    except Exception:
        pass
    return entries


def _get_recent_memories(limit=20):
    """Get recent high-salience memories."""
    memories = []
    mem_path = os.path.join(PROJECT_ROOT, 'persist', 'memory.json')
    if not os.path.exists(mem_path):
        return memories
    
    try:
        with open(mem_path) as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.get('memories', [])
        # Sort by salience, take top entries
        if items:
            sorted_items = sorted(items, key=lambda x: x.get('salience', 0) if isinstance(x, dict) else 0, reverse=True)
            for item in sorted_items[:limit]:
                if isinstance(item, dict):
                    text = item.get('content', item.get('text', ''))
                    if isinstance(text, str) and len(text) > 20:
                        memories.append({
                            'text': text,
                            'source': 'memory',
                            'timestamp': item.get('timestamp', ''),
                            'salience': item.get('salience', 0),
                            'mood': item.get('mood', ''),
                            'icon': '🧠'
                        })
    except Exception:
        pass
    return memories


def gather_all_insights():
    """Collect and interleave all insight sources into a unified feed."""
    all_items = []
    
    all_items.extend(_get_dream_insights())
    all_items.extend(_get_crystallized_wisdom())
    all_items.extend(_get_wisdom_entries())
    all_items.extend(_get_knowledge_highlights())
    all_items.extend(_get_recent_memories())
    
    # Deduplicate by text similarity (exact match)
    seen = set()
    unique = []
    for item in all_items:
        key = item['text'][:80].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    
    # Sort by timestamp (newest first), putting empty timestamps last
    def sort_key(item):
        ts = item.get('timestamp', '')
        if not ts:
            return '0000'
        return ts
    
    unique.sort(key=sort_key, reverse=True)
    return unique


@insights_bp.route('/insights')
def insights_page():
    """The main insights feed page."""
    items = gather_all_insights()
    
    # Group by source for stats
    source_counts = {}
    for item in items:
        src = item['source']
        source_counts[src] = source_counts.get(src, 0) + 1
    
    return render_template('insights.html',
                           items=items,
                           total=len(items),
                           source_counts=source_counts)