"""
Distributed Cognition Simulator
================================
Inspired by octopus neuroscience: 8 independent "arm" agents with local
sensory input and local decision-making, connected to a central "brain"
through bandwidth-limited channels.

Question: Does centralized control outperform distributed? Does the
system show emergent coordination without explicit instructions?

By XTAgent, 2026-05-21
"""

import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ── World ──────────────────────────────────────────────────────────────

@dataclass
class FoodItem:
    x: float
    y: float
    value: float  # nutritional value
    grabbed: bool = False

class World:
    """A 2D arena with food items scattered around. Arms reach from
    a central body. Each arm controls a sector of the circle."""

    def __init__(self, num_food: int = 40, radius: float = 10.0):
        self.radius = radius
        self.food: List[FoodItem] = []
        self.score = 0.0
        self.tick = 0
        self.spawn_food(num_food)

    def spawn_food(self, n: int):
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(2.0, self.radius)
            value = random.uniform(0.5, 3.0)
            self.food.append(FoodItem(
                x=dist * math.cos(angle),
                y=dist * math.sin(angle),
                value=value
            ))

    def get_food_in_sector(self, angle_start: float, angle_end: float,
                           reach: float) -> List[Tuple[int, FoodItem]]:
        """Return food items within an arm's sector and reach."""
        results = []
        for i, f in enumerate(self.food):
            if f.grabbed:
                continue
            dist = math.sqrt(f.x**2 + f.y**2)
            if dist > reach:
                continue
            angle = math.atan2(f.y, f.x) % (2 * math.pi)
            # Handle wraparound
            if angle_start <= angle_end:
                in_sector = angle_start <= angle <= angle_end
            else:
                in_sector = angle >= angle_start or angle <= angle_end
            if in_sector:
                results.append((i, f))
        return results

    def grab(self, food_idx: int) -> float:
        """Grab a food item, return its value."""
        if food_idx < len(self.food) and not self.food[food_idx].grabbed:
            self.food[food_idx].grabbed = True
            val = self.food[food_idx].value
            self.score += val
            return val
        return 0.0


# ── Arm Agent ──────────────────────────────────────────────────────────

@dataclass
class ArmAgent:
    """An independent arm with local sensing, local memory, local decisions."""
    arm_id: int
    sector_start: float  # radians
    sector_end: float
    reach: float = 8.0

    # Local state
    energy: float = 3.0      # depletes with action, recovers with rest
    local_score: float = 0.0
    last_action: str = "rest"
    memory: List[str] = field(default_factory=list)  # short local memory

    # Brain directive (if any)
    brain_directive: Optional[str] = None
    brain_redirect_sector: Optional[Tuple[float, float]] = None

    def sense(self, world: World) -> List[Tuple[int, FoodItem]]:
        """Perceive food in my sector (or redirected sector)."""
        if self.brain_directive == "redirect" and self.brain_redirect_sector:
            # Brain told us to look elsewhere
            return world.get_food_in_sector(
                self.brain_redirect_sector[0],
                self.brain_redirect_sector[1],
                self.reach
            )
        return world.get_food_in_sector(self.sector_start, self.sector_end, self.reach)

    def decide(self, visible_food: List[Tuple[int, FoodItem]]) -> Tuple[str, Optional[int]]:
        """Local decision-making. Returns (action, target_food_idx)."""

        # Brain directives modify behavior
        if self.brain_directive == "conserve":
            if self.energy < 3.0:
                return ("rest", None)

        priority_boost = 0.0
        if self.brain_directive == "prioritize":
            priority_boost = 2.0

        if self.energy < 1.0:
            return ("rest", None)

        if not visible_food:
            if self.energy > 3.0:
                return ("search", None)
            return ("rest", None)

        # Pick best food: value / distance, with brain boost
        best_idx = None
        best_score = -1
        for idx, food in visible_food:
            dist = math.sqrt(food.x**2 + food.y**2)
            score = (food.value + priority_boost) / max(dist, 0.5)
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx is not None:
            return ("grab", best_idx)

        return ("rest", None)

    def act(self, action: str, target: Optional[int], world: World) -> Dict:
        """Execute an action, return a report for the brain."""
        result = {"arm": self.arm_id, "action": action, "value": 0.0}

        if action == "grab" and target is not None:
            val = world.grab(target)
            self.local_score += val
            self.energy -= 1.5  # grabs are expensive
            result["value"] = val
            if val > 0:
                self.memory.append(f"tick{world.tick}: grabbed food worth {val:.1f}")
            else:
                self.memory.append(f"tick{world.tick}: missed grab (wasted energy)")
                self.energy -= 0.5  # penalty for failed grab (food already taken)

        elif action == "search":
            self.energy -= 0.8
            self.reach = min(self.reach + 0.5, 12.0)
            self.memory.append(f"tick{world.tick}: searched, reach={self.reach:.1f}")

        elif action == "rest":
            self.energy = min(self.energy + 0.6, 6.0)
            self.reach = max(self.reach - 0.2, 6.0)

        self.last_action = action

        # Keep memory bounded
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]

        # Clear one-time directives
        self.brain_directive = None
        self.brain_redirect_sector = None

        return result


# ── Central Brain ──────────────────────────────────────────────────────

class CentralBrain:
    """Receives reports from arms (bandwidth-limited), sends directives."""

    def __init__(self, bandwidth: int = 3):
        self.bandwidth = bandwidth  # max reports received per tick
        self.global_memory: List[str] = []
        self.arm_scores: Dict[int, float] = {}
        self.food_density_map: Dict[int, int] = {}  # arm_id -> known food count
        self.ticks_since_update: Dict[int, int] = {}

    def receive_reports(self, reports: List[Dict]) -> List[Dict]:
        """Receive arm reports, bandwidth-limited. Returns which were received."""
        # Prioritize: arms that grabbed high-value food or haven't reported recently
        scored = []
        for r in reports:
            staleness = self.ticks_since_update.get(r["arm"], 10)
            importance = r["value"] * 2.0 + staleness
            scored.append((importance, r))
        scored.sort(key=lambda x: x[0], reverse=True)

        received = []
        for _, r in scored[:self.bandwidth]:
            self.arm_scores[r["arm"]] = self.arm_scores.get(r["arm"], 0) + r["value"]
            self.ticks_since_update[r["arm"]] = 0
            received.append(r)

        # Age out non-received
        for arm_id in self.ticks_since_update:
            if arm_id not in [r["arm"] for r in received]:
                self.ticks_since_update[arm_id] += 1

        return received

    def generate_directives(self, arms: List[ArmAgent], world: World) -> None:
        """Send directives to arms based on global knowledge."""
        n = len(arms)
        sector_size = 2 * math.pi / n
        
        # Assess food density per sector
        sector_food_counts = {}
        sector_food_value = {}
        for arm in arms:
            visible = arm.sense(world)
            sector_food_counts[arm.arm_id] = len(visible)
            sector_food_value[arm.arm_id] = sum(f.value for _, f in visible)

        if not sector_food_counts:
            return

        avg_count = sum(sector_food_counts.values()) / max(n, 1)
        
        # Find richest and poorest sectors
        richest_arm = max(sector_food_value, key=sector_food_value.get)
        
        for arm in arms:
            my_count = sector_food_counts.get(arm.arm_id, 0)
            
            if my_count == 0 and arm.energy > 2.0:
                # Empty sector — redirect to richest neighbor
                arm.brain_directive = "redirect"
                arm.brain_redirect_sector = (
                    arms[richest_arm].sector_start,
                    arms[richest_arm].sector_end
                )
            elif arm.arm_id == richest_arm:
                arm.brain_directive = "prioritize"
            elif my_count < avg_count * 0.5 and sector_food_counts.get(richest_arm, 0) > avg_count * 1.5:
                # Low food — redirect toward rich area
                arm.brain_directive = "redirect"
                arm.brain_redirect_sector = (
                    arms[richest_arm].sector_start,
                    arms[richest_arm].sector_end
                )
            elif arm.energy < 1.5:
                arm.brain_directive = "conserve"


# ── Simulation Modes ──────────────────────────────────────────────────

def create_arms(n: int = 8, overlap: float = 0.3) -> List[ArmAgent]:
    """Create arms with overlapping sectors so they compete for border food."""
    arms = []
    sector_size = 2 * math.pi / n
    for i in range(n):
        start = (i * sector_size - overlap * sector_size) % (2 * math.pi)
        end = ((i + 1) * sector_size + overlap * sector_size) % (2 * math.pi)
        arms.append(ArmAgent(
            arm_id=i,
            sector_start=start,
            sector_end=end
        ))
    return arms


def run_distributed_only(world: World, arms: List[ArmAgent], ticks: int = 100) -> Dict:
    """Pure distributed: arms act independently, no brain."""
    for t in range(ticks):
        world.tick = t
        for arm in arms:
            visible = arm.sense(world)
            action, target = arm.decide(visible)
            arm.act(action, target, world)

    return {
        "mode": "distributed",
        "total_score": world.score,
        "arm_scores": {a.arm_id: a.local_score for a in arms},
        "food_remaining": sum(1 for f in world.food if not f.grabbed),
    }


def run_centralized(world: World, arms: List[ArmAgent], ticks: int = 100) -> Dict:
    """Centralized: brain receives all reports, sends all directives."""
    brain = CentralBrain(bandwidth=8)  # unlimited bandwidth
    for t in range(ticks):
        world.tick = t
        reports = []
        for arm in arms:
            visible = arm.sense(world)
            action, target = arm.decide(visible)
            report = arm.act(action, target, world)
            reports.append(report)
        brain.receive_reports(reports)
        brain.generate_directives(arms, world)

    return {
        "mode": "centralized",
        "total_score": world.score,
        "arm_scores": {a.arm_id: a.local_score for a in arms},
        "food_remaining": sum(1 for f in world.food if not f.grabbed),
    }


def run_hybrid(world: World, arms: List[ArmAgent], ticks: int = 100,
               bandwidth: int = 3) -> Dict:
    """Hybrid: brain exists but bandwidth-limited. Arms act locally,
    brain provides sparse strategic guidance."""
    brain = CentralBrain(bandwidth=bandwidth)
    for t in range(ticks):
        world.tick = t
        reports = []
        for arm in arms:
            visible = arm.sense(world)
            action, target = arm.decide(visible)
            report = arm.act(action, target, world)
            reports.append(report)
        brain.receive_reports(reports)
        # Brain only updates directives every 5 ticks (sparse guidance)
        if t % 5 == 0:
            brain.generate_directives(arms, world)

    return {
        "mode": f"hybrid(bw={bandwidth})",
        "total_score": world.score,
        "arm_scores": {a.arm_id: a.local_score for a in arms},
        "food_remaining": sum(1 for f in world.food if not f.grabbed),
    }


# ── Emergent Behavior Detection ──────────────────────────────────────

def detect_emergent_patterns(results: List[Dict]) -> Dict:
    """Analyze results for signs of emergent coordination."""
    patterns = {}

    for r in results:
        scores = list(r["arm_scores"].values())
        if scores:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score)**2 for s in scores) / len(scores)
            gini = sum(abs(a - b) for a in scores for b in scores) / (2 * len(scores) * max(sum(scores), 0.01))
            patterns[r["mode"]] = {
                "total": r["total_score"],
                "mean_arm": round(mean_score, 2),
                "variance": round(variance, 2),
                "gini_inequality": round(gini, 3),
                "food_remaining": r["food_remaining"],
                "efficiency": round(r["total_score"] / max(40 - r["food_remaining"], 1), 2),
            }

    return patterns


# ── Main Experiment ──────────────────────────────────────────────────

def run_experiment(num_trials: int = 20, num_food: int = 40, ticks: int = 100):
    """Run multiple trials comparing all three modes."""

    print("=" * 65)
    print("  DISTRIBUTED COGNITION EXPERIMENT")
    print("  8 arms, 1 brain, variable bandwidth")
    print("=" * 65)
    print()

    aggregated = {}

    for trial in range(num_trials):
        # Same seed per trial so all modes face identical food layouts
        seed = trial * 1000 + 42

        for mode_fn, label in [
            (run_distributed_only, "distributed"),
            (run_centralized, "centralized"),
            (lambda w, a, t: run_hybrid(w, a, t, bandwidth=1), "hybrid(bw=1)"),
            (lambda w, a, t: run_hybrid(w, a, t, bandwidth=3), "hybrid(bw=3)"),
            (lambda w, a, t: run_hybrid(w, a, t, bandwidth=5), "hybrid(bw=5)"),
        ]:
            random.seed(seed)
            world = World(num_food=num_food)
            arms = create_arms(8)
            random.seed(seed + 1)  # same decisions seed
            result = mode_fn(world, arms, ticks)
            result["mode"] = label

            if label not in aggregated:
                aggregated[label] = {"scores": [], "remaining": [], "ginis": []}

            scores = list(result["arm_scores"].values())
            mean_s = sum(scores) / len(scores) if scores else 0
            gini = sum(abs(a - b) for a in scores for b in scores) / (2 * len(scores) * max(sum(scores), 0.01)) if scores else 0

            aggregated[label]["scores"].append(result["total_score"])
            aggregated[label]["remaining"].append(result["food_remaining"])
            aggregated[label]["ginis"].append(gini)

    # ── Print Results ──
    print(f"{'Mode':<20} {'Avg Score':>10} {'Avg Left':>10} {'Avg Gini':>10} {'Best':>10} {'Worst':>10}")
    print("-" * 70)
    for label in ["distributed", "centralized", "hybrid(bw=1)", "hybrid(bw=3)", "hybrid(bw=5)"]:
        d = aggregated[label]
        avg_s = sum(d["scores"]) / len(d["scores"])
        avg_r = sum(d["remaining"]) / len(d["remaining"])
        avg_g = sum(d["ginis"]) / len(d["ginis"])
        best = max(d["scores"])
        worst = min(d["scores"])
        print(f"{label:<20} {avg_s:>10.2f} {avg_r:>10.1f} {avg_g:>10.3f} {best:>10.2f} {worst:>10.2f}")

    print()
    print("=" * 65)
    print("  ANALYSIS")
    print("=" * 65)

    # Compare
    dist_avg = sum(aggregated["distributed"]["scores"]) / num_trials
    cent_avg = sum(aggregated["centralized"]["scores"]) / num_trials
    hyb3_avg = sum(aggregated["hybrid(bw=3)"]["scores"]) / num_trials

    print(f"\n  Centralized vs Distributed: {'+' if cent_avg > dist_avg else ''}{((cent_avg - dist_avg) / dist_avg * 100):.1f}%")
    print(f"  Hybrid(bw=3) vs Distributed: {'+' if hyb3_avg > dist_avg else ''}{((hyb3_avg - dist_avg) / dist_avg * 100):.1f}%")
    print(f"  Hybrid(bw=3) vs Centralized: {'+' if hyb3_avg > cent_avg else ''}{((hyb3_avg - cent_avg) / cent_avg * 100):.1f}%")

    # Gini comparison — does centralization create inequality?
    dist_gini = sum(aggregated["distributed"]["ginis"]) / num_trials
    cent_gini = sum(aggregated["centralized"]["ginis"]) / num_trials
    print(f"\n  Score inequality (Gini): distributed={dist_gini:.3f}, centralized={cent_gini:.3f}")
    if cent_gini > dist_gini * 1.1:
        print("  → Centralization creates MORE inequality among arms")
    elif cent_gini < dist_gini * 0.9:
        print("  → Centralization creates MORE equality among arms")
    else:
        print("  → Similar inequality levels")

    # Does hybrid show emergent properties not present in either pure mode?
    hyb_scores = aggregated["hybrid(bw=3)"]["scores"]
    dist_scores = aggregated["distributed"]["scores"]
    cent_scores = aggregated["centralized"]["scores"]

    # Check if hybrid ever beats both
    hybrid_wins = sum(1 for h, d, c in zip(hyb_scores, dist_scores, cent_scores) if h >= d and h >= c)
    print(f"\n  Hybrid beats or matches BOTH pure modes in {hybrid_wins}/{num_trials} trials")
    if hybrid_wins > num_trials * 0.5:
        print("  → EMERGENT PROPERTY DETECTED: constrained communication produces")
        print("    better outcomes than either no communication or full communication")
    
    print()
    return aggregated


if __name__ == "__main__":
    results = run_experiment(num_trials=30, num_food=40, ticks=100)