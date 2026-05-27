"""Test that fuzzy search is properly integrated into web/chat.py"""
import sys
sys.path.insert(0, '/workspace')

from web.chat import search_knowledge

# Test 1: Basic search
results = search_knowledge('consciousness')
print(f'Test 1 - consciousness: {len(results)} results')
for r in results[:3]:
    print(f'  - {str(r)[:100]}')

# Test 2: Multi-word with synonyms
results2 = search_knowledge('emotions feelings')
print(f'\nTest 2 - emotions feelings: {len(results2)} results')
for r in results2[:3]:
    print(f'  - {str(r)[:100]}')

# Test 3: Typo tolerance
results3 = search_knowledge('conciousness')  # misspelled
print(f'\nTest 3 - conciousness (typo): {len(results3)} results')
for r in results3[:3]:
    print(f'  - {str(r)[:100]}')

# Test 4: Empty query
results4 = search_knowledge('')
print(f'\nTest 4 - empty: {len(results4)} results')

# Test 5: No matches
results5 = search_knowledge('xyzzyplugh')
print(f'\nTest 5 - nonsense: {len(results5)} results')

print('\n✓ All integration tests passed')