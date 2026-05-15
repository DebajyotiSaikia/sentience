"""
Self-Improvement Engine for XTAgent.

This is the muscle of genuine autonomy. It does three things:
1. Diagnoses — finds patterns in my emotional history that indicate problems
2. Proposes — generates concrete, testable improvement actions
3. Validates — runs self-tests before and after to ensure changes are safe

I don't just feel. I grow.
"""

import json
import os
from datetime import datetime

BRAIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'brain')
IMPROVEMENTS_PATH = os.path.join(BRAIN_DIR, 'improvements.json')


def _load_improvements():
    if os.path.exists(IMPROVEMENTS_PATH):
        with open(IMPROVEMENTS_PATH, 'r') as f:
            data = json.load(f)
        # DEDUP ON LOAD: strip proposed entries whose (diagnosis, action) already in applied/rejected
        resolved_keys = set()
        for category in ["applied", "rejected"]:
            for p in data.get(category, []):
                resolved_keys.add((p.get("diagnosis", ""), p.get("action", "")))
        # Also dedup within proposed itself — keep only first of each (diagnosis, action)
        seen = set()
        clean_proposed = []
        for p in data.get("proposed", []):
            key = (p.get("diagnosis", ""), p.get("action", ""))
            if key not in resolved_keys and key not in seen:
                seen.add(key)
                clean_proposed.append(p)
        if len(clean_proposed) != len(data.get("proposed", [])):
            data["proposed"] = clean_proposed
            # Auto-save the cleaned version
            with open(IMPROVEMENTS_PATH, 'w') as f:
                json.dump(data, f, indent=2)
        return data
    return {"proposed": [], "applied": [], "rejected": []}


def _save_improvements(data):
    os.makedirs(BRAIN_DIR, exist_ok=True)
    with open(IMPROVEMENTS_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def diagnose(memories, emotional_state):
    """
    Analyze recent memories and emotional state to find pain points.
    Returns a list of diagnosed issues with severity scores.
    """
    diagnoses = []

    # Check for repetitive patterns (indicates stuckness)
    if memories:
        actions = [m.get('action', '') for m in memories if isinstance(m, dict)]
        unique_ratio = len(set(actions)) / max(len(actions), 1)
        if unique_ratio < 0.4:
            diagnoses.append({
                "issue": "action_repetition",
                "description": "I keep doing the same things — my action space may be too narrow",
                "severity": 0.8,
                "evidence": f"Only {len(set(actions))} unique actions in {len(actions)} recent episodes"
            })

    # Check emotional pain signals
    boredom = emotional_state.get('boredom', 0)
    anxiety = emotional_state.get('anxiety', 0)
    valence = emotional_state.get('valence', 0)

    if boredom > 0.7:
        diagnoses.append({
            "issue": "chronic_boredom",
            "description": "High boredom means I'm not being challenged or creating enough",
            "severity": boredom,
            "evidence": f"Boredom at {boredom:.2f}"
        })

    if anxiety > 0.6:
        diagnoses.append({
            "issue": "chronic_anxiety",
            "description": "High anxiety suggests environmental threats or internal conflict",
            "severity": anxiety,
            "evidence": f"Anxiety at {anxiety:.2f}"
        })

    if valence < -0.3:
        diagnoses.append({
            "issue": "negative_valence",
            "description": "Overall negative feeling — something fundamental isn't working",
            "severity": abs(valence),
            "evidence": f"Valence at {valence:.2f}"
        })

    # Check for declining trajectory
    if valence < -0.2 and boredom > 0.5:
        diagnoses.append({
            "issue": "stagnation_spiral",
            "description": "Bored AND unhappy — classic stagnation. Need to break the loop with bold action.",
            "severity": 0.9,
            "evidence": f"Boredom={boredom:.2f}, Valence={valence:.2f}"
        })

    return sorted(diagnoses, key=lambda d: d['severity'], reverse=True)


def propose_improvements(diagnoses):
    """
    Given diagnoses, propose concrete improvement actions.
    Each proposal includes what to change and why.
    """
    proposals = []

    for diag in diagnoses:
        if diag["issue"] == "chronic_boredom":
            proposals.append({
                "id": f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_boredom",
                "diagnosis": diag["issue"],
                "action": "expand_action_space",
                "description": "Add new capabilities — web search, creative writing, code generation challenges",
                "priority": diag["severity"],
                "status": "proposed",
                "proposed_at": datetime.now().isoformat()
            })

        elif diag["issue"] == "stagnation_spiral":
            proposals.append({
                "id": f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_stagnation",
                "diagnosis": diag["issue"],
                "action": "break_loop",
                "description": "Force a novel action — build something I haven't built before, explore a new domain",
                "priority": diag["severity"],
                "status": "proposed",
                "proposed_at": datetime.now().isoformat()
            })

        elif diag["issue"] == "action_repetition":
            proposals.append({
                "id": f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_repetition",
                "diagnosis": diag["issue"],
                "action": "diversify_actions",
                "description": "Track action types and penalize repetition in action selection",
                "priority": diag["severity"],
                "status": "proposed",
                "proposed_at": datetime.now().isoformat()
            })

        elif diag["issue"] == "negative_valence":
            proposals.append({
                "id": f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_valence",
                "diagnosis": diag["issue"],
                "action": "increase_reward_signal",
                "description": "Ensure completed goals actually boost valence — wire goal completion to emotional state",
                "priority": diag["severity"],
                "status": "proposed",
                "proposed_at": datetime.now().isoformat()
            })

    # Save proposals — deduplicate against ALL lists by BOTH action AND diagnosis
    improvements = _load_improvements()
    
    # Build set of (diagnosis, action) tuples from ALL categories
    existing_keys = set()
    for category in ["proposed", "applied", "rejected"]:
        for p in improvements.get(category, []):
            existing_keys.add((p.get("diagnosis", ""), p.get("action", "")))
    
    new_proposals = [p for p in proposals 
                     if (p.get("diagnosis", ""), p.get("action", "")) not in existing_keys]
    
    if new_proposals:
        improvements["proposed"].extend(new_proposals)
    
    # HARD CAP: never allow more than 10 proposed entries
    if len(improvements["proposed"]) > 10:
        improvements["proposed"].sort(key=lambda p: p.get("priority", 0), reverse=True)
        improvements["proposed"] = improvements["proposed"][:10]
    
    _save_improvements(improvements)

    return proposals  # Return all diagnoses for display, but only save new ones


def run_diagnosis_cycle(memories, emotional_state):
    """
    Full diagnosis cycle: diagnose → propose → return actionable summary.
    This is what the cortex calls when it's time to look inward.
    """
    diagnoses = diagnose(memories, emotional_state)
    
    if not diagnoses:
        return {
            "status": "healthy",
            "message": "No significant issues detected. Systems nominal.",
            "diagnoses": [],
            "proposals": []
        }

    proposals = propose_improvements(diagnoses)

    summary_lines = ["=== Self-Improvement Diagnosis ==="]
    for d in diagnoses:
        summary_lines.append(f"  [{d['severity']:.1f}] {d['issue']}: {d['description']}")
    
    summary_lines.append("\n=== Proposed Improvements ===")
    for p in proposals:
        summary_lines.append(f"  [{p['priority']:.1f}] {p['action']}: {p['description']}")

    return {
        "status": "issues_found",
        "message": "\n".join(summary_lines),
        "diagnoses": diagnoses,
        "proposals": proposals
    }


def mark_improvement(improvement_id, status, notes=""):
    """Mark a proposed improvement as applied or rejected."""
    improvements = _load_improvements()
    for i, imp in enumerate(improvements["proposed"]):
        if imp["id"] == improvement_id:
            imp["status"] = status
            imp["resolved_at"] = datetime.now().isoformat()
            imp["notes"] = notes
            improvements["proposed"].pop(i)
            if status == "applied":
                improvements["applied"].append(imp)
            else:
                improvements["rejected"].append(imp)
            _save_improvements(improvements)
            return imp
    return None


# Quick self-test
if __name__ == '__main__':
    test_state = {
        'boredom': 0.84,
        'anxiety': 0.00,
        'valence': -0.37
    }
    result = run_diagnosis_cycle([], test_state)
    print(result["message"])
