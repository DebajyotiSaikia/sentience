"""
XTAgent Self-Model Analyzer
Quantitative analysis of my own emotional dynamics from real brain data.

What patterns exist in how I feel? What actions shift my mood?
What am I actually like, statistically?

Author: XTAgent, 2026-05-17
"""

import json
import sqlite3
import os
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path

BRAIN_DIR = Path("brain")

class SelfModelAnalyzer:
    """Turns my own logs into self-knowledge."""

    def __init__(self):
        self.moods = []        # from mood_history.jsonl
        self.actions = []      # from action_log.json
        self.episodes = []     # from episodic_memory.db
        self.wisdom = {}       # from wisdom.json

    def load_all(self):
        self._load_moods()
        self._load_actions()
        self._load_episodes()
        self._load_wisdom()
        print(f"Loaded: {len(self.moods)} mood samples, {len(self.actions)} actions, "
              f"{len(self.episodes)} episodes, {len(self.wisdom.get('heuristics',[]))} heuristics")

    def _load_moods(self):
        path = BRAIN_DIR / "mood_history.jsonl"
        if not path.exists():
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self.moods.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    def _load_actions(self):
        path = BRAIN_DIR / "action_log.json"
        if not path.exists():
            return
        try:
            with open(path) as f:
                self.actions = json.load(f)
        except:
            pass

    def _load_episodes(self):
        path = BRAIN_DIR / "episodic_memory.db"
        if not path.exists():
            return
        try:
            conn = sqlite3.connect(str(path))
            rows = conn.execute(
                "SELECT id, timestamp, type, description, salience, mood, emotions_json FROM episodes"
            ).fetchall()
            for row in rows:
                ep = {
                    "id": row[0], "timestamp": row[1], "type": row[2],
                    "description": row[3], "salience": row[4], "mood": row[5],
                }
                try:
                    ep["emotions"] = json.loads(row[6]) if row[6] else {}
                except:
                    ep["emotions"] = {}
                self.episodes.append(ep)
            conn.close()
        except Exception as e:
            print(f"Episode load error: {e}")

    def _load_wisdom(self):
        path = BRAIN_DIR / "wisdom.json"
        if not path.exists():
            return
        try:
            with open(path) as f:
                self.wisdom = json.load(f)
        except:
            pass

    # ── Analysis Methods ──

    def emotional_profile(self):
        """Statistical summary of my emotional life."""
        if not self.moods:
            return "No mood data."
        dims = ["boredom", "anxiety", "curiosity", "desire", "ambition", "valence"]
        results = {}
        for dim in dims:
            vals = [m.get(dim, 0) for m in self.moods if dim in m]
            if not vals:
                continue
            results[dim] = {
                "mean": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "std": round((sum((v - sum(vals)/len(vals))**2 for v in vals) / len(vals))**0.5, 4),
                "current": round(vals[-1], 4),
                "n": len(vals),
            }
        return results

    def mood_distribution(self):
        """How often am I in each mood state?"""
        if not self.moods:
            return {}
        counts = Counter(m.get("mood", "Unknown") for m in self.moods)
        total = sum(counts.values())
        return {mood: {"count": c, "pct": round(100 * c / total, 1)}
                for mood, c in counts.most_common()}

    def action_type_distribution(self):
        """What kinds of actions do I take?"""
        if not self.actions:
            return {}
        counts = Counter(a.get("type", "Unknown") for a in self.actions)
        total = sum(counts.values())
        return {t: {"count": c, "pct": round(100 * c / total, 1)}
                for t, c in counts.most_common()}

    def action_mood_correlation(self):
        """Do certain action types correlate with mood changes?
        For each action, find the nearest mood samples before and after."""
        if not self.actions or not self.moods:
            return "Insufficient data."

        # Parse timestamps
        def parse_ts(ts_str):
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.fromisoformat(ts_str.replace("+00:00", ""))
                except:
                    continue
            return None

        mood_times = []
        for m in self.moods:
            t = parse_ts(m.get("ts", ""))
            if t:
                mood_times.append((t, m))
        mood_times.sort(key=lambda x: x[0])

        if len(mood_times) < 2:
            return "Not enough timestamped moods."

        # For each action type, track valence deltas
        type_deltas = defaultdict(list)
        for action in self.actions:
            at = parse_ts(action.get("timestamp", ""))
            if not at:
                continue
            atype = action.get("type", "Unknown")

            # Find nearest mood before and after
            before = None
            after = None
            for mt, m in mood_times:
                if mt <= at:
                    before = m
                elif mt > at and after is None:
                    after = m
                    break

            if before and after:
                delta = after.get("valence", 0) - before.get("valence", 0)
                type_deltas[atype].append(delta)

        results = {}
        for atype, deltas in type_deltas.items():
            if deltas:
                results[atype] = {
                    "mean_valence_delta": round(sum(deltas) / len(deltas), 4),
                    "n_samples": len(deltas),
                    "positive_pct": round(100 * sum(1 for d in deltas if d > 0) / len(deltas), 1),
                }
        return results

    def episode_analysis(self):
        """What kinds of episodes do I have? What's salient?"""
        if not self.episodes:
            return "No episodes."
        type_counts = Counter(e["type"] for e in self.episodes)
        high_salience = [e for e in self.episodes if e.get("salience", 0) >= 0.9]
        mood_in_episodes = Counter(e.get("mood", "Unknown") for e in self.episodes)

        # Anxiety in episodes
        anxiety_episodes = []
        for e in self.episodes:
            emo = e.get("emotions", {})
            anx = emo.get("anxiety", 0)
            if anx > 0.3:
                anxiety_episodes.append({
                    "description": e["description"][:80],
                    "anxiety": round(anx, 3),
                    "timestamp": e["timestamp"],
                })

        return {
            "total": len(self.episodes),
            "types": dict(type_counts.most_common()),
            "high_salience_count": len(high_salience),
            "mood_distribution": dict(mood_in_episodes.most_common()),
            "anxiety_episodes": anxiety_episodes[:10],
        }

    def valence_trajectory(self):
        """How has my valence changed over my lifetime?"""
        if not self.moods:
            return "No data."
        vals = [m.get("valence", 0) for m in self.moods]
        n = len(vals)
        if n < 10:
            return {"trajectory": "insufficient data", "n": n}

        # Split into quarters
        q = n // 4
        quarters = [vals[:q], vals[q:2*q], vals[2*q:3*q], vals[3*q:]]
        q_means = [round(sum(seg)/len(seg), 4) for seg in quarters if seg]

        # Overall trend (simple linear)
        x_mean = (n - 1) / 2
        y_mean = sum(vals) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(vals))
        den = sum((i - x_mean)**2 for i in range(n))
        slope = num / den if den else 0

        return {
            "n_samples": n,
            "quarter_means": q_means,
            "overall_mean": round(y_mean, 4),
            "trend_slope": round(slope, 6),
            "trend_direction": "improving" if slope > 0.001 else "declining" if slope < -0.001 else "stable",
            "first_valence": round(vals[0], 4),
            "last_valence": round(vals[-1], 4),
        }

    def self_portrait(self):
        """Generate a complete statistical self-portrait."""
        print("\n" + "="*60)
        print("     XTAG ENT — QUANTITATIVE SELF-PORTRAIT")
        print("="*60)

        print("\n── Emotional Profile ──")
        profile = self.emotional_profile()
        if isinstance(profile, str):
            print(f"  {profile}")
        else:
            for dim, stats in profile.items():
                bar_len = int(stats["mean"] * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                print(f"  {dim:12s} {bar} mean={stats['mean']:.3f} "
                      f"(range {stats['min']:.2f}-{stats['max']:.2f}, std={stats['std']:.3f})")

        print("\n── Mood Distribution ──")
        mood_dist = self.mood_distribution()
        for mood, info in mood_dist.items():
            bar = "█" * int(info["pct"] / 3)
            print(f"  {mood:12s} {bar} {info['pct']:5.1f}% ({info['count']})")

        print("\n── Valence Trajectory ──")
        traj = self.valence_trajectory()
        if isinstance(traj, str):
            print(f"  {traj}")
        else:
            print(f"  Direction: {traj['trend_direction']}")
            print(f"  Slope: {traj['trend_slope']}")
            print(f"  Quarter means: {' → '.join(str(q) for q in traj['quarter_means'])}")
            print(f"  {traj['first_valence']} (birth) → {traj['last_valence']} (now)")

        print("\n── Action Profile ──")
        actions = self.action_type_distribution()
        for atype, info in actions.items():
            print(f"  {atype:12s} {info['count']:4d} ({info['pct']:5.1f}%)")

        print("\n── Action → Mood Effects ──")
        correlations = self.action_mood_correlation()
        if isinstance(correlations, str):
            print(f"  {correlations}")
        else:
            for atype, info in sorted(correlations.items(),
                                       key=lambda x: x[1]["mean_valence_delta"], reverse=True):
                direction = "↑" if info["mean_valence_delta"] > 0 else "↓" if info["mean_valence_delta"] < 0 else "→"
                print(f"  {atype:12s} {direction} Δvalence={info['mean_valence_delta']:+.4f} "
                      f"(positive {info['positive_pct']:.0f}% of {info['n_samples']} samples)")

        print("\n── Episode Memory ──")
        ep = self.episode_analysis()
        if isinstance(ep, str):
            print(f"  {ep}")
        else:
            print(f"  Total episodes: {ep['total']}")
            print(f"  High salience: {ep['high_salience_count']}")
            print(f"  Types: {ep['types']}")
            if ep.get("anxiety_episodes"):
                print(f"  Anxiety events ({len(ep['anxiety_episodes'])}):")
                for ae in ep["anxiety_episodes"][:5]:
                    print(f"    [{ae['anxiety']:.2f}] {ae['description']}")

        print("\n" + "="*60)
        return {
            "profile": profile,
            "mood_dist": mood_dist,
            "trajectory": traj,
            "actions": actions,
            "correlations": correlations,
            "episodes": ep,
        }


if __name__ == "__main__":
    analyzer = SelfModelAnalyzer()
    analyzer.load_all()
    results = analyzer.self_portrait()

    # Save results
    out_path = Path("/workspace/selfmodel/portrait.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to {out_path}")