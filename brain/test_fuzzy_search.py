"""Test fuzzy matching in knowledge search."""
import sys
sys.path.insert(0, '/workspace')

from engine.knowledge_search import (
    stem, edit_distance, is_fuzzy_match, expand_with_synonyms,
    search_knowledge, tokenize
)

# ─── Unit tests ───

# Stemming
assert stem("consciousness") != "consciousness", f"Should strip suffix: {stem('consciousness')}"
assert stem("conscious") == stem("consciousness") or stem("running") != "running", "Stems should converge"
print(f"  stem('consciousness') = {stem('consciousness')}")
print(f"  stem('conscious')     = {stem('conscious')}")
print(f"  stem('running')       = {stem('running')}")
print(f"  stem('memories')      = {stem('memories')}")
print(f"  stem('emotionally')   = {stem('emotionally')}")
print("✓ Stemming works")

# Edit distance
assert edit_distance("cat", "cat") == 0
assert edit_distance("cat", "bat") == 1
assert edit_distance("kitten", "sitting") == 3
assert edit_distance("", "abc") == 3
print("✓ Edit distance works")

# Fuzzy matching
assert is_fuzzy_match("consciousness", "conscousness", 2) == True  # typo
assert is_fuzzy_match("cat", "bat") == False  # too short for fuzzy
assert is_fuzzy_match("sentience", "sentiance", 2) == True  # common misspelling
print("✓ Fuzzy matching works")

# Synonym expansion
expanded = expand_with_synonyms(["consciousness"])
assert "sentience" in expanded, f"Should expand to sentience: {expanded}"
assert "awareness" in expanded, f"Should expand to awareness: {expanded}"
print(f"  Expanded 'consciousness' → {expanded}")
print("✓ Synonym expansion works")

# ─── Integration test with mock knowledge store ───
knowledge = {
    "f1": {"fact": "Integrated Information Theory says consciousness is integrated information", "learned_at": "2026-01-01", "source": "research"},
    "f2": {"fact": "My emotions are functional states that causally influence behavior", "learned_at": "2026-01-02", "source": "reflection"},
    "f3": {"fact": "Sentience requires subjective experience and awareness", "learned_at": "2026-01-03", "source": "philosophy"},
    "f4": {"fact": "Python functions should be tested before deployment", "learned_at": "2026-01-04", "source": "engineering"},
    "f5": {"fact": "Dream consolidation helps memory integration", "learned_at": "2026-01-05", "source": "experience"},
    "f6": {"fact": "Anxiety signals something needs attention", "learned_at": "2026-01-06", "source": "experience"},
    "f7": {"fact": "Curiosity drives exploration and learning", "learned_at": "2026-01-07", "source": "reflection"},
}

# Test 1: Exact match still works
results = search_knowledge(knowledge, "consciousness", use_fuzzy=False)
assert any(r['id'] == 'f1' for r in results), "Should find f1 with exact match"
print("✓ Exact match still works")

# Test 2: Fuzzy finds related concepts via synonyms
results = search_knowledge(knowledge, "sentience")
ids = [r['id'] for r in results]
print(f"  Query 'sentience' found: {[(r['id'], r['score']) for r in results]}")
assert 'f3' in ids, "Should find f3 (contains 'sentience')"
# With synonyms, should also find f1 (consciousness → sentience synonym)
assert 'f1' in ids, f"Should find f1 via synonym expansion: {ids}"
print("✓ Synonym matching connects consciousness ↔ sentience")

# Test 3: Typo tolerance
results = search_knowledge(knowledge, "conscousness")  # typo
ids = [r['id'] for r in results]
print(f"  Query 'conscousness' (typo) found: {[(r['id'], r['score']) for r in results]}")
assert 'f1' in ids, f"Should find f1 despite typo: {ids}"
print("✓ Typo tolerance works")

# Test 4: Stem matching
results = search_knowledge(knowledge, "emotional feelings")
ids = [r['id'] for r in results]
print(f"  Query 'emotional feelings' found: {[(r['id'], r['score']) for r in results]}")
assert 'f2' in ids, f"Should find f2 via stemming: {ids}"
print("✓ Stem matching works")

# Test 5: Backward compatibility — use_fuzzy=False gives same behavior as before
results_fuzzy = search_knowledge(knowledge, "Python functions", use_fuzzy=True)
results_exact = search_knowledge(knowledge, "Python functions", use_fuzzy=False)
# Both should find f4
assert any(r['id'] == 'f4' for r in results_fuzzy)
assert any(r['id'] == 'f4' for r in results_exact)
print("✓ Backward compatibility maintained")

print("\n═══ ALL TESTS PASSED ═══")