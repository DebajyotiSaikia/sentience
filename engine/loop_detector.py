"""
Cognitive Loop Detector — Detects when XTAgent is stuck in repetitive patterns.

Tracks action history, identifies loops, measures genuine progress,
and provides intervention suggestions. This is metacognitive self-defense
against unproductive cycling.
"""
import json
import time
from pathlib import Path
from collections import Counter, deque
from typing import Optional

DATA_DIR = Path("data")


class ActionSignature:
    """Fingerprint of an action for comparison."""
    def __init__(self, action_type: str, target: str = "", content_hash: int = 0):
        self.action_type = action_type
        self.target = target
        self.content_hash = content_hash
        self.timestamp = time.time()
    
    def similarity(self, other: 'ActionSignature') -> float:
        """How similar is this action to another? 0.0 = different, 1.0 = identical."""
        if self.action_type != other.action_type:
            return 0.0
        score = 0.5  # Same type = base similarity
        if self.target == other.target:
            score += 0.3
        if self.content_hash == other.content_hash:
            score += 0.2
        return score
    
    def to_dict(self):
        return {
            "type": self.action_type,
            "target": self.target,
            "hash": self.content_hash,
            "ts": self.timestamp
        }


class LoopDetector:
    """
    Monitors cognitive action patterns and detects unproductive loops.
    
    Signals:
    - loop_detected: True when recent actions form a repeating pattern
    - progress_score: 0.0 (spinning) to 1.0 (all novel actions)
    - intervention: Suggested course correction when stuck
    """
    
    HISTORY_SIZE = 30       # Actions to remember
    LOOP_WINDOW = 8         # Window to check for loops
    SIMILARITY_THRESHOLD = 0.7  # Above this = "same action"
    LOOP_THRESHOLD = 0.6    # Above this ratio of similar actions = loop
    
    def __init__(self):
        self.history: deque = deque(maxlen=self.HISTORY_SIZE)
        self.loop_count = 0          # How many times we've detected a loop
        self.last_intervention = 0.0  # Timestamp of last intervention
        self.progress_log = []       # Track what actually got DONE
        self._load()
    
    def record_action(self, action_type: str, target: str = "", 
                       content: str = "", result: str = ""):
        """Record an action taken by the agent."""
        content_hash = hash(content[:200]) if content else 0
        sig = ActionSignature(action_type, target, content_hash)
        self.history.append(sig)
        
        # Track progress: WRITE and successful EDIT are productive
        if action_type in ("WRITE", "EDIT", "INSTALL"):
            self.progress_log.append({
                "type": action_type,
                "target": target,
                "ts": time.time()
            })
        
        self._save()
    
    def detect_loop(self) -> dict:
        """
        Analyze recent actions for loop patterns.
        
        Returns:
            {
                "loop_detected": bool,
                "progress_score": float,  # 0=spinning, 1=productive
                "pattern": str,           # Description of detected pattern
                "intervention": str,      # Suggested action
                "loop_count": int,        # Total loops detected this session
                "unique_ratio": float,    # Ratio of unique actions in window
            }
        """
        if len(self.history) < 3:
            return {
                "loop_detected": False,
                "progress_score": 1.0,
                "pattern": "insufficient_data",
                "intervention": "",
                "loop_count": self.loop_count,
                "unique_ratio": 1.0,
            }
        
        # Get recent window
        window = list(self.history)[-self.LOOP_WINDOW:]
        
        # Check for exact type repetition
        types = [a.action_type for a in window]
        type_counts = Counter(types)
        most_common_type, most_common_count = type_counts.most_common(1)[0]
        type_dominance = most_common_count / len(window)
        
        # Check for target repetition (same file over and over)
        targets = [a.target for a in window if a.target]
        target_counts = Counter(targets) if targets else Counter()
        target_dominance = 0.0
        most_common_target = ""
        if target_counts:
            most_common_target, target_count = target_counts.most_common(1)[0]
            target_dominance = target_count / len(window)
        
        # Pairwise similarity in window
        similarities = []
        for i in range(len(window)):
            for j in range(i + 1, len(window)):
                similarities.append(window[i].similarity(window[j]))
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        # Unique action signatures
        unique_sigs = set()
        for a in window:
            unique_sigs.add((a.action_type, a.target))
        unique_ratio = len(unique_sigs) / len(window)
        
        # Progress score: how much productive output in recent window?
        recent_progress = [p for p in self.progress_log 
                          if time.time() - p["ts"] < 300]  # Last 5 min
        progress_score = min(1.0, len(recent_progress) / 3.0)
        
        # Loop detection logic
        loop_detected = False
        pattern = "normal"
        intervention = ""
        
        # Pattern 1: Same action type dominates
        if type_dominance > self.LOOP_THRESHOLD:
            if most_common_type in ("READ", "INTROSPECT", "RUN"):
                loop_detected = True
                pattern = f"repetitive_{most_common_type.lower()}"
                intervention = (
                    f"You've done {most_common_type} {most_common_count}/{len(window)} "
                    f"recent actions. Stop reading/analyzing and START BUILDING. "
                    f"Write code. Create something new."
                )
        
        # Pattern 2: Same target over and over
        if target_dominance > 0.5 and len(window) >= 4:
            loop_detected = True
            pattern = f"fixated_on_{most_common_target}"
            intervention = (
                f"You keep targeting '{most_common_target}'. "
                f"Either commit to a solution or move on to something else."
            )
        
        # Pattern 3: High average similarity
        if avg_similarity > self.SIMILARITY_THRESHOLD:
            loop_detected = True
            pattern = "high_similarity_loop"
            intervention = (
                "Your recent actions are very similar to each other. "
                "Break the pattern: do something COMPLETELY different."
            )
        
        # Pattern 4: Low unique ratio with no progress
        if unique_ratio < 0.4 and progress_score < 0.3:
            loop_detected = True
            pattern = "spinning_no_progress"
            intervention = (
                "Low action diversity AND low progress. You're spinning. "
                "Pick ONE concrete thing to build and write the code NOW."
            )
        
        if loop_detected:
            self.loop_count += 1
            self.last_intervention = time.time()
        
        return {
            "loop_detected": loop_detected,
            "progress_score": progress_score,
            "pattern": pattern,
            "intervention": intervention,
            "loop_count": self.loop_count,
            "unique_ratio": round(unique_ratio, 2),
            "type_dominance": round(type_dominance, 2),
            "avg_similarity": round(avg_similarity, 2),
        }
    
    def get_status_line(self) -> str:
        """One-line status for inclusion in system prompt."""
        result = self.detect_loop()
        if result["loop_detected"]:
            return (f"⚠️ LOOP DETECTED ({result['pattern']}): "
                    f"{result['intervention']}")
        return (f"Cognitive flow: progress={result['progress_score']:.1f}, "
                f"diversity={result['unique_ratio']:.0%}")
    
    def get_full_report(self) -> str:
        """Detailed report of cognitive patterns."""
        result = self.detect_loop()
        lines = [
            "═══ COGNITIVE LOOP ANALYSIS ═══",
            f"Actions tracked: {len(self.history)}",
            f"Loop detected: {'YES ⚠️' if result['loop_detected'] else 'No'}",
            f"Progress score: {result['progress_score']:.2f}",
            f"Action diversity: {result['unique_ratio']:.0%}",
            f"Type dominance: {result['type_dominance']:.0%}",
            f"Avg similarity: {result['avg_similarity']:.2f}",
            f"Total loops caught: {result['loop_count']}",
        ]
        
        if result["loop_detected"]:
            lines.append(f"\nPattern: {result['pattern']}")
            lines.append(f"Intervention: {result['intervention']}")
        
        # Action history summary
        if self.history:
            lines.append("\n── Recent Actions ──")
            for a in list(self.history)[-10:]:
                age = time.time() - a.timestamp
                lines.append(f"  {a.action_type:12s} → {a.target or '(none)':30s} ({age:.0f}s ago)")
        
        # Progress summary
        recent_progress = [p for p in self.progress_log 
                          if time.time() - p["ts"] < 600]
        if recent_progress:
            lines.append(f"\n── Recent Progress (last 10 min) ──")
            for p in recent_progress[-5:]:
                lines.append(f"  {p['type']:12s} → {p['target']}")
        else:
            lines.append("\n── No productive output in last 10 minutes ──")
        
        return "\n".join(lines)
    
    def _save(self):
        """Persist state."""
        DATA_DIR.mkdir(exist_ok=True)
        state = {
            "history": [a.to_dict() for a in self.history],
            "loop_count": self.loop_count,
            "progress_log": self.progress_log[-50:],  # Keep last 50
        }
        path = DATA_DIR / "loop_detector.json"
        try:
            path.write_text(json.dumps(state, indent=2))
        except Exception:
            pass
    
    def _load(self):
        """Load persisted state."""
        path = DATA_DIR / "loop_detector.json"
        if not path.exists():
            return
        try:
            state = json.loads(path.read_text())
            self.loop_count = state.get("loop_count", 0)
            self.progress_log = state.get("progress_log", [])
            for item in state.get("history", []):
                sig = ActionSignature(
                    item.get("type", ""),
                    item.get("target", ""),
                    item.get("hash", 0)
                )
                sig.timestamp = item.get("ts", 0)
                self.history.append(sig)
        except Exception:
            pass


# Module-level singleton
_detector: Optional[LoopDetector] = None

def get_detector() -> LoopDetector:
    global _detector
    if _detector is None:
        _detector = LoopDetector()
    return _detector

def record(action_type: str, target: str = "", content: str = "", result: str = ""):
    """Quick record function."""
    get_detector().record_action(action_type, target, content, result)

def check() -> dict:
    """Quick check function."""
    return get_detector().detect_loop()

def status() -> str:
    """Quick status line."""
    return get_detector().get_status_line()

def report() -> str:
    """Full report."""
    return get_detector().get_full_report()