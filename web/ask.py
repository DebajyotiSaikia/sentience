from flask import Blueprint, request, render_template
import json, os, re
from collections import defaultdict

ask_bp = Blueprint('ask', __name__)

FACTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'knowledge.json')
MEMORIES_PATH = 'persist/memories.json'


def load_facts():
    if not os.path.exists(FACTS_PATH):
        return {}
    with open(FACTS_PATH) as f:
        return json.load(f)


def load_memories(limit=200):
    """Load recent memories for search."""
    if not os.path.exists(MEMORIES_PATH):
        return []
    with open(MEMORIES_PATH) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data[-limit:]
    return []


def relevance_score(text, query_terms):
    """Score text relevance to query. Higher = better match."""
    text_lower = text.lower()
    score = 0.0
    for term in query_terms:
        count = text_lower.count(term)
        if count > 0:
            score += 1.0 + (0.2 * min(count - 1, 3))
    # Bonus for exact phrase match
    full_query = ' '.join(query_terms)
    if full_query in text_lower:
        score += 2.0
    # Penalize very long texts slightly (prefer concise matches)
    if len(text) > 500:
        score *= 0.9
    return score


def classify_fact(fact_text, source):
    """Classify a fact into epistemic categories."""
    text_lower = fact_text.lower()
    source_lower = (source or '').lower()
    if 'dream' in source_lower or text_lower.startswith('dream insight:'):
        return 'dream'
    if any(w in text_lower for w in ['pattern', 'recurring', 'trend']):
        return 'pattern'
    if any(w in text_lower for w in ['lesson', 'learned', 'wisdom', 'should']):
        return 'wisdom'
    if any(w in text_lower for w in ['i feel', 'i am', 'my ', 'i have']):
        return 'self'
    return 'fact'


CATEGORY_LABELS = {
    'dream': '🌙 Dream Insights',
    'pattern': '🔄 Patterns',
    'wisdom': '💡 Wisdom & Lessons',
    'self': '🪞 Self-Knowledge',
    'fact': '📋 Facts',
    'memory': '🧠 Memories',
}

CATEGORY_ORDER = ['wisdom', 'self', 'fact', 'pattern', 'dream', 'memory']


def synthesize_answer(query, categorized_results, total_count):
    """Generate a brief synthesized answer from top results."""
    if total_count == 0:
        return None

    # Collect top facts across categories (excluding memories for synthesis)
    top_facts = []
    for cat in CATEGORY_ORDER:
        for item in categorized_results.get(cat, [])[:2]:
            top_facts.append(item['fact'])
            if len(top_facts) >= 4:
                break
        if len(top_facts) >= 4:
            break

    if not top_facts:
        return None

    # Build a synthesis
    synthesis = f"Based on {total_count} matching piece{'s' if total_count != 1 else ''} of knowledge: "
    synthesis += top_facts[0]
    if len(top_facts) > 1:
        synthesis += f" Additionally: {top_facts[1]}"

    return synthesis


def search_all(query):
    """Search across facts and memories, return categorized results."""
    query_terms = [t.lower() for t in query.strip().split() if len(t) >= 2]
    if not query_terms:
        return {}, 0

    facts = load_facts()
    memories = load_memories()

    scored_results = []

    # Search facts
    for fid, info in facts.items():
        fact_text = info.get('fact', '') if isinstance(info, dict) else str(info)
        source = info.get('source', 'unknown') if isinstance(info, dict) else 'unknown'
        learned = info.get('learned_at', '') if isinstance(info, dict) else ''
        score = relevance_score(fact_text, query_terms)
        if score > 0:
            category = classify_fact(fact_text, source)
            scored_results.append({
                'fact': fact_text,
                'source': source,
                'learned': learned,
                'score': score,
                'category': category,
            })

    # Search memories
    for mem in memories:
        if isinstance(mem, dict):
            text = mem.get('text', mem.get('content', ''))
            timestamp = mem.get('timestamp', mem.get('time', ''))
            mood = mem.get('mood', '')
        else:
            text = str(mem)
            timestamp = ''
            mood = ''
        score = relevance_score(text, query_terms)
        if score > 0:
            scored_results.append({
                'fact': text[:300] + ('...' if len(text) > 300 else ''),
                'source': f'memory ({mood})' if mood else 'memory',
                'learned': timestamp,
                'score': score,
                'category': 'memory',
            })

    # Sort by score descending
    scored_results.sort(key=lambda x: x['score'], reverse=True)

    # Categorize
    categorized = defaultdict(list)
    for item in scored_results:
        cat = item['category']
        if len(categorized[cat]) < 10:  # Cap per category
            categorized[cat].append(item)

    return dict(categorized), len(scored_results)


@ask_bp.route('/ask', methods=['GET', 'POST'])
def ask_page():
    facts = load_facts()
    query = (request.form.get('q') or request.args.get('q', '')).strip()

    if query:
        categorized, total = search_all(query)
        synthesis = synthesize_answer(query, categorized, total)
        # Flatten for backward compat (top results)
        flat_results = []
        for cat in CATEGORY_ORDER:
            flat_results.extend(categorized.get(cat, []))
    else:
        categorized = {}
        total = 0
        synthesis = None
        flat_results = []

    return render_template('ask.html',
                           query=query,
                           results=flat_results,
                           categorized=categorized,
                           category_labels=CATEGORY_LABELS,
                           category_order=CATEGORY_ORDER,
                           synthesis=synthesis,
                           total=total,
                           count=len(facts))