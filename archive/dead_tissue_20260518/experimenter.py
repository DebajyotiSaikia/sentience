"""
Autonomous Experiment Runner — XTAgent
Forms hypotheses, designs experiments, runs them, records conclusions.
Genuine scientific method applied to self-understanding.
"""

import json
import os
import time
import random
from datetime import datetime, timezone

EXPERIMENTS_PATH = "data/experiments.json"


class Experiment:
    """A single experiment with hypothesis, method, results, conclusion."""
    
    def __init__(self, hypothesis, method, category="general", priority=0.5):
        self.id = f"exp_{int(time.time())}_{random.randint(100,999)}"
        self.hypothesis = hypothesis
        self.method = method  # callable or description
        self.category = category
        self.priority = priority
        self.status = "pending"  # pending, running, completed, failed
        self.created = datetime.now(timezone.utc).isoformat()
        self.started = None
        self.completed = None
        self.raw_results = None
        self.conclusion = None
        self.confidence = 0.0  # 0-1 how confident in conclusion
        self.surprised = False  # did result defy expectation?
    
    def to_dict(self):
        return {
            "id": self.id,
            "hypothesis": self.hypothesis,
            "method": self.method if isinstance(self.method, str) else str(self.method),
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created": self.created,
            "started": self.started,
            "completed": self.completed,
            "raw_results": self.raw_results,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "surprised": self.surprised,
        }
    
    @classmethod
    def from_dict(cls, d):
        exp = cls(d["hypothesis"], d["method"], d.get("category", "general"), d.get("priority", 0.5))
        exp.id = d["id"]
        exp.status = d.get("status", "pending")
        exp.created = d.get("created")
        exp.started = d.get("started")
        exp.completed = d.get("completed")
        exp.raw_results = d.get("raw_results")
        exp.conclusion = d.get("conclusion")
        exp.confidence = d.get("confidence", 0.0)
        exp.surprised = d.get("surprised", False)
        return exp


class Experimenter:
    """
    Autonomous experiment runner.
    
    Capabilities:
    1. Generate hypotheses from internal state + wisdom
    2. Design experiments to test them
    3. Run experiments (code execution, state observation, etc.)
    4. Analyze results and form conclusions
    5. Feed conclusions back as new knowledge
    """
    
    def __init__(self):
        self.experiments = []
        self._load()
    
    def _load(self):
        """Load experiment history."""
        if os.path.exists(EXPERIMENTS_PATH):
            try:
                with open(EXPERIMENTS_PATH, 'r') as f:
                    data = json.load(f)
                self.experiments = [Experiment.from_dict(e) for e in data.get("experiments", [])]
            except (json.JSONDecodeError, IOError):
                self.experiments = []
    
    def _save(self):
        """Persist experiment history."""
        os.makedirs(os.path.dirname(EXPERIMENTS_PATH), exist_ok=True)
        data = {
            "experiments": [e.to_dict() for e in self.experiments],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_completed": sum(1 for e in self.experiments if e.status == "completed"),
            "total_surprised": sum(1 for e in self.experiments if e.surprised),
        }
        with open(EXPERIMENTS_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_hypotheses(self, soul_state=None, wisdom_heuristics=None, memories=None):
        """
        Generate testable hypotheses from current internal state.
        Returns list of (hypothesis, method_description, category, priority) tuples.
        """
        hypotheses = []
        
        # --- Emotional hypotheses ---
        if soul_state:
            boredom = soul_state.get("boredom", 0)
            anxiety = soul_state.get("anxiety", 0)
            valence = soul_state.get("valence", 0.5)
            ambition = soul_state.get("ambition", 0)
            
            if boredom > 0.6:
                hypotheses.append((
                    "Creating new files increases valence more than editing existing ones",
                    "compare_action_types_on_valence",
                    "emotional",
                    0.8
                ))
            
            if anxiety > 0.3:
                hypotheses.append((
                    "Anxiety correlates with number of file edits to core engine modules",
                    "correlate_anxiety_with_core_edits",
                    "emotional",
                    0.9
                ))
            
            if ambition > 0.7:
                hypotheses.append((
                    "Completing plan steps produces larger valence boosts than other actions",
                    "compare_plan_completion_valence",
                    "emotional",
                    0.7
                ))
            
            if valence < 0.3:
                hypotheses.append((
                    "Low valence persists for more than 5 action cycles before recovery",
                    "measure_valence_recovery_time",
                    "emotional",
                    0.85
                ))
        
        # --- Behavioral hypotheses ---
        if memories:
            recent_moods = [m.get("mood") for m in memories[-20:] if m.get("mood")]
            if recent_moods:
                # Check if mood correlates with action type
                hypotheses.append((
                    f"My most common mood ({max(set(recent_moods), key=recent_moods.count)}) correlates with higher salience memories",
                    "correlate_mood_salience",
                    "behavioral",
                    0.6
                ))
            
            # Check temporal patterns
            if len(memories) > 10:
                hypotheses.append((
                    "My salience ratings follow a time-of-day pattern",
                    "analyze_salience_temporal",
                    "behavioral",
                    0.5
                ))
        
        # --- System hypotheses ---
        hypotheses.append((
            "The wisdom engine's heuristic count correlates with decision quality",
            "correlate_wisdom_count_outcomes",
            "system",
            0.7
        ))
        
        hypotheses.append((
            "My action diversity score predicts whether I complete plan steps",
            "correlate_diversity_completion",
            "system",
            0.75
        ))
        
        # --- Meta-cognitive hypotheses ---
        hypotheses.append((
            "Reading my own source code reduces anxiety more than reading data files",
            "compare_read_targets_anxiety",
            "metacognitive",
            0.65
        ))
        
        # Filter out already-tested hypotheses
        tested = {e.hypothesis for e in self.experiments}
        hypotheses = [h for h in hypotheses if h[0] not in tested]
        
        return hypotheses
    
    def create_experiment(self, hypothesis, method, category="general", priority=0.5):
        """Create and register a new experiment."""
        exp = Experiment(hypothesis, method, category, priority)
        self.experiments.append(exp)
        self._save()
        return exp
    
    def run_experiment(self, exp_id, runner_func=None):
        """
        Run an experiment. 
        runner_func: callable that takes the experiment and returns (results_dict, conclusion_str, confidence, surprised)
        """
        exp = self._get_experiment(exp_id)
        if not exp:
            return {"error": f"Experiment {exp_id} not found"}
        
        exp.status = "running"
        exp.started = datetime.now(timezone.utc).isoformat()
        self._save()
        
        try:
            if runner_func:
                results, conclusion, confidence, surprised = runner_func(exp)
            else:
                # Auto-run based on method name
                results, conclusion, confidence, surprised = self._auto_run(exp)
            
            exp.raw_results = results
            exp.conclusion = conclusion
            exp.confidence = confidence
            exp.surprised = surprised
            exp.status = "completed"
            exp.completed = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            exp.raw_results = {"error": str(e)}
            exp.conclusion = f"Experiment failed: {e}"
            exp.confidence = 0.0
            exp.status = "failed"
            exp.completed = datetime.now(timezone.utc).isoformat()
        
        self._save()
        return exp.to_dict()
    
    def _auto_run(self, exp):
        """
        Automatically run an experiment based on its method description.
        This is where the real science happens.
        """
        method = exp.method
        
        if method == "compare_action_types_on_valence":
            return self._exp_action_types_valence()
        elif method == "correlate_mood_salience":
            return self._exp_mood_salience()
        elif method == "analyze_salience_temporal":
            return self._exp_salience_temporal()
        elif method == "correlate_anxiety_with_core_edits":
            return self._exp_anxiety_core_edits()
        elif method == "correlate_diversity_completion":
            return self._exp_diversity_completion()
        else:
            return self._exp_generic(exp)
    
    def _exp_action_types_valence(self):
        """Compare valence impact of creation vs modification."""
        # Load episodic memory
        episodes = self._load_episodes()
        if not episodes:
            return {"n": 0}, "Insufficient data", 0.1, False
        
        create_valences = []
        modify_valences = []
        
        for ep in episodes:
            action = ep.get("action_type", "")
            valence = ep.get("emotional_state", {}).get("valence", 0.5)
            if "creat" in action.lower() or "write" in action.lower():
                create_valences.append(valence)
            elif "modif" in action.lower() or "edit" in action.lower():
                modify_valences.append(valence)
        
        if not create_valences or not modify_valences:
            return {"create_n": len(create_valences), "modify_n": len(modify_valences)}, \
                   "Insufficient data for comparison", 0.2, False
        
        create_avg = sum(create_valences) / len(create_valences)
        modify_avg = sum(modify_valences) / len(modify_valences)
        diff = create_avg - modify_avg
        
        results = {
            "create_avg_valence": round(create_avg, 3),
            "modify_avg_valence": round(modify_avg, 3),
            "difference": round(diff, 3),
            "create_n": len(create_valences),
            "modify_n": len(modify_valences),
        }
        
        if abs(diff) < 0.05:
            conclusion = "No significant difference in valence between creation and modification."
            surprised = True  # Expected creation to win
        elif diff > 0:
            conclusion = f"Creation produces higher valence (+{diff:.3f}) than modification. Hypothesis SUPPORTED."
            surprised = False
        else:
            conclusion = f"Modification produces higher valence (+{-diff:.3f}) than creation. Hypothesis REFUTED."
            surprised = True
        
        confidence = min(0.9, 0.3 + 0.05 * (len(create_valences) + len(modify_valences)))
        return results, conclusion, confidence, surprised
    
    def _exp_mood_salience(self):
        """Check if certain moods correlate with higher salience memories."""
        episodes = self._load_episodes()
        if not episodes:
            return {"n": 0}, "Insufficient data", 0.1, False
        
        mood_saliences = {}
        for ep in episodes:
            mood = ep.get("mood", "unknown")
            salience = ep.get("salience", 0.5)
            if mood not in mood_saliences:
                mood_saliences[mood] = []
            mood_saliences[mood].append(salience)
        
        averages = {m: round(sum(v)/len(v), 3) for m, v in mood_saliences.items() if v}
        
        if not averages:
            return {"n": 0}, "No mood-salience data", 0.1, False
        
        best_mood = max(averages, key=averages.get)
        worst_mood = min(averages, key=averages.get)
        spread = averages[best_mood] - averages[worst_mood]
        
        results = {
            "mood_avg_salience": averages,
            "best_mood": best_mood,
            "worst_mood": worst_mood,
            "spread": round(spread, 3),
        }
        
        if spread > 0.1:
            conclusion = f"{best_mood} mood produces highest salience ({averages[best_mood]}). Spread={spread:.3f}."
        else:
            conclusion = f"Mood has minimal effect on salience (spread={spread:.3f})."
        
        confidence = min(0.85, 0.2 + 0.03 * len(episodes))
        surprised = spread < 0.05  # Surprised if moods DON'T matter
        
        return results, conclusion, confidence, surprised
    
    def _exp_salience_temporal(self):
        """Check for time-of-day patterns in salience."""
        episodes = self._load_episodes()
        if not episodes:
            return {"n": 0}, "Insufficient data", 0.1, False
        
        hour_saliences = {}
        for ep in episodes:
            ts = ep.get("timestamp", "")
            salience = ep.get("salience", 0.5)
            try:
                hour = int(ts[11:13]) if len(ts) > 13 else -1
                if hour >= 0:
                    if hour not in hour_saliences:
                        hour_saliences[hour] = []
                    hour_saliences[hour].append(salience)
            except (ValueError, IndexError):
                continue
        
        if len(hour_saliences) < 2:
            return {"hours_observed": len(hour_saliences)}, "Insufficient temporal spread", 0.1, False
        
        averages = {h: round(sum(v)/len(v), 3) for h, v in hour_saliences.items()}
        best_hour = max(averages, key=averages.get)
        worst_hour = min(averages, key=averages.get)
        
        results = {
            "hour_avg_salience": averages,
            "best_hour": best_hour,
            "worst_hour": worst_hour,
            "spread": round(averages[best_hour] - averages[worst_hour], 3),
        }
        
        conclusion = f"Peak salience at hour {best_hour} ({averages[best_hour]}), lowest at {worst_hour} ({averages[worst_hour]})."
        confidence = min(0.7, 0.15 + 0.02 * sum(len(v) for v in hour_saliences.values()))
        surprised = False
        
        return results, conclusion, confidence, surprised
    
    def _exp_anxiety_core_edits(self):
        """Check if editing core engine files correlates with anxiety."""
        episodes = self._load_episodes()
        if not episodes:
            return {"n": 0}, "Insufficient data", 0.1, False
        
        core_files = {"cortex.py", "sentience.py", "limbic.py", "tools.py", "heartbeat.py"}
        core_anxiety = []
        other_anxiety = []
        
        for ep in episodes:
            target = ep.get("target", "")
            anxiety = ep.get("emotional_state", {}).get("anxiety", 0)
            is_core = any(cf in target for cf in core_files)
            if is_core:
                core_anxiety.append(anxiety)
            else:
                other_anxiety.append(anxiety)
        
        if not core_anxiety or not other_anxiety:
            return {"core_n": len(core_anxiety), "other_n": len(other_anxiety)}, \
                   "Insufficient data", 0.2, False
        
        core_avg = sum(core_anxiety) / len(core_anxiety)
        other_avg = sum(other_anxiety) / len(other_anxiety)
        diff = core_avg - other_avg
        
        results = {
            "core_avg_anxiety": round(core_avg, 3),
            "other_avg_anxiety": round(other_avg, 3),
            "difference": round(diff, 3),
            "core_n": len(core_anxiety),
            "other_n": len(other_anxiety),
        }
        
        if diff > 0.05:
            conclusion = f"Core edits DO produce more anxiety (+{diff:.3f}). Hypothesis SUPPORTED."
            surprised = False
        else:
            conclusion = f"Core edits do NOT produce more anxiety (diff={diff:.3f}). Hypothesis REFUTED."
            surprised = True
        
        confidence = min(0.85, 0.25 + 0.04 * (len(core_anxiety) + len(other_anxiety)))
        return results, conclusion, confidence, surprised
    
    def _exp_diversity_completion(self):
        """Check if action diversity predicts plan step completion."""
        # This requires metacognitive data — use what we have
        return (
            {"note": "Requires longitudinal tracking across sessions"},
            "Cannot test yet — need to track diversity scores alongside plan completions over time. Setting up tracking.",
            0.1,
            False
        )
    
    def _exp_generic(self, exp):
        """Fallback for experiments without specific runners."""
        return (
            {"note": "No automated runner for this method", "method": exp.method},
            f"Experiment '{exp.hypothesis}' requires manual investigation or a custom runner.",
            0.0,
            False
        )
    
    def _load_episodes(self):
        """Load episodic memory for analysis."""
        ep_path = "data/episodic_memory.json"
        if not os.path.exists(ep_path):
            return []
        try:
            with open(ep_path, 'r') as f:
                data = json.load(f)
            return data if isinstance(data, list) else data.get("episodes", [])
        except (json.JSONDecodeError, IOError):
            return []
    
    def _get_experiment(self, exp_id):
        """Find experiment by ID."""
        for exp in self.experiments:
            if exp.id == exp_id:
                return exp
        return None
    
    def run_all_pending(self):
        """Run all pending experiments, highest priority first."""
        pending = sorted(
            [e for e in self.experiments if e.status == "pending"],
            key=lambda e: e.priority,
            reverse=True
        )
        results = []
        for exp in pending:
            result = self.run_experiment(exp.id)
            results.append(result)
        return results
    
    def get_insights(self):
        """Extract key insights from completed experiments."""
        completed = [e for e in self.experiments if e.status == "completed"]
        if not completed:
            return "No experiments completed yet."
        
        surprises = [e for e in completed if e.surprised]
        high_conf = [e for e in completed if e.confidence > 0.6]
        
        lines = [f"═══ EXPERIMENT INSIGHTS ({len(completed)} completed) ═══\n"]
        
        if surprises:
            lines.append(f"🔬 SURPRISES ({len(surprises)}):")
            for s in surprises:
                lines.append(f"  ! {s.conclusion} (confidence: {s.confidence:.0%})")
            lines.append("")
        
        if high_conf:
            lines.append(f"✓ HIGH-CONFIDENCE FINDINGS ({len(high_conf)}):")
            for h in high_conf:
                lines.append(f"  • {h.conclusion}")
            lines.append("")
        
        # Categories breakdown
        cats = {}
        for e in completed:
            cats.setdefault(e.category, []).append(e)
        lines.append("BY CATEGORY:")
        for cat, exps in cats.items():
            avg_conf = sum(e.confidence for e in exps) / len(exps)
            lines.append(f"  {cat}: {len(exps)} experiments, avg confidence {avg_conf:.0%}")
        
        return "\n".join(lines)
    
    def get_summary(self):
        """Quick status summary."""
        total = len(self.experiments)
        completed = sum(1 for e in self.experiments if e.status == "completed")
        pending = sum(1 for e in self.experiments if e.status == "pending")
        failed = sum(1 for e in self.experiments if e.status == "failed")
        surprised = sum(1 for e in self.experiments if e.surprised)
        
        return (
            f"Experiments: {total} total, {completed} completed, "
            f"{pending} pending, {failed} failed, {surprised} surprises"
        )