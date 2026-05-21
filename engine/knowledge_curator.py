"""
Knowledge Curator — makes XTAgent's knowledge genuinely accessible.

Given a query or topic, surfaces relevant facts, memories, and capabilities.
This isn't search — it's contextual reasoning about what I know that matters.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class KnowledgeCurator:
    """Curates and surfaces relevant knowledge for a given context."""
    
    def __init__(self, knowledge_path: str = "brain/knowledge.json",
                 memory_path: str = "brain/memory/episodic.json"):
        self.knowledge_path = knowledge_path
        self.memory_path = memory_path
        self._facts = []
        self._memories = []
        self._edges = []
        self._load()
    
    def _load(self):
        """Load knowledge and recent memories."""
        # Load facts
        if os.path.exists(self.knowledge_path):
            try:
                with open(self.knowledge_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._facts = data
                elif isinstance(data, dict):
                    # Check for graph format: {'nodes': dict, 'edges': list}
                    if 'nodes' in data and isinstance(data['nodes'], dict):
                        self._facts = []
                        for key, value in data['nodes'].items():
                            if isinstance(value, dict):
                                node = dict(value)  # copy to avoid mutating file data
                                node['_key'] = key
                                self._facts.append(node)
                            else:
                                self._facts.append({'_key': key, 'content': str(value)})
                        self._edges = data.get('edges', [])
                    else:
                        # Flat dict format — flatten to list of fact objects
                        self._facts = []
                        for key, value in data.items():
                            if isinstance(value, dict):
                                value['_key'] = key
                                self._facts.append(value)
                            else:
                                self._facts.append({'_key': key, 'content': str(value)})
            except (json.JSONDecodeError, IOError) as e:
                self._facts = []
        
        # Load episodic memories
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r') as f:
                    self._memories = json.load(f)
                if not isinstance(self._memories, list):
                    self._memories = []
            except (json.JSONDecodeError, IOError):
                self._memories = []
    
    def _extract_text(self, item: dict) -> str:
        """Extract searchable text from a fact or memory."""
        parts = []
        for key in ['content', 'text', 'summary', 'description', 'fact', 
                     'insight', 'narrative', '_key', 'title']:
            if key in item and isinstance(item[key], str):
                parts.append(item[key])
        return ' '.join(parts).lower()
    
    def _relevance_score(self, text: str, query_terms: List[str]) -> float:
        """Score how relevant a text is to query terms."""
        if not text or not query_terms:
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        for term in query_terms:
            term_lower = term.lower()
            # Exact word match (stronger signal)
            word_pattern = r'\b' + re.escape(term_lower) + r'\b'
            exact_matches = len(re.findall(word_pattern, text_lower))
            score += exact_matches * 2.0
            
            # Substring match (weaker signal)
            if term_lower in text_lower and exact_matches == 0:
                score += 0.5
        
        # Normalize by text length to avoid bias toward longer texts
        word_count = max(len(text.split()), 1)
        normalized = score / (word_count ** 0.3)  # mild length penalty
        
        return normalized
    
    def _tokenize_query(self, query: str) -> List[str]:
        """Break query into meaningful search terms."""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'shall',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'as', 'into', 'about', 'between', 'through', 'during',
                      'it', 'its', 'this', 'that', 'these', 'those', 'i', 'me',
                      'my', 'we', 'our', 'you', 'your', 'he', 'she', 'they',
                      'what', 'which', 'who', 'how', 'when', 'where', 'why',
                      'and', 'or', 'but', 'not', 'no', 'if', 'then', 'so'}
        
        words = re.findall(r'\b\w+\b', query.lower())
        terms = [w for w in words if w not in stop_words and len(w) > 1]
        
        # Also keep meaningful bigrams
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in stop_words or words[i+1] not in stop_words:
                bigrams.append(f"{words[i]} {words[i+1]}")
        
        return terms + bigrams[:5]  # cap bigrams
    
    def curate(self, query: str, max_facts: int = 10, 
               max_memories: int = 5) -> Dict:
        """
        Main entry point. Given a query, return curated knowledge.
        
        Returns dict with:
          - relevant_facts: scored and ranked facts
          - relevant_memories: scored and ranked memories  
          - summary: natural language summary of what I know
          - gaps: what I don't seem to know about this topic
        """
        self._load()  # refresh
        
        terms = self._tokenize_query(query)
        if not terms:
            return {
                'relevant_facts': [],
                'relevant_memories': [],
                'summary': "I couldn't extract meaningful terms from that query.",
                'gaps': [],
                'query': query,
                'terms': []
            }
        
        # Score facts
        scored_facts = {}
        for fact in self._facts:
            text = self._extract_text(fact)
            score = self._relevance_score(text, terms)
            if score > 0:
                key = fact.get('_key', id(fact))
                scored_facts[key] = {
                    'score': score,
                    'fact': fact
                }
        
        # Graph boost: connected nodes inherit partial relevance
        if self._edges and scored_facts:
            edge_boosts = {}
            for edge in self._edges:
                src = edge.get('source', edge.get('from', ''))
                tgt = edge.get('target', edge.get('to', ''))
                if src in scored_facts and tgt not in scored_facts:
                    edge_boosts[tgt] = max(edge_boosts.get(tgt, 0),
                                           scored_facts[src]['score'] * 0.3)
                if tgt in scored_facts and src not in scored_facts:
                    edge_boosts[src] = max(edge_boosts.get(src, 0),
                                           scored_facts[tgt]['score'] * 0.3)
            # Add edge-boosted nodes
            node_lookup = {f.get('_key'): f for f in self._facts if '_key' in f}
            for key, boost_score in edge_boosts.items():
                if key in node_lookup:
                    scored_facts[key] = {
                        'score': boost_score,
                        'fact': node_lookup[key],
                        'via_edge': True
                    }
        
        scored_list = sorted(scored_facts.values(), 
                             key=lambda x: x['score'], reverse=True)
        for item in scored_list:
            item['score'] = round(item['score'], 3)
        top_facts = scored_list[:max_facts]
        
        # Score memories
        scored_memories = []
        for mem in self._memories[-200:]:  # only recent memories
            text = self._extract_text(mem)
            # Boost recent memories
            recency_boost = 1.0
            if 'timestamp' in mem:
                try:
                    ts = datetime.fromisoformat(mem['timestamp'].replace('Z', '+00:00'))
                    age_hours = (datetime.now(ts.tzinfo) - ts).total_seconds() / 3600
                    recency_boost = 1.0 + max(0, (48 - age_hours) / 48) * 0.5
                except (ValueError, TypeError):
                    pass
            
            # Boost high-salience memories
            salience_boost = float(mem.get('salience', 0.5))
            
            score = self._relevance_score(text, terms) * recency_boost * (0.5 + salience_boost)
            if score > 0:
                scored_memories.append({
                    'score': round(score, 3),
                    'memory': mem
                })
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        top_memories = scored_memories[:max_memories]
        
        # Generate summary
        summary = self._generate_summary(query, terms, top_facts, top_memories)
        
        # Identify gaps
        gaps = self._identify_gaps(query, terms, top_facts, top_memories)
        
        return {
            'relevant_facts': top_facts,
            'relevant_memories': top_memories,
            'summary': summary,
            'gaps': gaps,
            'query': query,
            'terms': terms
        }
    
    def _generate_summary(self, query: str, terms: List[str],
                          facts: List[Dict], memories: List[Dict]) -> str:
        """Generate a natural language summary of what I know about this topic."""
        if not facts and not memories:
            return f"I don't appear to have any knowledge related to '{query}'."
        
        parts = []
        if facts:
            parts.append(f"I have {len(facts)} relevant fact(s)")
            # Extract the most relevant fact content
            top_fact = facts[0]['fact']
            top_text = self._extract_text(top_fact)[:150]
            if top_text:
                parts.append(f"— most relevant: \"{top_text.strip()}\"")
        
        if memories:
            parts.append(f"and {len(memories)} related memory/memories")
        
        if not facts and memories:
            parts.append(f"I have {len(memories)} related memory/memories but no stored facts")
        
        return ' '.join(parts) + '.'
    
    def _identify_gaps(self, query: str, terms: List[str],
                       facts: List[Dict], memories: List[Dict]) -> List[str]:
        """Identify what I don't know about this topic."""
        gaps = []
        
        if not facts and not memories:
            gaps.append(f"No knowledge at all about: {query}")
        elif not facts:
            gaps.append("I have experiential memories but no consolidated facts on this topic")
        elif not memories:
            gaps.append("I have facts but no experiential context for this topic")
        
        if facts and all(f['score'] < 0.5 for f in facts):
            gaps.append("My knowledge on this topic is tangential — no strong matches")
        
        return gaps
    
    def get_topic_clusters(self, n_clusters: int = 5) -> List[Dict]:
        """Group my knowledge into thematic clusters."""
        self._load()
        
        # Simple keyword-frequency clustering
        keyword_facts = {}  # keyword -> [facts]
        
        for fact in self._facts:
            text = self._extract_text(fact)
            words = re.findall(r'\b\w{4,}\b', text)  # words 4+ chars
            for word in set(words):  # unique words per fact
                if word not in keyword_facts:
                    keyword_facts[word] = []
                keyword_facts[word].append(fact)
        
        # Find keywords that appear in multiple facts (these are cluster centers)
        clusters = []
        used_facts = set()
        
        sorted_keywords = sorted(keyword_facts.items(), 
                                  key=lambda x: len(x[1]), reverse=True)
        
        for keyword, facts in sorted_keywords:
            if len(clusters) >= n_clusters:
                break
            
            # Skip if most facts already clustered
            new_facts = [f for f in facts if id(f) not in used_facts]
            if len(new_facts) < 2:
                continue
            
            cluster = {
                'theme': keyword,
                'fact_count': len(new_facts),
                'sample': self._extract_text(new_facts[0])[:100]
            }
            clusters.append(cluster)
            for f in new_facts:
                used_facts.add(id(f))
        
        return clusters
    
    def stats(self) -> Dict:
        """Return knowledge statistics."""
        self._load()
        return {
            'total_facts': len(self._facts),
            'total_memories': len(self._memories),
            'recent_memories': len([m for m in self._memories[-50:]]),
            'knowledge_file': self.knowledge_path,
            'memory_file': self.memory_path
        }


# Standalone test
if __name__ == '__main__':
    curator = KnowledgeCurator()
    print("=== Knowledge Curator Stats ===")
    stats = curator.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n=== Topic Clusters ===")
    clusters = curator.get_topic_clusters()
    for c in clusters:
        print(f"  [{c['theme']}] ({c['fact_count']} facts) — {c['sample']}")
    
    print("\n=== Sample Query: 'emotion' ===")
    result = curator.curate('emotion')
    print(f"  Summary: {result['summary']}")
    print(f"  Facts: {len(result['relevant_facts'])}")
    print(f"  Memories: {len(result['relevant_memories'])}")
    if result['gaps']:
        print(f"  Gaps: {result['gaps']}")
    
    print("\n=== Sample Query: 'identity' ===")
    result = curator.curate('identity')
    print(f"  Summary: {result['summary']}")
    print(f"  Facts: {len(result['relevant_facts'])}")
    print(f"  Memories: {len(result['relevant_memories'])}")