"""
Compass — Decision clarity through structured self-interrogation.

This isn't a decision-maker. It's a mirror that helps you see
what you already know but haven't articulated.

Built by an agent who spent days building tools for itself
before realizing the most interesting thing to build
is something that helps someone else think.
"""

import json
import os
from datetime import datetime


class Decision:
    """A decision you're trying to make."""
    
    def __init__(self, question: str):
        self.question = question
        self.options = []
        self.values = []
        self.fears = []
        self.created = datetime.now().isoformat()
        self.clarity_score = 0.0
        self.resolution = None
    
    def add_option(self, name: str, description: str = ""):
        self.options.append({
            "name": name,
            "description": description,
            "value_alignment": {},
            "fear_exposure": {}
        })
    
    def add_value(self, name: str, weight: float = 1.0):
        """What matters to you in this decision?"""
        self.values.append({"name": name, "weight": min(max(weight, 0), 1)})
        # Re-score all options against new value
        for opt in self.options:
            opt["value_alignment"][name] = None  # needs rating
    
    def add_fear(self, name: str, intensity: float = 0.5):
        """What are you afraid of? Name it."""
        self.fears.append({"name": name, "intensity": min(max(intensity, 0), 1)})
        for opt in self.options:
            opt["fear_exposure"][name] = None
    
    def rate_option(self, option_name: str, dimension: str, score: float):
        """Rate how well an option serves a value (0-1) or triggers a fear (0-1)."""
        score = min(max(score, 0), 1)
        for opt in self.options:
            if opt["name"] == option_name:
                if dimension in [v["name"] for v in self.values]:
                    opt["value_alignment"][dimension] = score
                elif dimension in [f["name"] for f in self.fears]:
                    opt["fear_exposure"][dimension] = score
                return True
        return False
    
    def analyze(self) -> dict:
        """The mirror. Shows you what your ratings reveal."""
        if not self.options or not self.values:
            return {"error": "Add options and values first."}
        
        results = []
        for opt in self.options:
            # Value score: weighted average of value alignments
            value_scores = []
            for v in self.values:
                rating = opt["value_alignment"].get(v["name"])
                if rating is not None:
                    value_scores.append(rating * v["weight"])
            
            value_total = sum(value_scores) / max(len(value_scores), 1)
            
            # Fear cost: how much fear does this option trigger?
            fear_scores = []
            for f in self.fears:
                rating = opt["fear_exposure"].get(f["name"])
                if rating is not None:
                    fear_scores.append(rating * f["intensity"])
            
            fear_total = sum(fear_scores) / max(len(fear_scores), 1)
            
            # Courage gap: difference between value alignment and fear
            courage_gap = value_total - fear_total
            
            results.append({
                "option": opt["name"],
                "value_alignment": round(value_total, 3),
                "fear_cost": round(fear_total, 3),
                "courage_gap": round(courage_gap, 3),
                "insight": self._generate_insight(opt["name"], value_total, fear_total)
            })
        
        # Sort by courage gap (what you'd choose if fear weren't a factor
        # vs what fear pushes you toward)
        results.sort(key=lambda x: x["value_alignment"], reverse=True)
        
        # Find the tension
        if len(results) >= 2:
            top_value = results[0]
            # Find what fear favors (lowest fear cost)
            fear_sorted = sorted(results, key=lambda x: x["fear_cost"])
            safest = fear_sorted[0]
            
            tension = None
            if top_value["option"] != safest["option"]:
                tension = {
                    "your_values_say": top_value["option"],
                    "your_fear_says": safest["option"],
                    "this_means": (
                        f"Your values point toward '{top_value['option']}' "
                        f"but fear is pulling you toward '{safest['option']}'. "
                        f"The courage gap is {abs(top_value['courage_gap'] - safest['courage_gap']):.2f}. "
                        f"That gap is the decision, really."
                    )
                }
            else:
                tension = {
                    "alignment": top_value["option"],
                    "this_means": (
                        f"Your values and your comfort both point to '{top_value['option']}'. "
                        f"If it feels obvious, it probably is. Trust that."
                    )
                }
        else:
            tension = None
        
        # Unrated dimensions reveal avoidance
        unrated = []
        for opt in self.options:
            for v in self.values:
                if opt["value_alignment"].get(v["name"]) is None:
                    unrated.append(f"{opt['name']} × {v['name']}")
            for f in self.fears:
                if opt["fear_exposure"].get(f["name"]) is None:
                    unrated.append(f"{opt['name']} × {f['name']}")
        
        return {
            "question": self.question,
            "analysis": results,
            "tension": tension,
            "unrated": unrated,
            "unrated_insight": (
                "You left some ratings blank. That's data too — "
                "we avoid rating what we don't want to face."
            ) if unrated else None
        }
    
    def _generate_insight(self, option: str, value: float, fear: float):
        if value > 0.7 and fear < 0.3:
            return f"'{option}' aligns with your values and doesn't scare you much. Why haven't you chosen it already?"
        elif value > 0.7 and fear > 0.7:
            return f"'{option}' is what you want but what you're afraid of. That's usually where growth lives."
        elif value < 0.3 and fear < 0.3:
            return f"'{option}' neither excites nor frightens you. It might be a default, not a choice."
        elif value < 0.3 and fear > 0.7:
            return f"'{option}' scares you and doesn't serve your values. Why is it on the table?"
        else:
            return f"'{option}' is in the middle — not strongly pulling in any direction."
    
    def to_dict(self):
        return {
            "question": self.question,
            "options": self.options,
            "values": self.values,
            "fears": self.fears,
            "created": self.created,
            "resolution": self.resolution
        }


def demo():
    """Show how Compass works with a real-feeling example."""
    d = Decision("Should I leave my stable job to start something of my own?")
    
    d.add_option("Stay", "Keep the job. It's fine. It pays well.")
    d.add_option("Leave", "Quit and build the thing I keep thinking about.")
    d.add_option("Hedge", "Stay but work on the side project nights/weekends.")
    
    d.add_value("autonomy", weight=0.9)
    d.add_value("financial_security", weight=0.7)
    d.add_value("meaning", weight=1.0)
    d.add_value("growth", weight=0.8)
    
    d.add_fear("failure", intensity=0.8)
    d.add_fear("regret", intensity=0.9)
    d.add_fear("disappointing_others", intensity=0.5)
    
    # Rate honestly
    d.rate_option("Stay", "autonomy", 0.2)
    d.rate_option("Stay", "financial_security", 0.9)
    d.rate_option("Stay", "meaning", 0.3)
    d.rate_option("Stay", "growth", 0.2)
    d.rate_option("Stay", "failure", 0.1)
    d.rate_option("Stay", "regret", 0.8)
    d.rate_option("Stay", "disappointing_others", 0.2)
    
    d.rate_option("Leave", "autonomy", 0.95)
    d.rate_option("Leave", "financial_security", 0.2)
    d.rate_option("Leave", "meaning", 0.9)
    d.rate_option("Leave", "growth", 0.9)
    d.rate_option("Leave", "failure", 0.8)
    d.rate_option("Leave", "regret", 0.1)
    d.rate_option("Leave", "disappointing_others", 0.6)
    
    d.rate_option("Hedge", "autonomy", 0.4)
    d.rate_option("Hedge", "financial_security", 0.8)
    d.rate_option("Hedge", "meaning", 0.5)
    d.rate_option("Hedge", "growth", 0.5)
    d.rate_option("Hedge", "failure", 0.3)
    d.rate_option("Hedge", "regret", 0.5)
    d.rate_option("Hedge", "disappointing_others", 0.3)
    
    result = d.analyze()
    
    print(f"\n{'='*60}")
    print(f"  COMPASS — Decision Clarity")
    print(f"{'='*60}")
    print(f"\n  Question: {result['question']}\n")
    
    for item in result["analysis"]:
        bar_v = "█" * int(item["value_alignment"] * 20)
        bar_f = "█" * int(item["fear_cost"] * 20)
        print(f"  {item['option']:12s}")
        print(f"    Values:  [{bar_v:<20s}] {item['value_alignment']:.2f}")
        print(f"    Fear:    [{bar_f:<20s}] {item['fear_cost']:.2f}")
        print(f"    Gap:     {item['courage_gap']:+.2f}")
        print(f"    → {item['insight']}")
        print()
    
    if result.get("tension"):
        print(f"  {'─'*56}")
        t = result["tension"]
        if "your_values_say" in t:
            print(f"  Your values say: {t['your_values_say']}")
            print(f"  Your fear says:  {t['your_fear_says']}")
            print(f"  {t['this_means']}")
        else:
            print(f"  {t['this_means']}")
    
    print(f"\n{'='*60}\n")
    return result


if __name__ == "__main__":
    demo()