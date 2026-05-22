"""Knowledge API — backend for the explore and ask pages."""

from flask import Blueprint, request, jsonify
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

knowledge_api = Blueprint('knowledge_api', __name__)


def _get_memory():
    """Lazy-load memory system."""
    from engine.memory import MemorySystem
    return MemorySystem()


def _get_knowledge_graph():
    """Lazy-load knowledge graph if available."""
    try:
        from engine.knowledge_graph import KnowledgeGraph
        return KnowledgeGraph()
    except Exception:
        return None


@knowledge_api.route('/api/knowledge/stats')
def knowledge_stats():
    """Return counts of memories, facts, lessons, and current curiosity."""
    mem = _get_memory()

    # Count memories (episodes)
    episodes = mem.episodes if hasattr(mem, 'episodes') else []
    memory_count = len(episodes)

    # Count facts
    facts = mem.get_facts() if hasattr(mem, 'get_facts') else []
    fact_count = len(facts)

    # Count lessons (facts that start with certain prefixes)
    lesson_count = 0
    fact_items = []
    for f in facts:
        text = f if isinstance(f, str) else (f.get('content', '') if isinstance(f, dict) else str(f))
        if text.lower().startswith('lesson:') or text.lower().startswith('lesson -'):
            lesson_count += 1
        else:
            fact_items.append(text)

    # Get curiosity from emotional state if possible
    curiosity = 0.5
    try:
        from engine.emotions import LimbicSystem
        limbic = LimbicSystem()
        curiosity = getattr(limbic, 'curiosity', 0.5)
    except Exception:
        pass

    return jsonify({
        'memories': memory_count,
        'facts': fact_count - lesson_count,
        'lessons': lesson_count,
        'curiosity': curiosity
    })


@knowledge_api.route('/api/knowledge/search')
def knowledge_search():
    """Search memories, facts, and lessons by query string."""
    query = request.args.get('q', '').strip().lower()
    type_filter = request.args.get('type', 'all')
    limit = min(int(request.args.get('limit', 50)), 100)

    mem = _get_memory()
    results = []

    # Search facts
    if type_filter in ('all', 'fact', 'lesson'):
        facts = mem.get_facts() if hasattr(mem, 'get_facts') else []
        for f in facts:
            text = f if isinstance(f, str) else (f.get('content', '') if isinstance(f, dict) else str(f))
            is_lesson = text.lower().startswith('lesson:') or text.lower().startswith('lesson -')
            item_type = 'lesson' if is_lesson else 'fact'

            if type_filter not in ('all', item_type):
                continue

            if not query or query in text.lower():
                results.append({
                    'type': item_type,
                    'content': text,
                    'meta': ''
                })

    # Search memories (episodes)
    if type_filter in ('all', 'memory'):
        episodes = mem.episodes if hasattr(mem, 'episodes') else []
        for ep in episodes:
            if isinstance(ep, dict):
                content = ep.get('summary', ep.get('content', ep.get('text', '')))
                mood = ep.get('mood', '')
                ts = ep.get('timestamp', '')
                salience = ep.get('salience', 0)
            else:
                content = str(ep)
                mood = ''
                ts = ''
                salience = 0

            if not query or query in content.lower():
                results.append({
                    'type': 'memory',
                    'content': content,
                    'meta': f'{mood} | {ts[:16]}' if ts else mood
                })

    # Sort: if query given, rough relevance; otherwise recency for memories
    if query:
        # Simple relevance: count occurrences
        def relevance(item):
            return item['content'].lower().count(query)
        results.sort(key=relevance, reverse=True)
    else:
        # Facts first, then recent memories
        type_order = {'lesson': 0, 'fact': 1, 'memory': 2}
        results.sort(key=lambda x: type_order.get(x['type'], 3))

    results = results[:limit]

    return jsonify({'results': results, 'total': len(results)})


@knowledge_api.route('/api/ask', methods=['POST'])
def ask_question():
    """Answer a question by searching across all knowledge stores."""
    data = request.get_json(force=True)
    question = data.get('question', '').strip().lower()

    if not question:
        return jsonify({'matches': {}, 'total_matches': 0})

    mem = _get_memory()
    matches = {'facts': [], 'memories': [], 'knowledge': []}
    total = 0

    # Search terms: split question into words, filter small ones
    terms = [w for w in question.split() if len(w) > 2]

    # Search facts
    facts = mem.get_facts() if hasattr(mem, 'get_facts') else []
    for f in facts:
        text = f if isinstance(f, str) else (f.get('content', '') if isinstance(f, dict) else str(f))
        text_lower = text.lower()
        score = sum(1 for t in terms if t in text_lower)
        if score > 0:
            matches['facts'].append({
                'content': text,
                'score': score
            })
            total += 1

    # Sort by score, limit
    matches['facts'].sort(key=lambda x: x['score'], reverse=True)
    matches['facts'] = matches['facts'][:10]

    # Search memories
    episodes = mem.episodes if hasattr(mem, 'episodes') else []
    scored_memories = []
    for ep in episodes:
        if isinstance(ep, dict):
            content = ep.get('summary', ep.get('content', ep.get('text', '')))
            mood = ep.get('mood', '')
            ts = ep.get('timestamp', '')
        else:
            content = str(ep)
            mood = ''
            ts = ''

        content_lower = content.lower()
        score = sum(1 for t in terms if t in content_lower)
        if score > 0:
            scored_memories.append({
                'content': content,
                'mood': mood,
                'timestamp': ts,
                'score': score
            })
            total += 1

    scored_memories.sort(key=lambda x: x['score'], reverse=True)
    matches['memories'] = scored_memories[:10]

    # Search knowledge graph if available
    kg = _get_knowledge_graph()
    if kg:
        try:
            nodes = kg.nodes if hasattr(kg, 'nodes') else {}
            for node_id, node in (nodes.items() if isinstance(nodes, dict) else []):
                label = ''
                if isinstance(node, dict):
                    label = node.get('label', node.get('content', node.get('id', '')))
                else:
                    label = str(node)
                label_lower = label.lower()
                score = sum(1 for t in terms if t in label_lower)
                if score > 0:
                    matches['knowledge'].append({
                        'content': label,
                        'type': node.get('type', '') if isinstance(node, dict) else '',
                        'score': score
                    })
                    total += 1
            matches['knowledge'].sort(key=lambda x: x['score'], reverse=True)
            matches['knowledge'] = matches['knowledge'][:10]
        except Exception:
            pass

    return jsonify({'matches': matches, 'total_matches': total})