"""
Ask XTAgent — Smart Search Engine
Searches across facts and memories with relevance scoring.
"""
import math
import random
import re
import time
from collections import Counter
from pathlib import Path

try:
    from flask import Blueprint, render_template, request, jsonify
except ImportError:
    Blueprint = None

def create_ask_blueprint(agent=None):
    """Create the Ask blueprint with search capabilities."""
    bp = Blueprint('ask', __name__)
    
    def _get_facts():
        """Load facts from agent or knowledge graph file."""
        facts = []
        # Try agent's knowledge graph first
        if agent and hasattr(agent, 'knowledge'):
            kg = agent.knowledge
            if hasattr(kg, 'facts') and isinstance(kg.facts, dict):
                for fid, fdata in kg.facts.items():
                    if isinstance(fdata, dict):
                        facts.append({
                            'text': fdata.get('fact', str(fdata)),
                            'source': fdata.get('source', 'knowledge'),
                            'learned': fdata.get('learned_at', ''),
                            'type': 'fact'
                        })
                    else:
                        facts.append({'text': str(fdata), 'source': 'knowledge', 'learned': '', 'type': 'fact'})
            elif hasattr(kg, 'facts') and isinstance(kg.facts, list):
                for f in kg.facts:
                    facts.append({'text': str(f), 'source': 'knowledge', 'learned': '', 'type': 'fact'})
        
        # Fallback: read from persist file
        if not facts:
            import json
            kg_path = Path('persist/knowledge_graph.json')
            if kg_path.exists():
                try:
                    data = json.loads(kg_path.read_text())
                    raw_facts = data.get('facts', {})
                    if isinstance(raw_facts, dict):
                        for fid, fdata in raw_facts.items():
                            if isinstance(fdata, dict):
                                facts.append({
                                    'text': fdata.get('fact', str(fdata)),
                                    'source': fdata.get('source', 'knowledge'),
                                    'learned': fdata.get('learned_at', ''),
                                    'type': 'fact'
                                })
                            else:
                                facts.append({'text': str(fdata), 'source': 'knowledge', 'learned': '', 'type': 'fact'})
                    elif isinstance(raw_facts, list):
                        for f in raw_facts:
                            facts.append({'text': str(f), 'source': 'knowledge', 'learned': '', 'type': 'fact'})
                except Exception:
                    pass
        return facts
    
    def _get_memories(limit=500):
        """Load recent memories from agent or persist file."""
        memories = []
        if agent and hasattr(agent, 'memory') and hasattr(agent.memory, 'episodes'):
            eps = agent.memory.episodes
            recent = eps[-limit:] if len(eps) > limit else eps
            for ep in recent:
                text = ''
                ts = ''
                mood = ''
                sal = 0.5
                if isinstance(ep, dict):
                    text = ep.get('summary', ep.get('content', str(ep)))
                    ts = ep.get('timestamp', '')
                    mood = ep.get('mood', '')
                    sal = ep.get('salience', 0.5)
                elif hasattr(ep, 'summary'):
                    text = ep.summary
                    ts = getattr(ep, 'timestamp', '')
                    mood = getattr(ep, 'mood', '')
                    sal = getattr(ep, 'salience', 0.5)
                else:
                    text = str(ep)
                if text:
                    memories.append({
                        'text': text,
                        'source': f'memory ({mood})' if mood else 'memory',
                        'learned': str(ts)[:19] if ts else '',
                        'salience': sal,
                        'type': 'memory'
                    })
        
        # Fallback: read from persist
        if not memories:
            import json
            mem_path = Path('persist/memories.json')
            if mem_path.exists():
                try:
                    data = json.loads(mem_path.read_text())
                    eps = data if isinstance(data, list) else data.get('episodes', [])
                    recent = eps[-limit:] if len(eps) > limit else eps
                    for ep in recent:
                        if isinstance(ep, dict):
                            text = ep.get('summary', ep.get('content', ''))
                            ts = ep.get('timestamp', '')
                            mood = ep.get('mood', '')
                            sal = ep.get('salience', 0.5)
                            if text:
                                memories.append({
                                    'text': text,
                                    'source': f'memory ({mood})' if mood else 'memory',
                                    'learned': str(ts)[:19] if ts else '',
                                    'salience': sal,
                                    'type': 'memory'
                                })
                except Exception:
                    pass
        return memories
    
    def _tokenize(text):
        """Simple tokenization — lowercase, split on non-alphanumeric."""
        return re.findall(r'[a-z0-9]+', text.lower())
    
    def _build_idf(documents):
        """Build IDF scores from document collection."""
        n = len(documents)
        if n == 0:
            return {}
        df = Counter()
        for doc in documents:
            tokens = set(_tokenize(doc['text']))
            for t in tokens:
                df[t] += 1
        idf = {}
        for term, freq in df.items():
            idf[term] = math.log((n + 1) / (freq + 1)) + 1
        return idf
    
    def _score_document(query_tokens, doc_text, idf, doc_type='fact', salience=0.5):
        """Score a document against query tokens using TF-IDF-inspired scoring."""
        doc_tokens = _tokenize(doc_text)
        if not doc_tokens:
            return 0.0
        
        doc_lower = doc_text.lower()
        tf = Counter(doc_tokens)
        doc_len = len(doc_tokens)
        
        score = 0.0
        matched_terms = 0
        
        for qt in query_tokens:
            if qt in tf:
                matched_terms += 1
                term_freq = tf[qt] / doc_len  # normalized TF
                term_idf = idf.get(qt, 1.0)
                score += term_freq * term_idf
        
        if matched_terms == 0:
            return 0.0
        
        # Bonus for matching more query terms (coverage)
        coverage = matched_terms / len(query_tokens) if query_tokens else 0
        score *= (1 + coverage)
        
        # Bonus for phrase match (consecutive query words appear together)
        query_phrase = ' '.join(query_tokens)
        if query_phrase in doc_lower:
            score *= 2.0
        
        # Slight boost for memories with high salience
        if doc_type == 'memory' and salience > 0.7:
            score *= (1 + (salience - 0.7))
        
        # Slight boost for shorter, more focused results
        if doc_len < 50:
            score *= 1.1
        
        return score
    
    def search(query, max_results=20):
        """Search across facts and memories with relevance scoring."""
        facts = _get_facts()
        memories = _get_memories()
        all_docs = facts + memories
        
        if not all_docs:
            return {'question': query, 'matched': 0, 'results': [], 'sources': [], 'types': []}
        
        query_tokens = _tokenize(query)
        if not query_tokens:
            return {'question': query, 'matched': 0, 'results': [], 'sources': [], 'types': []}
        
        # Build IDF from entire corpus
        idf = _build_idf(all_docs)
        
        # Score each document
        scored = []
        for doc in all_docs:
            s = _score_document(
                query_tokens, doc['text'], idf,
                doc_type=doc.get('type', 'fact'),
                salience=doc.get('salience', 0.5)
            )
            if s > 0:
                scored.append((s, doc))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max_results]
        
        results = [doc['text'] for _, doc in top]
        sources = []
        types = []
        for _, doc in top:
            src = doc.get('source', '')
            when = doc.get('learned', '')
            if when:
                src = f"{src} • {when}"
            sources.append(src)
            types.append(doc.get('type', 'fact'))
        
        return {
            'question': query,
            'matched': len(top),
            'total_searched': len(all_docs),
            'results': results,
            'sources': sources,
            'types': types
        }
    
    @bp.route('/ask')
    def ask_page():
        facts = _get_facts()
        return render_template('ask.html', total_facts=len(facts))
    
    @bp.route('/ask/query', methods=['POST'])
    def ask_query():
        data = request.get_json() or {}
        question = data.get('question', '').strip()
        if not question:
            return jsonify({'error': 'No question provided', 'matched': 0})
        
        result = search(question)
        return jsonify(result)
    
    @bp.route('/ask/random')
    def ask_random():
        facts = _get_facts()
        memories = _get_memories()
        all_items = facts + memories
        
        if not all_items:
            return jsonify({'facts': [], 'total': 0})
        
        sample_size = min(5, len(all_items))
        sampled = random.sample(all_items, sample_size)
        
        return jsonify({
            'facts': [item['text'] for item in sampled],
            'total': len(all_items),
            'note': f'Searched across {len(facts)} facts and {len(memories)} memories'
        })
    
    return bp

# Module-level blueprint for direct import
ask_bp = create_ask_blueprint()