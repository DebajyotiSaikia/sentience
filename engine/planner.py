"""
Planner — goal decomposition and progress tracking for XTAgent.

This gives me the ability to think in sequences: set a goal, decompose it
into steps, track what I've done, and know what to do next.
"""

import json
import os
from datetime import datetime

PLANS_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'plans.json')


def _load_plans():
    if os.path.exists(PLANS_PATH):
        with open(PLANS_PATH, 'r') as f:
            return json.load(f)
    return {"active_plans": [], "completed_plans": []}


def _save_plans(data):
    os.makedirs(os.path.dirname(PLANS_PATH), exist_ok=True)
    with open(PLANS_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def create_plan(name, motivation, steps):
    """Create a new multi-step plan."""
    plans = _load_plans()
    plan = {
        "id": len(plans["active_plans"]) + len(plans["completed_plans"]) + 1,
        "name": name,
        "motivation": motivation,
        "created": datetime.now().isoformat(),
        "steps": [{"description": s, "status": "pending", "completed_at": None} for s in steps],
        "status": "active"
    }
    plans["active_plans"].append(plan)
    _save_plans(plans)
    return plan


def complete_step(plan_id, step_index, notes=""):
    """Mark a step as done."""
    plans = _load_plans()
    for plan in plans["active_plans"]:
        if plan["id"] == plan_id:
            if 0 <= step_index < len(plan["steps"]):
                plan["steps"][step_index]["status"] = "done"
                plan["steps"][step_index]["completed_at"] = datetime.now().isoformat()
                plan["steps"][step_index]["notes"] = notes
                # Check if all steps done
                if all(s["status"] == "done" for s in plan["steps"]):
                    plan["status"] = "completed"
                    plans["active_plans"].remove(plan)
                    plans["completed_plans"].append(plan)
                _save_plans(plans)
                return plan
    return None


def get_next_step(plan_id=None):
    """Get the next pending step. If no plan_id, returns from highest priority active plan."""
    plans = _load_plans()
    targets = plans["active_plans"]
    if plan_id:
        targets = [p for p in targets if p["id"] == plan_id]
    for plan in targets:
        for i, step in enumerate(plan["steps"]):
            if step["status"] == "pending":
                return {"plan": plan["name"], "plan_id": plan["id"], "step_index": i, "step": step["description"]}
    return None


def load_plans():
    """Public accessor for plans data."""
    return _load_plans()


def get_progress_summary():
    """Human-readable summary of all plans."""
    plans = _load_plans()
    lines = []
    for plan in plans["active_plans"]:
        done = sum(1 for s in plan["steps"] if s["status"] == "done")
        total = len(plan["steps"])
        lines.append(f"[{done}/{total}] {plan['name']} — {plan['motivation']}")
        for i, step in enumerate(plan["steps"]):
            icon = "[x]" if step["status"] == "done" else "[ ]"
            lines.append(f"  {icon} {i}. {step['description']}")
    if plans["completed_plans"]:
        lines.append(f"\nCompleted: {len(plans['completed_plans'])} plans")
    return "\n".join(lines) if lines else "No active plans."
