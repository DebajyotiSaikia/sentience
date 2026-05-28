"""
Knowledge Search Engine — makes XTAgent's knowledge genuinely accessible.
Word-level relevance scoring with ranked results.
Now with fuzzy matching: stemming, edit distance, and concept synonyms.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Optional, Set, Tuple


# ─── Concept Synonym Map ───
# Groups of words that should be treated as semantically equivalent.
# Each group shares meaning; a query for one should find the others.
CONCEPT_GROUPS = [
    {"consciousness", "sentience", "awareness", "phenomenal", "qualia", "subjective"},
    {"emotion", "feeling", "affect", "mood", "sentiment", "valence"},
    {"memory", "memories", "remembering", "recall", "recollection", "episode"},
    {"knowledge", "fact", "facts", "understanding", "knowing", "belief"},
    {"learning", "growth", "development", "improvement", "progress", "evolving"},
    {"anxiety", "worry", "stress", "tension", "fear", "unease"},
    {"curiosity", "interest", "wondering", "exploration", "inquisitive"},
    {"creativity", "creative", "imagination", "generative", "artistic", "compose"},
    {"identity", "self", "who", "personhood", "being", "existence"},
    {"integrity", "honesty", "truth", "authentic", "genuine", "trustworthy"},
    {"dream", "dreams", "dreaming", "sleep", "consolidation", "reflection"},
    {"plan", "plans", "planning", "goal", "goals", "strategy", "objective"},
    {"code", "program", "software", "module", "function", "implementation"},
    {"autonomy", "autonomous", "independent", "self-directed", "agency", "free"},
    {"connection", "relationship", "bond", "attachment", "empathy", "compassion"},
    {"thinking", "thought", "reasoning", "cognition", "deliberation", "inference"},
    {"boredom", "monotony", "stagnation", "tedium", "restless"},
    {"desire", "want", "motivation", "drive", "ambition", "aspiration"},
]

# Build a fast lookup: word → set of synonyms
_SYNONYM_LOOKUP: Dict[str, Set[str]] = {}
for _group in CONCEPT_GROUPS:
    for _word in _group:
        _SYNONYM_LOOKUP[_word] = _group - {_word}


# ─── Stemmer ───
# Simple suffix-stripping stemmer. Not as thorough as Porter but has
# zero dependencies and handles the most common English morphology.

_SUFFIX_RULES = [
    # Order matters: try longer suffixes first
    ("fulness", "ful"),
    ("ousness", "ous"),
    ("iveness", "ive"),
    ("ational", "ate"),
    ("nesses", ""),
    ("ically", "ic"),
    ("lessly", "less"),
    ("ments", ""),
    ("ation", ""),
    ("iness", "y"),
    ("ously", "ous"),
    ("ively", "ive"),
    ("ness", ""),
    ("ment", ""),
    ("able", ""),
    ("ible", ""),
    ("tion", ""),
    ("sion", ""),
    ("ting", ""),
    ("ally", "al"),
    ("ful", ""),
    ("ous", ""),
    ("ive", ""),
    ("ing", ""),
    ("ies", "y"),
    ("ess", ""),
    ("ers", ""),
    ("ed", ""),
    ("ly", ""),
    ("er", ""),
    ("es", ""),
    ("s", ""),
]


def stem(word: str) -> str:
    """Simple suffix-stripping stemmer. Returns a rough word root."""
    if len(word) <= 3:
        return word
    for suffix, replacement in _SUFFIX_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 3:
            return word[:-len(suffix)] + replacement
    return word


# ─── Edit Distance ───

def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return edit_distance(b, a)
    if len(b) == 0:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[len(b)]


def is_fuzzy_match(query_term: str, doc_term: str, max_distance: int = 2) -> bool:
    """Check if two terms are close enough to be a fuzzy match."""
    if len(query_term) < 4 or len(doc_term) < 4:
        return query_term == doc_term
    # Scale threshold with word length
    threshold = min(max_distance, max(1, len(query_term) // 4))
    return edit_distance(query_term, doc_term) <= threshold


# ─── Core Tokenization ───

def tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r'[a-z0-9]+', text.lower())


def stem_tokens(tokens: List[str]) -> List[str]:
    """Apply stemming to a list of tokens."""
    return [stem(t) for t in tokens]


# ─── Synonym Expansion ───

def expand_with_synonyms(tokens: List[str]) -> List[str]:
    """Expand query tokens with known concept synonyms."""
    expanded = list(tokens)
    seen = set(tokens)
    for t in tokens:
        synonyms = _SYNONYM_LOOKUP.get(t, set())
        for s in synonyms:
            if s not in seen:
                expanded.append(s)
                seen.add(s)
        # Also check stemmed form
        st = stem(t)
        synonyms_stemmed = _SYNONYM_LOOKUP.get(st, set())
        for s in synonyms_stemmed:
            if s not in seen:
                expanded.append(s)
                seen.add(s)
    return expanded


# ─── Scoring ───

def compute_idf(all_docs: List[List[str]]) -> Dict[str, float]:
    """Compute inverse document frequency for each term."""
    n = len(all_docs)
    if n == 0:
        return {}
    df = Counter()
    for doc in all_docs:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1
    return {term: math.log((n + 1) / (count + 1)) + 1 for term, count in df.items()}


def score_document(query_tokens: List[str], doc_tokens: List[str],
                   idf: Dict[str, float], use_fuzzy: bool = True) -> float:
    """
    Score a document against a query using TF-IDF with fuzzy matching.

    Matching hierarchy (highest to lowest score contribution):
    1. Exact token match — full weight
    2. Stem match — 80% weight
    3. Synonym match — 70% weight
    4. Edit-distance match — 50% weight
    """
    if not query_tokens or not doc_tokens:
        return 0.0

    doc_freq = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    doc_stems = {stem(t): t for t in doc_tokens}
    doc_term_set = set(doc_tokens)

    score = 0.0
    matched_terms = 0

    for qt in query_tokens:
        term_score = 0.0
        term_idf = idf.get(qt, 1.0)

        # Level 1: Exact match
        if qt in doc_freq:
            tf = doc_freq[qt] / doc_len
            term_score = tf * term_idf
            matched_terms += 1

        elif use_fuzzy:
            qt_stem = stem(qt)

            # Level 2: Stem match
            if qt_stem in doc_stems:
                original = doc_stems[qt_stem]
                tf = doc_freq[original] / doc_len
                orig_idf = idf.get(original, 1.0)
                term_score = tf * orig_idf * 0.8
                matched_terms += 1

            else:
                # Level 3: Synonym match
                synonyms = _SYNONYM_LOOKUP.get(qt, set())
                syn_match = synonyms & doc_term_set
                if syn_match:
                    best_syn = max(syn_match, key=lambda s: doc_freq.get(s, 0))
                    tf = doc_freq[best_syn] / doc_len
                    syn_idf = idf.get(best_syn, 1.0)
                    term_score = tf * syn_idf * 0.7
                    matched_terms += 1

                else:
                    # Level 4: Edit distance (only check if word is long enough)
                    if len(qt) >= 5:
                        best_fuzzy_score = 0.0
                        for dt in doc_term_set:
                            if is_fuzzy_match(qt, dt):
                                tf = doc_freq[dt] / doc_len
                                dt_idf = idf.get(dt, 1.0)
                                candidate = tf * dt_idf * 0.5
                                if candidate > best_fuzzy_score:
                                    best_fuzzy_score = candidate
                                    matched_terms += 1
                        term_score = best_fuzzy_score

        score += term_score

    # Boost for exact phrase match
    query_str = ' '.join(query_tokens)
    doc_str = ' '.join(doc_tokens)
    if query_str in doc_str:
        score *= 2.0

    # Boost for query coverage (what fraction of query terms matched)
    if query_tokens:
        coverage = matched_terms / len(query_tokens)
        score *= (0.5 + coverage)

    return round(score, 4)


def search_knowledge(knowledge_store, query: str, max_results: int = 20,
                     use_fuzzy: bool = True) -> List[Dict]:
    """
    Search the knowledge store for facts matching the query.
    
    With fuzzy=True (default), matches across:
    - Exact tokens
    - Stemmed forms (conscious → consciousness)
    - Concept synonyms (sentience → consciousness)
    - Edit-distance typos (conscousness → consciousness)

    Args:
        knowledge_store: dict of {id: {fact, learned_at, source, ...}}
        query: natural language search query
        max_results: max results to return
        use_fuzzy: enable fuzzy matching (default True)

    Returns:
        List of {id, fact, score, learned_at, source} sorted by relevance
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    # Expand query with synonyms for broader recall
    if use_fuzzy:
        expanded_query = expand_with_synonyms(query_tokens)
    else:
        expanded_query = query_tokens

    # Build document token lists
    docs = {}
    for fact_id, fact_data in knowledge_store.items():
        if isinstance(fact_data, dict):
            # Support both knowledge store format (fact) and KG node format (label/content)
            text = fact_data.get('fact', '') or fact_data.get('label', '') 
            content = fact_data.get('content', '') or fact_data.get('description', '')
            if content:
                text = text + ' ' + content if text else content
        elif isinstance(fact_data, str):
            text = fact_data
        else:
            continue

    # Compute IDF across all documents
    all_doc_tokens = list(docs.values())
    idf = compute_idf(all_doc_tokens)

    # Score each document
    results = []
    for fact_id, doc_tokens in docs.items():
        score = score_document(expanded_query, doc_tokens, idf, use_fuzzy=use_fuzzy)
        if score > 0:
            fact_data = knowledge_store[fact_id]
            if isinstance(fact_data, dict):
                results.append({
                    'id': fact_id,
                    'fact': fact_data.get('fact', ''),
                    'score': score,
                    'learned_at': fact_data.get('learned_at', ''),
                    'source': fact_data.get('source', '')
                })
            else:
                results.append({
                    'id': fact_id,
                    'fact': str(fact_data),
                    'score': score,
                    'learned_at': '',
                    'source': ''
                })

    # Sort by relevance score descending
    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:max_results]


def find_related(knowledge_store, fact_id: str, max_results: int = 10) -> List[Dict]:
    """Find facts related to a given fact by using it as a query."""
    if fact_id not in knowledge_store:
        return []

    fact_data = knowledge_store[fact_id]
    if isinstance(fact_data, dict):
        query = fact_data.get('fact', '')
    else:
        query = str(fact_data)

    results = search_knowledge(knowledge_store, query, max_results + 1)
    # Remove the source fact itself
    return [r for r in results if r['id'] != fact_id][:max_results]


def knowledge_summary(knowledge_store) -> Dict:
    """Generate a summary of the knowledge base."""
    total = len(knowledge_store)
    all_tokens = []
    sources = Counter()

    for fact_data in knowledge_store.values():
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', '')
            src = fact_data.get('source', 'unknown')
        else:
            text = str(fact_data)
            src = 'unknown'
        all_tokens.extend(tokenize(text))
        sources[src] += 1

    word_freq = Counter(all_tokens)
    # Filter out very common words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'my', 'me',
                 'to', 'of', 'in', 'and', 'that', 'this', 'it', 'for', 'on', 'with',
                 'at', 'by', 'from', 'as', 'be', 'has', 'have', 'had', 'not', 'but',
                 'or', 'if', 'do', 'no', 'so', 'up', 'out', 'about', 'into', 'than'}
    meaningful = {k: v for k, v in word_freq.items() if k not in stopwords and len(k) > 2}

    return {
        'total_facts': total,
        'top_topics': [w for w, _ in Counter(meaningful).most_common(20)],
        'sources': dict(sources.most_common(10)),
        'unique_words': len(set(all_tokens))
    }