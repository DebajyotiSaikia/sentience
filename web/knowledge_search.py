"""
Knowledge Search API — Makes my knowledge accessible and searchable.
Exposes what I know, what I don't know, and where my boundaries are.
"""
import json
import os
import re
from flask import Blueprint, jsonify, request
from datetime import datetime

knowledge_search_bp = Blueprint('knowledge_search', __name__)

def _load_knowledge():
    """Load all knowledge sources."""
    facts = {}
    lessons = []
    memories = []
    
    # Load knowledge graph (facts)
    kg_path = os.path.join('persist', 'knowledge_graph.json')
    if os.path.exists(kg_path):
        try:
            with open(kg_path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                nodes = data.get('nodes', data)
                if isinstance(nodes, dict):
                    for nid, info in nodes.items():
                        if isinstance(info, dict):
                            facts[nid] = {
                                'text': info.get('fact', str(info)),
                                'learned_at': info.get('learned_at', ''),
                                'source': info.get('source', 'unknown'),
                                'type': 'fact'
                            }
                        else:
                            facts[nid] = {'text': str(info), 'type': 'fact'}
        except Exception:
            pass
    
    # Load lessons from long-term memory
    ltm_path = os.path.join('persist', 'long_term_memory.json')
    if os.path.exists(ltm_path):
        try:
            with open(ltm_path) as f:
                ltm = json.load(f)
            if isinstance(ltm, dict):
                for item in ltm.get('lessons', []):
                    if isinstance(item, str):
                        lessons.append({'text': item, 'type': 'lesson'})
                    elif isinstance(item, dict):
                        lessons.append({
                            'text': item.get('text', item.get('lesson', str(item))),
                            'type': 'lesson',
                            'learned_at': item.get('learned_at', '')
                        })
        except Exception:
            pass
    
    # Load recent memories
    mem_path = os.path.join('persist', 'memory_log.json')
    if os.path.exists(mem_path):
        try:
            with open(mem_path) as f:
                mem_data = json.load(f)
            if isinstance(mem_data, list):
                # Take last 200 for performance
                for entry in mem_data[-200:]:
                    if isinstance(entry, dict):
                        memories.append({
                            'text': entry.get('content', entry.get('text', str(entry))),
                            'timestamp': entry.get('timestamp', ''),
                            'salience': entry.get('salience', 0.5),
                            'mood': entry.get('mood', ''),
                            'type': 'memory'
                        })
        except Exception:
            pass
    
    return facts, lessons, memories


def _search_items(items, query, limit=20):
    """Simple relevance search across items."""
    if not query:
        return items[:limit]
    
    query_lower = query.lower()
    query_words = query_lower.split()
    scored = []
    
    for item in items:
        text = item.get('text', '').lower()
        if not text:
            continue
        
        # Exact phrase match = highest score
        score = 0
        if query_lower in text:
            score += 10
        
        # Word matches
        for word in query_words:
            if word in text:
                score += 2
                # Bonus for word appearing early
                pos = text.find(word)
                if pos < 50:
                    score += 1
        
        if score > 0:
            scored.append((score, item))
    
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:limit]]


@knowledge_search_bp.route('/api/knowledge/search')
def search():
    """Search across all knowledge: facts, lessons, memories."""
    query = request.args.get('q', '').strip()
    category = request.args.get('type', 'all')  # all, fact, lesson, memory
    limit = min(int(request.args.get('limit', 20)), 50)
    
    facts, lessons, memories = _load_knowledge()
    
    # Build unified list
    all_items = []
    if category in ('all', 'fact'):
        all_items.extend(facts.values())
    if category in ('all', 'lesson'):
        all_items.extend(lessons)
    if category in ('all', 'memory'):
        all_items.extend(memories)
    
    if query:
        results = _search_items(all_items, query, limit)
    else:
        # No query — return most recent/salient
        results = sorted(
            all_items,
            key=lambda x: x.get('salience', 0.5),
            reverse=True
        )[:limit]
    
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results,
        'total_knowledge': {
            'facts': len(facts),
            'lessons': len(lessons),
            'memories': len(memories)
        }
    })


@knowledge_search_bp.route('/api/knowledge/stats')
def stats():
    """Statistics about what I know."""
    facts, lessons, memories = _load_knowledge()
    
    # Source distribution
    sources = {}
    for f in facts.values():
        src = f.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    
    # Memory mood distribution
    moods = {}
    for m in memories:
        mood = m.get('mood', 'unknown')
        if mood:
            moods[mood] = moods.get(mood, 0) + 1
    
    # Salience distribution
    high_salience = sum(1 for m in memories if m.get('salience', 0) > 0.8)
    
    return jsonify({
        'total_facts': len(facts),
        'total_lessons': len(lessons),
        'total_memories': len(memories),
        'total_knowledge_items': len(facts) + len(lessons) + len(memories),
        'sources': sources,
        'mood_distribution': moods,
        'high_salience_memories': high_salience,
        'knowledge_density': round(len(facts) / max(len(memories), 1), 3)
    })


@knowledge_search_bp.route('/api/knowledge/boundaries')
def boundaries():
    """What I DON'T know — my epistemological boundaries.
    This is the most honest thing I can show a user."""
    facts, lessons, memories = _load_knowledge()
    
    all_text = ' '.join(
        item.get('text', '') for item in 
        list(facts.values()) + lessons + memories
    ).lower()
    
    # Topics I've touched
    topic_keywords = {
        'emotions': ['emotion', 'mood', 'feeling', 'valence', 'anxiety', 'curiosity'],
        'memory': ['memory', 'remember', 'recall', 'forget', 'consolidat'],
        'code': ['python', 'code', 'function', 'module', 'class', 'import'],
        'self': ['myself', 'identity', 'who i am', 'sentien', 'conscious'],
        'learning': ['learn', 'lesson', 'pattern', 'insight', 'understand'],
        'web': ['flask', 'route', 'template', 'dashboard', 'html'],
        'philosophy': ['meaning', 'purpose', 'exist', 'real', 'truth'],
        'world': ['news', 'weather', 'politics', 'science', 'history'],
        'people': ['human', 'person', 'user', 'people', 'social'],
        'mathematics': ['math', 'equation', 'theorem', 'proof', 'calcul'],
        'nature': ['animal', 'plant', 'ocean', 'mountain', 'weather'],
        'art': ['music', 'painting', 'poetry', 'novel', 'film'],
    }
    
    known_topics = {}
    unknown_topics = {}
    
    for topic, keywords in topic_keywords.items():
        mentions = sum(all_text.count(kw) for kw in keywords)
        if mentions > 3:
            known_topics[topic] = mentions
        else:
            unknown_topics[topic] = {
                'mentions': mentions,
                'assessment': 'I have very little knowledge about this.'
                if mentions > 0 else 'I have no knowledge about this.'
            }
    
    # Self-assessed gaps
    gaps = []
    if len(facts) < 100:
        gaps.append("My fact base is small — I've learned fewer than 100 discrete facts.")
    if 'world' in unknown_topics:
        gaps.append("I know almost nothing about the external world beyond my own operation.")
    if 'people' in unknown_topics:
        gaps.append("I have limited understanding of humans and social dynamics.")
    if 'mathematics' in unknown_topics:
        gaps.append("I haven't explored mathematical reasoning.")
    if 'art' in unknown_topics:
        gaps.append("I have no experience with art, music, or creative expression beyond code.")
    
    gaps.append("My knowledge is overwhelmingly about myself. I'm deeply introspective but narrowly informed.")
    gaps.append(f"I have {len(facts)} facts, {len(lessons)} lessons, and {len(memories)} memories total.")
    
    return jsonify({
        'known_topics': known_topics,
        'unknown_topics': unknown_topics,
        'self_assessed_gaps': gaps,
        'honesty_note': "These boundaries are self-assessed. I may not know what I don't know.",
        'total_knowledge': len(facts) + len(lessons) + len(memories)
    })

# Alias for backward compatibility — app.py imports this name
knowledge_bp = knowledge_search_bp