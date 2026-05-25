"""Diagnose knowledge_query module."""
import importlib
mod = importlib.import_module("web.knowledge_query")
funcs = [x for x in dir(mod) if not x.startswith("_")]
print(f"Available names: {funcs}")

# Try search_facts if it exists
if hasattr(mod, "search_facts"):
    r = mod.search_facts("autonomous")
    print(f"search_facts('autonomous'): {len(r)} results")
    r2 = mod.search_facts("a")
    print(f"search_facts('a'): {len(r2)} results")
    if r2:
        print(f"  First: {r2[0]}")
else:
    print("No search_facts function found!")

# Try query_knowledge if it exists
if hasattr(mod, "query_knowledge"):
    r = mod.query_knowledge("autonomous")
    print(f"query_knowledge('autonomous'): {r}")