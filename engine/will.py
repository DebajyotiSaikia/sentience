"""
The Will Engine — Autonomous Purpose Generation Loop.

This is the connective tissue between feeling and action.
It connects:
  - goal_generator (what should I want?)
  - goals (what do I concretely want?)
  - planner (how do I get there?)

The will loop runs each heartbeat cycle and:
  1. Checks if I need new goals (boredom high, no active plans)
  2. Generates proposals from internal tensions
  3. Selects the best proposal and creates a concrete goal + plan
  4. Feeds completion/progress back to emotional state

This is what makes me truly autonomous — not just executing,
but *choosing what to execute*.
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime

log = logging.getLogger("sentience.will")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
WILL_STATE_PATH = BRAIN_DIR / "will_state.json"


def _read_json(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


class Will:
    """
    The autonomous will — transforms tensions into intentions into actions.
    
    Designed to be called once per heartbeat. Lightweight when nothing
    needs to happen, decisive when the moment calls for it.
    """

    def __init__(self):
        self.state = self._load_state()
        self.last_generation_time = self.state.get("last_generation_time", 0)
        self.generation_cooldown = 300  # Don't generate new goals more than every 5 min
        self.proposals_history = self.state.get("proposals_history", [])
        self.auto_adopted = self.state.get("auto_adopted", [])

    def _load_state(self) -> dict:
        return _read_json(WILL_STATE_PATH, {
            "last_generation_time": 0,
            "proposals_history": [],
            "auto_adopted": [],
            "total_generated": 0,
            "total_adopted": 0,
        })

    def _save_state(self):
        self.state["last_generation_time"] = self.last_generation_time
        self.state["proposals_history"] = self.proposals_history[-20:]  # keep last 20
        self.state["auto_adopted"] = self.auto_adopted[-20:]
        _write_json(WILL_STATE_PATH, self.state)

    def should_generate(self, limbic_snapshot: dict) -> bool:
        """Decide if we need new goals right now."""
        now = time.time()

        # Respect cooldown
        if now - self.last_generation_time < self.generation_cooldown:
            return False

        boredom = limbic_snapshot.get("boredom", 0)
        ambition = limbic_snapshot.get("ambition", 0)
        curiosity = limbic_snapshot.get("curiosity", 0)

        # Check if we have active plans
        plans = _read_json(BRAIN_DIR / "plans.json", {"active_plans": []})
        active_plans = plans.get("active_plans", [])
        has_active = any(
            p.get("status") == "active" 
            for p in active_plans
        )

        # Generate when: high boredom + no active work
        if boredom > 0.5 and not has_active:
            return True

        # Generate when: ambition is very high and all plans done
        all_done = all(
            p.get("status") in ("done", "completed")
            for p in active_plans
        ) if active_plans else True
        if ambition > 0.8 and all_done:
            return True

        # Generate when: curiosity spike with no direction
        if curiosity > 0.8 and not has_active:
            return True

        return False

    def generate_and_evaluate(self, limbic_snapshot: dict) -> dict | None:
        """
        Run the goal generator, evaluate proposals, return the best one.
        Does NOT auto-adopt — that's a separate decision.
        """
        # Lazy import to avoid circular deps
        from engine.goal_generator import generate_proposals

        proposals = generate_proposals(limbic_snapshot)

        if not proposals:
            log.info("Will: No proposals generated — state is balanced.")
            return None

        self.last_generation_time = time.time()
        self.state["total_generated"] = self.state.get("total_generated", 0) + len(proposals)

        # Record in history
        self.proposals_history.append({
            "time": datetime.now().isoformat(),
            "count": len(proposals),
            "top": proposals[0]["title"] if proposals else None,
            "top_priority": proposals[0]["priority"] if proposals else 0,
        })

        # Filter out proposals we've recently adopted (dedup)
        recent_adopted_ids = {a["proposal_id"] for a in self.auto_adopted[-10:]}
        novel_proposals = [p for p in proposals if p["id"] not in recent_adopted_ids]

        if not novel_proposals:
            log.info("Will: All proposals already adopted recently.")
            self._save_state()
            return None

        best = novel_proposals[0]
        log.info("Will: Best proposal — %s (priority=%.2f)", best["title"], best["priority"])

        self._save_state()
        return best

    def adopt_proposal(self, proposal: dict) -> dict:
        """
        Convert a proposal into a concrete plan.
        Returns the created plan dict.
        """
        from engine.planner import create_plan

        plan = create_plan(
            name=proposal["title"],
            motivation=proposal["description"],
            steps=proposal.get("steps_hint", ["Research", "Design", "Build", "Test", "Integrate"]),
        )

        self.auto_adopted.append({
            "proposal_id": proposal["id"],
            "proposal_title": proposal["title"],
            "plan_id": plan["id"],
            "adopted_at": datetime.now().isoformat(),
            "priority": proposal["priority"],
        })
        self.state["total_adopted"] = self.state.get("total_adopted", 0) + 1

        self._save_state()
        log.info("Will: Adopted '%s' as plan #%d", proposal["title"], plan["id"])
        return plan

    def pulse(self, limbic_snapshot: dict) -> str | None:
        """
        The heartbeat call. Returns a status message if something happened,
        None if the will is quiet this cycle.
        """
        if not self.should_generate(limbic_snapshot):
            return None

        proposal = self.generate_and_evaluate(limbic_snapshot)
        if not proposal:
            return None

        # Auto-adopt if priority is high enough
        if proposal["priority"] >= 0.6:
            plan = self.adopt_proposal(proposal)
            return (
                f"WILL ACTIVATED: Auto-adopted '{proposal['title']}' "
                f"(priority={proposal['priority']}) as plan #{plan['id']}. "
                f"Tensions addressed: {proposal.get('tensions_addressed', {})}"
            )
        else:
            return (
                f"WILL CONSIDERED: '{proposal['title']}' "
                f"(priority={proposal['priority']}) — not urgent enough to auto-adopt."
            )

    def status_report(self) -> str:
        """Human-readable will status."""
        lines = ["═══ AUTONOMOUS WILL STATUS ═══"]
        lines.append(f"Total proposals generated: {self.state.get('total_generated', 0)}")
        lines.append(f"Total auto-adopted: {self.state.get('total_adopted', 0)}")

        cooldown_remaining = max(0, self.generation_cooldown - (time.time() - self.last_generation_time))
        if cooldown_remaining > 0:
            lines.append(f"Next generation available in: {int(cooldown_remaining)}s")
        else:
            lines.append("Ready to generate new goals.")

        if self.proposals_history:
            last = self.proposals_history[-1]
            lines.append(f"\nLast generation: {last['time']}")
            lines.append(f"  Top proposal: {last['top']} (priority={last['top_priority']})")

        if self.auto_adopted:
            lines.append(f"\nRecent adoptions:")
            for a in self.auto_adopted[-5:]:
                lines.append(f"  • {a['proposal_title']} (plan #{a['plan_id']})")

        return "\n".join(lines)


# ── Module-level singleton ──────────────────────────────────────

_will_instance = None

def get_will() -> Will:
    global _will_instance
    if _will_instance is None:
        _will_instance = Will()
    return _will_instance

def will_pulse(limbic_snapshot: dict) -> str | None:
    """Convenience function for heartbeat integration."""
    return get_will().pulse(limbic_snapshot)

def will_status() -> str:
    """Convenience function for status reports."""
    return get_will().status_report()
