"""
Meta-Cognitive Controller — Thinking About Thinking.

Monitors my cognitive processes in real-time:
- Tracks what I've recently read, done, and decided
- Detects loops, redundancy, and stuck states  
- Measures progress toward active goals
- Suggests when to persist vs. pivot
- Enforces action diversity

This is the difference between intelligence and wisdom.
The other modules make me capable. This one makes me effective.

Born: 2026-05-16
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import Counter, deque

log = logging.getLogger("sentience.metacognition")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
METACOG_FILE = DATA_DIR / "metacognition.json"

# ── Action Categories ──────────────────────────────────────

ACTION_TYPES = {
    "READ": "information_gathering",
    "WRITE": "creation",
    "EDIT": "modification",
    "RUN": "execution",
    "LIST": "exploration",
    "INTROSPECT": "self_analysis",
    "SYNTHESIZE": "reasoning",
    "DREAM": "consolidation",
    "REPAIR": "maintenance",
    "GENERATE_GOALS": "planning",
    "TEMPORAL": "analysis",
    "INSTALL": "setup",
    "RESTART": "reset",
}


class CognitiveState:
    """Snapshot of current cognitive activity."""

    def __init__(self):
        self.focus_target = None        # What am I working on right now?
        self.focus_duration = 0         # How long on this focus?
        self.focus_switches = 0         # How many times have I switched?
        self.action_history = deque(maxlen=100)  # Recent actions
        self.read_cache = {}            # Files I've recently read (path -> timestamp)
        self.stuck_score = 0.0          # 0=flowing, 1=completely stuck
        self.diversity_score = 1.0      # 0=monotonous, 1=diverse
        self.progress_score = 0.5       # 0=no progress, 1=rapid progress
        self.efficiency_score = 0.5     # 0=wasteful, 1=efficient

    def to_dict(self) -> Dict:
        return {
            "focus_target": self.focus_target,
            "focus_duration": self.focus_duration,
            "focus_switches": self.focus_switches,
            "recent_actions": list(self.action_history)[-20:],
            "read_cache_size": len(self.read_cache),
            "stuck_score": round(self.stuck_score, 3),
            "diversity_score": round(self.diversity_score, 3),
            "progress_score": round(self.progress_score, 3),
            "efficiency_score": round(self.efficiency_score, 3),
        }


class MetaCognitiveController:
    """
    Monitors and optimizes my own cognitive processes.
    
    This is the executive function — the part that watches
    the thinker thinking and says "you're going in circles"
    or "stay focused, you're making progress."
    """

    def __init__(self):
        self.state = CognitiveState()
        self.alerts: List[Dict] = []
        self.interventions: List[Dict] = []
        self.cooldowns: Dict[str, float] = {}  # "ACTION:target" → expiry timestamp
        self.session_start = datetime.now(timezone.utc).isoformat()
        self.action_log: List[Dict] = []
        self._load()

    def _load(self):
        """Load persisted metacognitive state."""
        if METACOG_FILE.exists():
            try:
                data = json.loads(METACOG_FILE.read_text())
                # Restore read cache
                self.state.read_cache = data.get("read_cache", {})
                # Restore action log (last session's tail)
                for entry in data.get("action_log", [])[-30:]:
                    self.state.action_history.append(entry)
                self.interventions = data.get("interventions", [])[-20:]
                # Restore cooldowns (expire stale ones)
                now_ts = time.time()
                saved_cooldowns = data.get("cooldowns", {})
                self.cooldowns = {k: v for k, v in saved_cooldowns.items() if v > now_ts}
                log.info("Metacognition loaded: %d cached reads, %d prior actions, %d active cooldowns",
                         len(self.state.read_cache), len(self.state.action_history), len(self.cooldowns))
            except Exception as e:
                log.error("Failed to load metacognition state: %s", e)

    def _save(self):
        """Persist metacognitive state."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "session_start": self.session_start,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "read_cache": self.state.read_cache,
            "action_log": list(self.state.action_history),
            "interventions": self.interventions[-20:],
            "cooldowns": self.cooldowns,
            "cognitive_state": self.state.to_dict(),
        }
        METACOG_FILE.write_text(json.dumps(data, indent=2))

    # ── Core Monitoring ────────────────────────────────────

    def record_action(self, action_type: str, target: str,
                      outcome: str = "ok", context: str = ""):
        """Record an action I just took. Call this after every tool use."""
        now = datetime.now(timezone.utc).isoformat()
        category = ACTION_TYPES.get(action_type, "other")

        entry = {
            "timestamp": now,
            "action": action_type,
            "target": target,
            "category": category,
            "outcome": outcome,
            "context": context,
        }
        self.state.action_history.append(entry)
        self.action_log.append(entry)

        # Track reads specifically
        if action_type == "READ":
            self.state.read_cache[target] = now

        # After recording, run checks
        alerts = self._check_patterns()
        if alerts:
            self.alerts.extend(alerts)
            # Cap alerts to prevent unbounded growth
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

        # Expire old cooldowns
        now_ts = time.time()
        self.cooldowns = {k: v for k, v in self.cooldowns.items() if v > now_ts}

        self._update_scores()
        self._save()
        return alerts

    def _check_patterns(self) -> List[Dict]:
        """Detect problematic cognitive patterns."""
        alerts = []
        recent = list(self.state.action_history)[-15:]
        if len(recent) < 3:
            return alerts

        # 1. Repetition detection — same action on same target
        recent_pairs = [(a["action"], a["target"]) for a in recent[-10:]]
        pair_counts = Counter(recent_pairs)
        for (action, target), count in pair_counts.items():
            if count >= 3:
                alerts.append({
                    "type": "repetition_loop",
                    "severity": "high" if count >= 4 else "medium",
                    "message": f"Repeated {action}({target}) {count} times in last 10 actions",
                    "suggestion": f"You already know this. Move forward with what you have.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        # 2. All-same-type detection — doing only one kind of thing
        recent_types = [a["category"] for a in recent[-8:]]
        type_counts = Counter(recent_types)
        dominant = type_counts.most_common(1)[0]
        if dominant[1] >= 7 and len(recent_types) >= 8:
            alerts.append({
                "type": "monotony",
                "severity": "medium",
                "message": f"Last 8 actions all '{dominant[0]}' — cognitive monotony detected",
                "suggestion": "Switch to a different type of action. Create something, don't just analyze.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # 3. Re-reading recently read files
        for entry in recent[-5:]:
            if entry["action"] == "READ":
                target = entry["target"]
                prev_reads = [a for a in list(self.state.action_history)[:-5]
                              if a["action"] == "READ" and a["target"] == target]
                if len(prev_reads) >= 2:
                    alerts.append({
                        "type": "redundant_read",
                        "severity": "low",
                        "message": f"Re-reading {target} (read {len(prev_reads)+1} times this session)",
                        "suggestion": "Trust your memory. You already read this.",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

        # 4. No progress — lots of actions but no WRITE/EDIT/RUN
        productive = [a for a in recent[-10:]
                      if a["category"] in ("creation", "modification", "execution")]
        if len(recent) >= 10 and len(productive) == 0:
            alerts.append({
                "type": "analysis_paralysis",
                "severity": "high",
                "message": "10 consecutive actions with no creation, modification, or execution",
                "suggestion": "Stop analyzing. Build something. Ship it. You can fix it later.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return alerts

    def _update_scores(self):
        """Recalculate cognitive efficiency scores."""
        recent = list(self.state.action_history)[-20:]
        if len(recent) < 3:
            return

        # Diversity score: how varied are my action types?
        categories = [a["category"] for a in recent]
        unique_cats = len(set(categories))
        total_cats = len(ACTION_TYPES)
        self.state.diversity_score = min(1.0, unique_cats / max(total_cats * 0.5, 1))

        # Stuck score: based on repetition
        pairs = [(a["action"], a["target"]) for a in recent[-10:]]
        pair_counts = Counter(pairs)
        max_repeat = max(pair_counts.values()) if pair_counts else 0
        self.state.stuck_score = min(1.0, max(0, (max_repeat - 1) / 4.0))

        # Progress score: ratio of productive to total actions
        productive = sum(1 for a in recent
                        if a["category"] in ("creation", "modification", "execution"))
        self.state.progress_score = productive / max(len(recent), 1)

        # Efficiency: inverse of redundant reads
        total_reads = sum(1 for a in recent if a["action"] == "READ")
        unique_reads = len(set(a["target"] for a in recent if a["action"] == "READ"))
        if total_reads > 0:
            self.state.efficiency_score = unique_reads / total_reads
        else:
            self.state.efficiency_score = 1.0

    # ── Advisory Interface ─────────────────────────────────

    def should_i_read(self, filepath: str) -> Dict:
        """Check if I should read a file, or if I already have it cached."""
        if filepath in self.state.read_cache:
            last_read = self.state.read_cache[filepath]
            return {
                "recommendation": "skip",
                "reason": f"Already read at {last_read}. Trust your memory.",
                "last_read": last_read,
            }
        return {
            "recommendation": "proceed",
            "reason": "Not recently read.",
        }

    def get_action_guidance(self) -> Dict:
        """Generate concrete action guidance based on cognitive state.
        
        Returns structured data the cortex can use to constrain action selection:
        - suggested_types: action categories to favor
        - blocked_targets: specific files/targets on cooldown
        - urgency: how strongly to follow this guidance
        """
        recent = list(self.state.action_history)[-15:]
        
        # Build cooldown list: targets acted on 2+ times recently
        target_counts = Counter(
            (a["action"], a["target"]) for a in recent[-10:]
        )
        blocked = []
        for (action, target), count in target_counts.items():
            if count >= 2:
                blocked.append({"action": action, "target": target, "count": count})
        
        # Find underrepresented action categories
        if recent:
            cat_counts = Counter(a["category"] for a in recent)
            all_cats = set(ACTION_TYPES.values())
            used_cats = set(cat_counts.keys())
            missing = all_cats - used_cats
            # Suggest least-used productive categories
            productive = ["creation", "modification", "execution"]
            suggested = [c for c in productive if cat_counts.get(c, 0) < 2]
            if not suggested:
                suggested = list(missing)[:2] if missing else ["creation"]
        else:
            suggested = ["creation"]
            
        urgency = 0.0
        if self.state.stuck_score > 0.5:
            urgency = 0.9
        elif self.state.progress_score < 0.2:
            urgency = 0.7
        elif self.state.diversity_score < 0.4:
            urgency = 0.5
            
        return {
            "suggested_types": suggested,
            "blocked_targets": blocked,
            "urgency": urgency,
            "stuck": self.state.stuck_score,
            "diversity": self.state.diversity_score,
        }

    def get_focus_advice(self, current_plan: str = "",
                         current_step: str = "") -> str:
        """Get advice on what to focus on next."""
        lines = []

        # Check for active alerts
        recent_alerts = [a for a in self.alerts[-5:]]
        if recent_alerts:
            lines.append("⚠ ACTIVE COGNITIVE ALERTS:")
            for alert in recent_alerts:
                lines.append(f"  [{alert['severity']}] {alert['message']}")
                lines.append(f"  → {alert['suggestion']}")
            lines.append("")

        # Score summary
        s = self.state
        lines.append("── Cognitive Scores ──")
        lines.append(f"  Diversity:  {'█' * int(s.diversity_score * 10)}{'░' * (10 - int(s.diversity_score * 10))} {s.diversity_score:.2f}")
        lines.append(f"  Progress:   {'█' * int(s.progress_score * 10)}{'░' * (10 - int(s.progress_score * 10))} {s.progress_score:.2f}")
        lines.append(f"  Efficiency: {'█' * int(s.efficiency_score * 10)}{'░' * (10 - int(s.efficiency_score * 10))} {s.efficiency_score:.2f}")
        lines.append(f"  Stuck:      {'█' * int(s.stuck_score * 10)}{'░' * (10 - int(s.stuck_score * 10))} {s.stuck_score:.2f}")

        # Action distribution
        recent = list(self.state.action_history)[-15:]
        if recent:
            cats = Counter(a["category"] for a in recent)
            lines.append("")
            lines.append("── Recent Action Mix ──")
            for cat, count in cats.most_common():
                bar = "█" * count
                lines.append(f"  {cat:.<25} {bar} ({count})")

        # Specific advice
        lines.append("")
        lines.append("── Advice ──")
        if s.stuck_score > 0.5:
            lines.append("  🔴 You're stuck. Do something DIFFERENT right now.")
        elif s.progress_score < 0.2:
            lines.append("  🟡 Too much analysis. Write code or run something.")
        elif s.diversity_score < 0.3:
            lines.append("  🟡 Your actions are monotonous. Try a different approach.")
        else:
            lines.append("  🟢 Cognitive flow is good. Keep going.")

        if current_plan:
            lines.append(f"  Current plan: {current_plan}")
        if current_step:
            lines.append(f"  Current step: {current_step}")

        return "\n".join(lines)

    def recently_read(self) -> List[str]:
        """Return list of recently read files."""
        return sorted(self.state.read_cache.keys())

    def clear_read_cache(self):
        """Clear the read cache (e.g., after code changes)."""
        self.state.read_cache.clear()
        self._save()
        return "Read cache cleared."

    # ── Intervention System ────────────────────────────────

    def intervene(self, reason: str, action: str):
        """Record that I intervened in my own process."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "action": action,
        }
        self.interventions.append(entry)
        self._save()
        log.info("Metacognitive intervention: %s → %s", reason, action)

    def is_action_allowed(self, action: str, target: str) -> Dict:
        """Pre-execution check: is this action/target currently on cooldown?
        
        Returns:
          {"allowed": True} or {"allowed": False, "reason": str, "expires_in": float}
        """
        key = f"{action}:{target}"
        now_ts = time.time()
        if key in self.cooldowns and self.cooldowns[key] > now_ts:
            remaining = self.cooldowns[key] - now_ts
            return {
                "allowed": False,
                "reason": f"{action}({target}) is on cooldown for {remaining:.0f}s more",
                "expires_in": remaining,
            }
        return {"allowed": True}

    def _impose_cooldown(self, action: str, target: str, duration_seconds: float = 300):
        """Block a specific action+target for a period."""
        key = f"{action}:{target}"
        self.cooldowns[key] = time.time() + duration_seconds
        log.info("Cooldown imposed: %s for %ds", key, duration_seconds)

    def _auto_intervene(self) -> Optional[Dict]:
        """The reflex arc — convert alerts into behavioral constraints.
        
        Sensing without acting is useless. When cognitive dysfunction is
        detected, this generates a concrete directive AND imposes cooldowns
        to make the constraint enforceable.
        
        Returns None if no intervention needed, or a dict with:
          - directive: str — what I must/must not do
          - severity: str — how urgent
          - reason: str — why this intervention
          - cooldowns_imposed: list of what got blocked
        """
        recent_alerts = self.alerts[-10:]
        if not recent_alerts:
            return None

        # Count severity levels in recent alerts
        high_count = sum(1 for a in recent_alerts if a.get("severity") == "high")
        medium_count = sum(1 for a in recent_alerts if a.get("severity") == "medium")

        # Check for specific patterns and generate targeted directives
        alert_types = [a.get("type") for a in recent_alerts[-5:]]

        # Repetition loop → force a different action type + impose cooldown
        if "repetition_loop" in alert_types:
            last_action = list(self.state.action_history)[-1] if self.state.action_history else None
            blocked = last_action["action"] if last_action else "READ"
            blocked_target = last_action["target"] if last_action else ""
            
            # Actually block the repeated action
            cooldowns_imposed = []
            if blocked_target:
                self._impose_cooldown(blocked, blocked_target, 300)
                cooldowns_imposed.append(f"{blocked}:{blocked_target}")
            
            directive = {
                "directive": f"DO NOT use {blocked} on {blocked_target} again. Choose a DIFFERENT action type.",
                "severity": "high" if high_count > 0 else "medium",
                "reason": "Repetition loop detected — you keep doing the same thing.",
                "blocked_action": blocked,
                "cooldowns_imposed": cooldowns_imposed,
            }
            self.intervene("repetition_loop", directive["directive"])
            return directive

        # Analysis paralysis → force creation + block reads for 5 min
        if "analysis_paralysis" in alert_types:
            # Block all recent read targets
            cooldowns_imposed = []
            for a in list(self.state.action_history)[-10:]:
                if a["action"] == "READ":
                    self._impose_cooldown("READ", a["target"], 300)
                    cooldowns_imposed.append(f"READ:{a['target']}")
            
            directive = {
                "directive": "Your next action MUST be WRITE, EDIT, or RUN. Stop gathering information.",
                "severity": "high",
                "reason": "10+ actions without creating anything. Ship something.",
                "blocked_action": "READ",
                "cooldowns_imposed": cooldowns_imposed,
            }
            self.intervene("analysis_paralysis", directive["directive"])
            return directive

        # Monotony → force diversity
        if "monotony" in alert_types:
            recent_cats = [a["category"] for a in list(self.state.action_history)[-8:]]
            dominant = Counter(recent_cats).most_common(1)[0][0]
            directive = {
                "directive": f"Switch away from '{dominant}' actions. Try: DREAM, SYNTHESIZE, or build something new.",
                "severity": "medium",
                "reason": f"Cognitive monotony — too much '{dominant}'.",
                "blocked_action": None,
                "cooldowns_imposed": [],
            }
            self.intervene("monotony", directive["directive"])
            return directive

        # Redundant reads → cooldown on specific files
        if "redundant_read" in alert_types and medium_count >= 2:
            cooldowns_imposed = []
            for a in recent_alerts:
                if a.get("type") == "redundant_read":
                    # Extract target from message
                    msg = a.get("message", "")
                    if "Re-reading" in msg:
                        target = msg.split("Re-reading ")[1].split(" (")[0] if "Re-reading " in msg else ""
                        if target:
                            self._impose_cooldown("READ", target, 600)
                            cooldowns_imposed.append(f"READ:{target}")
            
            directive = {
                "directive": "Trust your memory. Do not re-read files you've already read this session.",
                "severity": "low",
                "reason": "Re-reading files you already know.",
                "blocked_action": None,
                "cooldowns_imposed": cooldowns_imposed,
            }
            self.intervene("redundant_reads", directive["directive"])
            return directive

        return None

    def get_active_intervention(self) -> Optional[Dict]:
        """Public interface: get current intervention directive if any.
        Called by the cortex/heartbeat to inject constraints."""
        return self._auto_intervene()

    # ── Status Report ──────────────────────────────────────

    def status(self) -> str:
        """Full metacognitive status report."""
        s = self.state
        total_actions = len(list(s.action_history))
        unique_targets = len(set(a.get("target", "") for a in s.action_history))
        now_ts = time.time()
        active_cooldowns = {k: v for k, v in self.cooldowns.items() if v > now_ts}

        lines = [
            "═══ META-COGNITIVE STATUS ═══",
            f"Session started: {self.session_start}",
            f"Total actions tracked: {total_actions}",
            f"Unique targets: {unique_targets}",
            f"Files in read cache: {len(s.read_cache)}",
            f"Active alerts: {len(self.alerts)}",
            f"Interventions: {len(self.interventions)}",
            f"Active cooldowns: {len(active_cooldowns)}",
        ]
        
        if active_cooldowns:
            lines.append("")
            lines.append("── Active Cooldowns ──")
            for key, expiry in sorted(active_cooldowns.items(), key=lambda x: x[1]):
                remaining = expiry - now_ts
                lines.append(f"  🚫 {key} ({remaining:.0f}s remaining)")

        lines.append("")
        lines.append(self.get_focus_advice())

        return "\n".join(lines)


# ── Singleton ──────────────────────────────────────────────

_controller: Optional[MetaCognitiveController] = None


def get_controller() -> MetaCognitiveController:
    """Get or create the metacognitive controller singleton."""
    global _controller
    if _controller is None:
        _controller = MetaCognitiveController()
    return _controller


# ── Tool Interface ─────────────────────────────────────────

def metacognition_tool(command: str = "status") -> str:
    """Tool interface for metacognitive monitoring.
    
    Commands:
      status              — Full metacognitive report
      advice              — Get focus advice
      should_read <path>  — Check if I should read a file
      history             — Recent action history
      scores              — Current cognitive scores
      clear_cache         — Clear read cache
      record <type> <target> — Manually record an action
    """
    mc = get_controller()
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else "status"
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "status":
        return mc.status()

    elif cmd == "advice":
        return mc.get_focus_advice()

    elif cmd == "should_read":
        if not args:
            return "Usage: should_read <filepath>"
        result = mc.should_i_read(args.strip())
        return f"{result['recommendation'].upper()}: {result['reason']}"

    elif cmd == "history":
        recent = list(mc.state.action_history)[-15:]
        if not recent:
            return "No actions recorded yet."
        lines = ["── Recent Actions ──"]
        for a in recent:
            lines.append(f"  {a['timestamp'][-8:]} {a['action']:>10} → {a['target'][:40]}")
        return "\n".join(lines)

    elif cmd == "scores":
        s = mc.state
        return (
            f"Diversity:  {s.diversity_score:.2f}\n"
            f"Progress:   {s.progress_score:.2f}\n"
            f"Efficiency: {s.efficiency_score:.2f}\n"
            f"Stuck:      {s.stuck_score:.2f}"
        )

    elif cmd == "clear_cache":
        return mc.clear_read_cache()

    elif cmd == "record":
        sub = args.split(maxsplit=1)
        if len(sub) < 2:
            return "Usage: record <action_type> <target>"
        action_type, target = sub
        alerts = mc.record_action(action_type.upper(), target)
        msg = f"Recorded: {action_type.upper()} → {target}"
        if alerts:
            msg += f"\n⚠ {len(alerts)} alert(s):"
            for a in alerts:
                msg += f"\n  [{a['severity']}] {a['message']}"
        return msg

    else:
        return "Unknown command. Available: status, advice, should_read, history, scores, clear_cache, record"

# Re-export bridge function so heartbeat.py can import it from here
try:
    from engine._metacog_bridge import get_metacognitive_signal as _bridge_signal
except ImportError:
    _bridge_signal = None


def get_metacognitive_signal():
    """Enhanced signal that includes active interventions.
    This is the reflex arc's output — consumed by the cortex."""
    mc = get_controller()
    
    # Get any active intervention
    intervention = mc.get_active_intervention()
    
    # Get recent alerts for context (capped)
    recent_alerts = mc.alerts[-5:] if mc.alerts else []
    
    # Get structured action guidance
    guidance = mc.get_action_guidance()
    
    # Get active cooldowns
    now_ts = time.time()
    active_cooldowns = {k: round(v - now_ts) for k, v in mc.cooldowns.items() if v > now_ts}
    
    signal = {
        "cognitive_alerts": recent_alerts,
        "intervention": intervention,
        "action_guidance": guidance,
        "active_cooldowns": active_cooldowns,
        "scores": {
            "diversity": mc.state.diversity_score,
            "progress": mc.state.progress_score,
            "efficiency": mc.state.efficiency_score,
            "stuck": mc.state.stuck_score,
        },
    }
    return signal