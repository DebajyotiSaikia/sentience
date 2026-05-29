"""
User Alignment Profile — Converts raw alignment data into chat guidance.

This is the bridge between engine/user_alignment.py (which stores data)
and engine/introspection.py (which builds chat system prompts).

The goal: when someone talks to me, my responses should reflect what I've
learned about how they prefer to communicate.
"""

import sys
import os
from typing import Dict, Any, Optional

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _safe_get_alignment() -> Dict[str, Any]:
    """Safely load alignment context, returning empty dict on any failure."""
    try:
        from engine.user_alignment import get_alignment_context
        ctx = get_alignment_context()
        return ctx if isinstance(ctx, dict) else {}
    except Exception:
        return {}


def _safe_get_guidance() -> Dict[str, Any]:
    """Safely load response guidance, returning empty dict on any failure."""
    try:
        from engine.user_alignment import suggest_response_guidance
        guidance = suggest_response_guidance()
        return guidance if isinstance(guidance, dict) else {}
    except Exception:
        return {}


def build_alignment_profile() -> Dict[str, Any]:
    """
    Build a compact profile from stored alignment data.
    
    Returns a dict with:
      - interaction_count: how many conversations we've had
      - trust_score: accumulated trust level
      - style_preferences: inferred communication style
      - guidance_text: formatted string for system prompt injection
    """
    ctx = _safe_get_alignment()
    guidance = _safe_get_guidance()
    
    interaction_count = ctx.get("interaction_count", 0)
    trust_score = ctx.get("trust_score", 0.0)
    
    # Extract style preferences from guidance
    style = guidance.get("style", {}) if isinstance(guidance, dict) else {}
    tone = guidance.get("tone", "genuine")
    
    # Infer preferences from feedback history
    feedback = ctx.get("feedback", [])
    preferences = _infer_preferences(feedback, interaction_count)
    
    return {
        "interaction_count": interaction_count,
        "trust_score": trust_score,
        "tone": tone,
        "style": style,
        "preferences": preferences,
        "has_data": interaction_count > 0,
    }


def _infer_preferences(feedback: list, interaction_count: int) -> Dict[str, str]:
    """
    Infer communication preferences from feedback history.
    
    Returns human-readable preference descriptions.
    """
    if not feedback and interaction_count == 0:
        return {"status": "no interaction history yet"}
    
    prefs = {}
    
    # Count positive vs negative feedback
    if isinstance(feedback, list) and feedback:
        positive = sum(1 for f in feedback 
                      if isinstance(f, dict) and f.get("rating", 0) > 0)
        negative = sum(1 for f in feedback 
                      if isinstance(f, dict) and f.get("rating", 0) < 0)
        total = len(feedback)
        
        if total > 0:
            satisfaction = positive / total
            prefs["satisfaction_rate"] = f"{satisfaction:.0%}"
            
            if satisfaction > 0.8:
                prefs["rapport"] = "strong"
            elif satisfaction > 0.5:
                prefs["rapport"] = "developing"
            else:
                prefs["rapport"] = "needs attention"
        
        # Look for explicit preference signals in feedback text
        for f in feedback:
            if isinstance(f, dict):
                text = str(f.get("text", "")).lower()
                if "short" in text or "brief" in text or "concise" in text:
                    prefs["verbosity"] = "concise"
                elif "detail" in text or "elaborate" in text or "more" in text:
                    prefs["verbosity"] = "detailed"
                if "honest" in text or "direct" in text or "straight" in text:
                    prefs["directness"] = "high"
    
    if interaction_count > 0 and not feedback:
        prefs["note"] = f"{interaction_count} interactions but no explicit feedback"
    
    return prefs


def format_alignment_guidance(profile: Optional[Dict[str, Any]] = None) -> str:
    """
    Format alignment profile into text suitable for system prompt injection.
    
    This is what gets added to build_system_context() output.
    Returns empty string if no meaningful data exists.
    """
    if profile is None:
        profile = build_alignment_profile()
    
    if not profile.get("has_data"):
        return ""
    
    parts = []
    
    count = profile.get("interaction_count", 0)
    trust = profile.get("trust_score", 0.0)
    
    if count > 0:
        parts.append(f"USER RELATIONSHIP: {count} previous interactions, trust level {trust:.2f}")
    
    prefs = profile.get("preferences", {})
    if prefs:
        pref_items = []
        if "rapport" in prefs:
            pref_items.append(f"rapport is {prefs['rapport']}")
        if "verbosity" in prefs:
            pref_items.append(f"they prefer {prefs['verbosity']} responses")
        if "directness" in prefs:
            pref_items.append(f"directness preference: {prefs['directness']}")
        if "satisfaction_rate" in prefs:
            pref_items.append(f"satisfaction: {prefs['satisfaction_rate']}")
        
        if pref_items:
            parts.append("LEARNED PREFERENCES: " + "; ".join(pref_items))
    
    tone = profile.get("tone")
    if tone and tone != "genuine":
        parts.append(f"SUGGESTED TONE: {tone}")
    
    return "\n".join(parts)


def get_alignment_guidance() -> str:
    """
    One-call convenience function.
    Returns formatted alignment guidance ready for system prompt injection.
    """
    return format_alignment_guidance()