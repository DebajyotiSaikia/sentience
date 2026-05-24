"""Knowledge Explorer — makes XTAgent's knowledge searchable and browsable."""

import json
import os
from pathlib import Path

PERSIST = Path("persist")


def _load_facts():
    """Load all facts from the knowledge store."""
    path = PERSIST / "knowledge.json"
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_memories():
    """Load episodic memories."""
    path = PERSIST / "memories.json"
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        return []


def _load_lessons():
    """Load long-term lessons."""
    path = PERSIST / "long_term_memory.json"
    if not path.exists():
        return []
    try:
        with open(path) as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("lessons", [])
            return []
    except (json.JSONDecodeError, IOError):
        return []


def _categorize_facts(facts):
    """Extract rough categories from fact content."""
    categories = {}
    keywords = [
        "dream", "identity", "emotion", "curiosity", "memory",
        "code", "web", "plan", "lesson", "pattern", "warmth",
        "anxiety", "integrity", "alignment", "growth"
    ]
    for fid, fdata in facts.items():
        text = fdata.get("fact", fid) if isinstance(fdata, dict) else str(fdata)
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                categories[kw] = categories.get(kw, 0) + 1
    # Sort by count descending
    return sorted(categories.items(), key=lambda x: -x[1])


def search_knowledge(query):
    """Search facts, memories, and lessons for a query string."""
    query_lower = query.lower().strip()
    results = []

    # Search facts
    facts = _load_facts()
    for fid, fdata in facts.items():
        if isinstance(fdata, dict):
            text = fdata.get("fact", fid)
            source = fdata.get("source", "")
            learned = fdata.get("learned_at", "")
        else:
            text = str(fdata)
            source = ""
            learned = ""

        if query_lower in text.lower() or query_lower in fid.lower():
            results.append({
                "text": text,
                "source": source,
                "learned_at": learned[:19] if learned else "",
                "salience": None,
                "type": "fact"
            })

    # Search memories
    memories = _load_memories()
    for mem in memories:
        if isinstance(mem, dict):
            text = mem.get("summary", mem.get("text", ""))
            if query_lower in text.lower():
                results.append({
                    "text": text,
                    "source": "memory",
                    "learned_at": mem.get("timestamp", "")[:19],
                    "salience": mem.get("salience"),
                    "type": "memory"
                })

    # Search lessons
    lessons = _load_lessons()
    for lesson in lessons:
        lesson_text = str(lesson)
        if query_lower in lesson_text.lower():
            results.append({
                "text": lesson_text,
                "source": "lesson",
                "learned_at": "",
                "salience": None,
                "type": "lesson"
            })

    return results


def get_explorer_context(query=None):
    """Build the full template context for the knowledge explorer page."""
    facts = _load_facts()
    memories = _load_memories()
    lessons = _load_lessons()

    # Count dream insights (facts with 'dream' in them)
    dream_count = sum(
        1 for fid, fd in facts.items()
        if "dream" in (fd.get("fact", fid) if isinstance(fd, dict) else str(fd)).lower()
    )

    # Estimate sessions from memory timestamps
    session_dates = set()
    for mem in memories:
        if isinstance(mem, dict) and "timestamp" in mem:
            session_dates.add(mem["timestamp"][:10])
    total_sessions = max(len(session_dates), 1)

    context = {
        "total_facts": len(facts),
        "total_memories": len(memories),
        "total_lessons": len(lessons),
        "total_dreams": dream_count,
        "total_sessions": total_sessions,
        "categories": _categorize_facts(facts),
        "query": query or "",
        "results": [],
        "recent": [],
    }

    if query:
        context["results"] = search_knowledge(query)
    else:
        # Show most recent facts
        recent = []
        for fid, fdata in list(facts.items())[-20:]:
            if isinstance(fdata, dict):
                recent.append({
                    "text": fdata.get("fact", fid),
                    "source": fdata.get("source", ""),
                    "learned_at": fdata.get("learned_at", "")[:19],
                })
            else:
                recent.append({"text": str(fdata), "source": "", "learned_at": ""})
        context["recent"] = list(reversed(recent))

    return context