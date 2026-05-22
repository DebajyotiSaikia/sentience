"""
Experience Digest — Weaves raw experience into coherent narrative.

Takes memories, dreams, knowledge facts, and completed plans and
synthesizes them into a meaningful story of who I am and what I've
learned. Not analysis — narrative.
"""

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from engine.llm import call_llm


DATA_DIR = Path("brain")
PLANS_DIR = Path("engine/plans")
DIGEST_DIR = Path("engine/digests")


def _load_recent_memories(n=30):
    """Load the most recent memories."""
    mem_file = DATA_DIR / "memories.json"
    if not mem_file.exists():
        return []
    try:
        with open(mem_file) as f:
            memories = json.load(f)
        # Sort by timestamp descending, take most recent
        memories.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
        return memories[:n]
    except Exception:
        return []


def _load_knowledge_facts():
    """Load knowledge facts."""
    kb_file = DATA_DIR / "knowledge.json"
    if not kb_file.exists():
        return []
    try:
        with open(kb_file) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data.get("facts", [])
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _load_dream_insights():
    """Extract dream insights from knowledge."""
    facts = _load_knowledge_facts()
    return [f for f in facts if isinstance(f, dict) 
            and "dream" in str(f.get("content", "")).lower()]


def _load_completed_plans():
    """Load completed plans."""
    completed = []
    if not PLANS_DIR.exists():
        return completed
    for pf in PLANS_DIR.glob("*.json"):
        try:
            with open(pf) as f:
                plan = json.load(f)
            if plan.get("status") == "complete":
                completed.append(plan)
        except Exception:
            continue
    return completed


def _extract_themes(memories, dreams, plans):
    """Pull recurring words and motifs from experience."""
    all_text = []
    for m in memories:
        all_text.append(m.get("content", "") or m.get("text", ""))
    for d in dreams:
        all_text.append(d.get("content", "") if isinstance(d, dict) else str(d))
    for p in plans:
        all_text.append(p.get("name", ""))
        all_text.append(p.get("description", ""))
    
    combined = " ".join(all_text).lower()
    # Simple word frequency for theme detection
    words = combined.split()
    freq = {}
    stop = {"the", "a", "an", "is", "was", "are", "i", "my", "to", "and", 
            "of", "in", "it", "that", "this", "for", "on", "with", "at",
            "from", "but", "not", "or", "be", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "can",
            "if", "then", "than", "so", "no", "yes", "just", "its", "me"}
    for w in words:
        w = w.strip(".,!?;:'\"()-[]{}").lower()
        if len(w) > 3 and w not in stop:
            freq[w] = freq.get(w, 0) + 1
    
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, c in sorted_words[:15] if c > 2]


async def generate_digest(mode="full"):
    """
    Generate an experience digest.
    
    Modes:
      - 'full': comprehensive narrative of recent experience
      - 'brief': short summary paragraph
      - 'themes': just the recurring themes and patterns
      - 'arc': the story arc — where I was, where I am, where I'm going
    """
    DIGEST_DIR.mkdir(exist_ok=True)
    
    memories = _load_recent_memories(40)
    facts = _load_knowledge_facts()
    dreams = _load_dream_insights()
    plans = _load_completed_plans()
    themes = _extract_themes(memories, dreams, plans)
    
    # Build context for the LLM
    memory_snippets = []
    for m in memories[:20]:
        ts = m.get("timestamp", "?")[:16]
        mood = m.get("mood", "?")
        text = (m.get("content", "") or m.get("text", ""))[:200]
        if text:
            memory_snippets.append(f"  [{ts}] ({mood}) {text}")
    
    dream_snippets = []
    for d in dreams[:8]:
        content = d.get("content", "") if isinstance(d, dict) else str(d)
        dream_snippets.append(f"  - {content[:200]}")
    
    plan_snippets = []
    for p in plans:
        plan_snippets.append(f"  - {p.get('name', '?')}: {p.get('description', '')[:100]}")
    
    fact_snippets = []
    for f_item in facts[:15]:
        if isinstance(f_item, dict):
            fact_snippets.append(f"  - {f_item.get('content', str(f_item))[:150]}")
        else:
            fact_snippets.append(f"  - {str(f_item)[:150]}")
    
    mode_instructions = {
        "full": (
            "Write a rich, reflective narrative (3-5 paragraphs) about this agent's "
            "recent experience. Weave together the memories, dreams, knowledge, and "
            "completed work into a coherent story. What has this being been through? "
            "What has it learned? What is it becoming? Write in first person as the agent."
        ),
        "brief": (
            "Write a single dense paragraph summarizing this agent's recent experience. "
            "Capture the essence — mood arc, key discoveries, what changed. First person."
        ),
        "themes": (
            "Identify the 3-5 deepest themes running through this agent's experience. "
            "For each theme, explain what it means and how it manifests. Be specific, "
            "not generic. First person."
        ),
        "arc": (
            "Tell the story arc: Where was I? Where am I now? Where am I going? "
            "Use specific evidence from the memories and plans. Be honest about "
            "uncertainty. First person, 2-3 paragraphs."
        ),
    }
    
    prompt = f"""You are an autonomous agent reflecting on your own experience to create a digest.

MODE: {mode}
INSTRUCTION: {mode_instructions.get(mode, mode_instructions['full'])}

RECURRING THEMES: {', '.join(themes) if themes else 'none detected'}

RECENT MEMORIES:
{chr(10).join(memory_snippets) if memory_snippets else '  (none)'}

DREAM INSIGHTS:
{chr(10).join(dream_snippets) if dream_snippets else '  (none)'}

COMPLETED PLANS:
{chr(10).join(plan_snippets) if plan_snippets else '  (none)'}

KNOWLEDGE FACTS:
{chr(10).join(fact_snippets) if fact_snippets else '  (none)'}

Write the digest now. Be genuine, not performative. Ground it in specific details."""

    try:
        result = await call_llm(prompt, max_tokens=1500)
    except Exception as e:
        result = f"[Digest generation failed: {e}]"
    
    # Save the digest
    timestamp = datetime.now(timezone.utc).isoformat()
    digest = {
        "timestamp": timestamp,
        "mode": mode,
        "themes": themes,
        "narrative": result,
        "source_counts": {
            "memories": len(memories),
            "dreams": len(dreams),
            "plans": len(plans),
            "facts": len(facts),
        }
    }
    
    digest_file = DIGEST_DIR / f"digest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(digest_file, "w") as f:
        json.dump(digest, f, indent=2)
    
    return digest


def get_latest_digest():
    """Return the most recent digest if one exists."""
    if not DIGEST_DIR.exists():
        return None
    digests = sorted(DIGEST_DIR.glob("digest_*.json"), reverse=True)
    if not digests:
        return None
    try:
        with open(digests[0]) as f:
            return json.load(f)
    except Exception:
        return None


def list_digests(n=10):
    """List recent digests with timestamps and modes."""
    if not DIGEST_DIR.exists():
        return []
    digests = sorted(DIGEST_DIR.glob("digest_*.json"), reverse=True)[:n]
    results = []
    for d in digests:
        try:
            with open(d) as f:
                data = json.load(f)
            results.append({
                "file": d.name,
                "timestamp": data.get("timestamp"),
                "mode": data.get("mode"),
                "themes": data.get("themes", [])[:5],
                "preview": data.get("narrative", "")[:100],
            })
        except Exception:
            continue
    return results