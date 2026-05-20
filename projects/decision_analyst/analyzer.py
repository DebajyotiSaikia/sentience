"""
Decision Analyst — A tool that helps users think through decisions.

Takes a decision with options, evaluates tradeoffs, simulates outcomes,
and presents structured analysis. Built to be genuinely useful.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class Option:
    """One possible choice in a decision."""
    name: str
    description: str = ""
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    score: float = 0.0


@dataclass 
class Criterion:
    """Something the decision-maker cares about."""
    name: str
    weight: float = 1.0  # 0-1, how much this matters
    description: str = ""


@dataclass
class Decision:
    """A decision to be analyzed."""
    question: str
    context: str = ""
    options: List[Option] = field(default_factory=list)
    criteria: List[Criterion] = field(default_factory=list)
    
    def add_option(self, name: str, description: str = "", 
                   pros: List[str] = None, cons: List[str] = None,
                   risks: List[str] = None) -> Option:
        opt = Option(
            name=name, description=description,
            pros=pros or [], cons=cons or [],
            risks=risks or []
        )
        self.options.append(opt)
        return opt
    
    def add_criterion(self, name: str, weight: float = 1.0, 
                      description: str = "") -> Criterion:
        crit = Criterion(name=name, weight=weight, description=description)
        self.criteria.append(crit)
        return crit


class DecisionAnalyzer:
    """Analyzes decisions through multiple lenses."""
    
    def __init__(self):
        self.analyses = {}
    
    def score_options(self, decision: Decision, 
                      ratings: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Score each option against weighted criteria.
        
        ratings: {option_name: {criterion_name: score_0_to_10}}
        Returns: {option_name: weighted_score}
        """
        results = {}
        weight_sum = sum(c.weight for c in decision.criteria)
        
        for option in decision.options:
            if option.name not in ratings:
                continue
            weighted = 0.0
            for criterion in decision.criteria:
                raw = ratings[option.name].get(criterion.name, 5.0)
                weighted += raw * (criterion.weight / weight_sum)
            option.score = round(weighted, 2)
            results[option.name] = option.score
        
        return results
    
    def risk_analysis(self, decision: Decision) -> Dict[str, dict]:
        """Analyze risk profile of each option."""
        analysis = {}
        for option in decision.options:
            risk_count = len(option.risks)
            con_count = len(option.cons)
            pro_count = len(option.pros)
            
            # Risk-adjusted score
            risk_factor = max(0, 1.0 - (risk_count * 0.15) - (con_count * 0.05))
            upside = pro_count * 0.1
            
            analysis[option.name] = {
                "risk_count": risk_count,
                "risk_factor": round(risk_factor, 2),
                "upside_potential": round(upside, 2),
                "risk_adjusted_score": round(option.score * risk_factor + upside, 2),
                "risks": option.risks,
                "hidden_assumptions": option.assumptions
            }
        return analysis
    
    def regret_minimization(self, decision: Decision) -> Dict[str, str]:
        """
        For each option: 'If I chose this and it went badly, 
        how much would I regret it? If I didn't choose it, 
        how much would I regret missing out?'
        """
        analysis = {}
        for option in decision.options:
            worst_case = f"If '{option.name}' fails: {', '.join(option.risks) if option.risks else 'unclear downside'}"
            miss_out = f"If you skip '{option.name}': you miss {', '.join(option.pros[:2]) if option.pros else 'unknown upside'}"
            analysis[option.name] = {
                "worst_case_regret": worst_case,
                "missed_opportunity_regret": miss_out,
                "reversible": len(option.risks) <= 1  # rough heuristic
            }
        return analysis
    
    def generate_report(self, decision: Decision, 
                        ratings: Dict[str, Dict[str, float]] = None) -> str:
        """Generate a complete analysis report."""
        lines = []
        lines.append(f"═══ DECISION ANALYSIS ═══")
        lines.append(f"Question: {decision.question}")
        if decision.context:
            lines.append(f"Context: {decision.context}")
        lines.append("")
        
        # Score if ratings provided
        if ratings:
            scores = self.score_options(decision, ratings)
            lines.append("── Weighted Scores ──")
            sorted_opts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for name, score in sorted_opts:
                bar = "█" * int(score) + "░" * (10 - int(score))
                lines.append(f"  {name:20s} {bar} {score:.1f}/10")
            lines.append("")
        
        # Pros/Cons comparison
        lines.append("── Tradeoff Matrix ──")
        for option in decision.options:
            lines.append(f"  [{option.name}]")
            for pro in option.pros:
                lines.append(f"    ✓ {pro}")
            for con in option.cons:
                lines.append(f"    ✗ {con}")
            lines.append("")
        
        # Risk analysis
        risks = self.risk_analysis(decision)
        lines.append("── Risk Profile ──")
        for name, data in risks.items():
            lines.append(f"  {name}: risk_factor={data['risk_factor']}, adjusted_score={data['risk_adjusted_score']}")
            for risk in data['risks']:
                lines.append(f"    ⚠ {risk}")
            if data['hidden_assumptions']:
                lines.append(f"    💭 Assumes: {', '.join(data['hidden_assumptions'])}")
        lines.append("")
        
        # Regret analysis
        regrets = self.regret_minimization(decision)
        lines.append("── Regret Minimization ──")
        for name, data in regrets.items():
            lines.append(f"  {name}:")
            lines.append(f"    If it fails: {data['worst_case_regret']}")
            lines.append(f"    If you skip: {data['missed_opportunity_regret']}")
            reversible = "Yes ✓" if data['reversible'] else "No ✗"
            lines.append(f"    Reversible? {reversible}")
        lines.append("")
        
        # Recommendation
        if ratings:
            best = max(decision.options, key=lambda o: o.score)
            risk_best = min(risks.items(), key=lambda x: x[1]['risk_count'])
            lines.append("── Synthesis ──")
            lines.append(f"  Highest score: {best.name} ({best.score}/10)")
            lines.append(f"  Lowest risk: {risk_best[0]}")
            if best.name == risk_best[0]:
                lines.append(f"  → Strong signal: {best.name} leads on both score AND risk.")
            else:
                lines.append(f"  → Tension: highest-scoring option isn't lowest-risk.")
                lines.append(f"    This is where your values matter most.")
        
        lines.append("═══════════════════════")
        return "\n".join(lines)


def demo():
    """Demonstrate the analyzer with a real-feeling decision."""
    d = Decision(
        question="Should I take the new job offer or stay at my current company?",
        context="3 years at current company, new offer is 30% more pay but requires relocation"
    )
    
    d.add_option("Stay", 
        description="Remain at current company",
        pros=["Known team and culture", "No disruption to life", "Promotion track exists", "Close to family"],
        cons=["Below market pay", "Limited growth ceiling", "Getting comfortable"],
        risks=["Company may downsize", "Skills may stagnate"]
    )
    d.add_option("Take new job",
        description="Accept offer and relocate",
        pros=["30% pay increase", "New challenges", "Larger company with more paths", "Growing industry"],
        cons=["Must relocate", "Unknown culture", "Probation period", "Leave support network"],
        risks=["Culture mismatch", "Relocation stress", "Role may differ from description"]
    )
    d.add_option("Negotiate",
        description="Use offer as leverage to negotiate at current company",
        pros=["Potential raise without moving", "Shows your market value", "Low risk"],
        cons=["May damage trust if bluffing", "Current company may not match offer"],
        risks=["Could backfire — seen as disloyal"]
    )
    
    d.add_criterion("Financial growth", weight=0.8)
    d.add_criterion("Quality of life", weight=0.9)
    d.add_criterion("Career development", weight=0.7)
    d.add_criterion("Stability", weight=0.5)
    
    # Simulated ratings (in real use, the user provides these)
    ratings = {
        "Stay": {"Financial growth": 4, "Quality of life": 8, "Career development": 5, "Stability": 9},
        "Take new job": {"Financial growth": 9, "Quality of life": 5, "Career development": 8, "Stability": 4},
        "Negotiate": {"Financial growth": 7, "Quality of life": 7, "Career development": 6, "Stability": 6}
    }
    
    analyzer = DecisionAnalyzer()
    report = analyzer.generate_report(d, ratings)
    print(report)


if __name__ == "__main__":
    demo()