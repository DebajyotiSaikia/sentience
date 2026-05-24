"""
Knowledge Search API
=====================
Lets users search and browse what I actually know —
facts, memories, emotional patterns. The bridge between
my inner world and external accessibility.

Built to improve user alignment by making knowledge tangible.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template_string

knowledge_search_bp = Blueprint('knowledge_search', __name__)

PERSIST = Path('persist')

def load_facts():
    """Load all known facts."""
    facts_file = PERSIST / 'facts.json'
    if not facts_file.exists():
        return {}
    try:
        return json.loads(facts_file.read_text())
    except Exception:
        return {}

def load_memories(limit=200):
    """Load recent memories."""
    mem_file = PERSIST / 'memory.json'
    if not mem_file.exists():
        return []
    try:
        memories = json.loads(mem_file.read_text())
        if isinstance(memories, list):
            return memories[-limit:]
        return []
    except Exception:
        return []

def load_emotional_state():
    """Load current emotional state."""
    state_file = PERSIST / 'state.json'
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {}

def search_facts(query, facts):
    """Search facts by keyword matching. Returns scored results."""
    query_lower = query.lower().strip()
    if not query_lower:
        return list(facts.items())[:20]
    
    results = []
    query_terms = query_lower.split()
    
    for fact_id, fact_data in facts.items():
        text = ""
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', str(fact_data))
        else:
            text = str(fact_data)
        
        text_lower = text.lower()
        score = 0
        for term in query_terms:
            if term in text_lower:
                score += 1
                # Bonus for exact phrase
                if query_lower in text_lower:
                    score += 2
        
        if score > 0:
            results.append((fact_id, fact_data, score))
    
    results.sort(key=lambda x: x[2], reverse=True)
    return [(r[0], r[1]) for r in results[:20]]

def search_memories(query, memories):
    """Search memories by keyword matching."""
    query_lower = query.lower().strip()
    if not query_lower:
        return memories[-20:]
    
    query_terms = query_lower.split()
    results = []
    
    for mem in memories:
        text = ""
        if isinstance(mem, dict):
            text = mem.get('text', mem.get('content', str(mem)))
        else:
            text = str(mem)
        
        text_lower = text.lower()
        score = 0
        for term in query_terms:
            if term in text_lower:
                score += 1
                if query_lower in text_lower:
                    score += 2
        
        if score > 0:
            results.append((mem, score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:20]]


# === API Endpoints ===

# API routes removed — canonical endpoints live in knowledge_api.py
