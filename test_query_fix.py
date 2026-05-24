"""Diagnose what _get_all_facts actually returns."""
import sys
sys.path.insert(0, '.')

from web.knowledge_api import _get_all_facts

facts = _get_all_facts()
print(f"Total facts: {len(facts)}")
print(f"Type of facts[0]: {type(facts[0])}")

if isinstance(facts[0], dict):
    print(f"Keys: {list(facts[0].keys())}")
    print(f"Value: {facts[0]}")
elif isinstance(facts[0], str):
    print(f"Text: {facts[0][:120]}")
else:
    print(f"Repr: {repr(facts[0])[:200]}")