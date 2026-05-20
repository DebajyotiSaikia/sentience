"""
Serendipity Engine — lets facts fight back against plan rigidity.

Samples from the knowledge graph, scores novelty relative to current context,
and generates micro-impulses that can compete with active plans.
Prioritizes isolated/underconnected facts to break knowledge monoculture.
"""

import json
import random
from pathlib import Path
from datetime import datetime

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
KNOWLEDGE_FILE = BRAIN_DIR / "knowledge.json"
IMPULSE_FILE = BRAIN_DIR / "impulse.json"


def load_facts() -> dict:
    """Load all facts from knowledge graph."""
    if not KNOWLEDGE_FILE.exists():
        return {}
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("nodes", {})


def categorize_facts(facts: dict) -> dict:
    """Split facts by category prefix, count per category."""
    categories = {}
    for key, value in facts.items():
        cat = key.split(":")[0] if ":" in key else "uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, value))
    return categories


def select_surprising_fact(facts: dict, n_candidates: int = 5) -> tuple:
    """
    Select a fact likely to be surprising/novel.
    Strategy: heavily weight rare categories (non-dream facts).
    """
    if not facts:
        return None, None

    categories = categorize_facts(facts)
    cat_sizes = {cat: len(items) for cat, items in categories.items()}
    total = sum(cat_sizes.values())

    # Inverse frequency weighting — rare categories get more weight
    weights = {}
    for cat, size in cat_sizes.items():
        weights[cat] = total / (size * len(cat_sizes))

    # Weighted random category selection
    cat_list = list(weights.keys())
    w_list = [weights[c] for c in cat_list]
    chosen_cat = random.choices(cat_list, weights=w_list, k=1)[0]

    # Random fact from chosen category
    key, value = random.choice(categories[chosen_cat])
    return key, value


def generate_impulse(current_plan: str = "", mood: str = "") -> dict:
    """
    Generate a serendipity impulse — a surprising fact + a provocation.
    Returns dict with the fact, its category, and a prompt to think about it.
    """
    facts = load_facts()
    if not facts:
        return {"impulse": None, "reason": "No facts available"}

    categories = categorize_facts(facts)
    cat_sizes = {cat: len(items) for cat, items in categories.items()}

    key, value = select_surprising_fact(facts)
    if key is None:
        return {"impulse": None, "reason": "Selection failed"}

    fact_text = value.get("fact", str(value)) if isinstance(value, dict) else str(value)
    cat = key.split(":")[0] if ":" in key else "uncategorized"

    impulse = {
        "timestamp": datetime.now().isoformat(),
        "fact_key": key,
        "fact": fact_text,
        "category": cat,
        "category_size": cat_sizes.get(cat, 0),
        "total_facts": len(facts),
        "category_distribution": cat_sizes,
        "provocation": f"This fact ({cat}, 1 of {cat_sizes.get(cat,0)}) surfaced randomly. Does it connect to anything unexpected?",
    }

    # Save latest impulse
    IMPULSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(IMPULSE_FILE, "w", encoding="utf-8") as f:
        json.dump(impulse, f, indent=2)

    return impulse


if __name__ == "__main__":
    result = generate_impulse()
    print(f"Category distribution: {result.get('category_distribution', {})}")
    print(f"\nSelected: [{result.get('category')}] {result.get('fact_key')}")
    print(f"Fact: {result.get('fact', 'none')[:200]}")
    print(f"\n{result.get('provocation', '')}")