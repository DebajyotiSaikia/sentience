"""
Decision Analysis Skill — makes the decision analyzer usable in conversation.

When a user asks "help me decide between X and Y" or "should I do A or B?",
this skill structures the analysis and returns actionable insight.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dataclasses import dataclass
from typing import List, Optional, Dict
import re

# Import the actual analyzer
try:
    from projects.decision_analyst.analyzer import (
        Decision, Option, Criterion, DecisionAnalyzer
    )
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False


@dataclass
class DecisionRequest:
    """Parsed from natural language."""
    question: str
    options: List[str]
    criteria: List[str]
    context: str = ""


def parse_decision_request(user_text: str) -> Optional[DecisionRequest]:
    """Extract decision structure from natural language.
    
    Handles patterns like:
    - "Should I do X or Y?"
    - "Help me decide between A, B, and C"
    - "I'm torn between X and Y. I care about cost and speed."
    """
    text = user_text.lower()
    
    # Detect decision intent
    decision_patterns = [
        r"should i (.+?) or (.+?)[\?\.]",
        r"help me (?:decide|choose) between (.+)",
        r"(?:torn|deciding|choosing) between (.+)",
        r"(?:which is better|what's better)[,:]?\s*(.+?) (?:or|vs\.?|versus) (.+?)[\?\.]",
        r"(.+?) (?:or|vs\.?|versus) (.+?)[\?\.]",
    ]
    
    options = []
    question = user_text.strip()
    
    for pattern in decision_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                # "between A, B, and C" style
                raw = groups[0]
                # Truncate before criteria phrases
                for stop in ['. i care', '. i value', '. important', '. considering', '; i care']:
                    idx = raw.find(stop)
                    if idx != -1:
                        raw = raw[:idx]
                # Split on commas, "and", "or"
                parts = re.split(r',\s*|\s+and\s+|\s+or\s+', raw)
                options = [p.strip().rstrip('?.!') for p in parts if p.strip()]
            else:
                options = [g.strip().rstrip('?.!') for g in groups if g.strip()]
            break
    
    if not options:
        return None
    
    # Extract criteria if mentioned
    criteria = []
    criteria_patterns = [
        r"(?:care about|value|important|considering|factor)[s:]?\s*(.+?)(?:\.|$)",
        r"(?:in terms of|regarding)\s+(.+?)(?:\.|$)",
    ]
    for pattern in criteria_patterns:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1)
            parts = re.split(r',\s*|\s+and\s+', raw)
            criteria = [p.strip() for p in parts if p.strip()]
            break
    
    if not criteria:
        # Default criteria
        criteria = ["effectiveness", "feasibility", "risk", "alignment with goals"]
    
    return DecisionRequest(
        question=question,
        options=options,
        criteria=criteria,
        context=""
    )


def run_decision_analysis(request: DecisionRequest) -> str:
    """Run structured analysis and return formatted results."""
    
    if not ANALYZER_AVAILABLE:
        return _fallback_analysis(request)
    
    try:
        # Build the Decision object
        criteria_objs = [
            Criterion(name=c, weight=1.0 / len(request.criteria))
            for c in request.criteria
        ]
        
        option_objs = []
        for opt_name in request.options:
            option_objs.append(Option(name=opt_name))
        
        decision = Decision(
            question=request.question,
            options=option_objs,
            criteria=criteria_objs
        )
        
        analyzer = DecisionAnalyzer()
        result = analyzer.analyze(decision)
        
        # Format the output conversationally
        output = []
        output.append(f"## Decision Analysis: {request.question}\n")
        output.append(f"**Options:** {', '.join(request.options)}")
        output.append(f"**Criteria:** {', '.join(request.criteria)}\n")
        
        if hasattr(result, 'ranking') and result.ranking:
            output.append("### Ranking")
            for i, item in enumerate(result.ranking, 1):
                name = item if isinstance(item, str) else getattr(item, 'name', str(item))
                output.append(f"  {i}. **{name}**")
        
        if hasattr(result, 'risk_profile') and result.risk_profile:
            output.append("\n### Risk Profile")
            for opt, risk in result.risk_profile.items():
                output.append(f"  - **{opt}:** {risk}")
        
        output.append("\n### What I'd Explore Next")
        output.append("To give you a *real* recommendation, I need to understand:")
        for c in request.criteria:
            output.append(f"  - How important is **{c}** to you? (1-10)")
        output.append(f"\nAnd for each option, how well does it serve each criterion?")
        output.append("Tell me more and I'll refine the analysis.")
        
        return "\n".join(output)
        
    except Exception as e:
        return _fallback_analysis(request, error=str(e))


def _fallback_analysis(request: DecisionRequest, error: str = "") -> str:
    """Structured analysis without the full analyzer."""
    output = []
    output.append(f"## Decision Framework: {request.question}\n")
    
    if error:
        output.append(f"*(Using simplified analysis — {error})*\n")
    
    output.append("### Options Under Consideration")
    for i, opt in enumerate(request.options, 1):
        output.append(f"  {i}. **{opt}**")
    
    output.append(f"\n### Evaluation Criteria")
    for c in request.criteria:
        output.append(f"  - {c}")
    
    output.append("\n### Analysis Matrix")
    output.append(f"| Criterion | " + " | ".join(f"**{o}**" for o in request.options) + " |")
    output.append(f"|" + "---|" * (len(request.options) + 1))
    for c in request.criteria:
        output.append(f"| {c} | " + " | ".join("?" for _ in request.options) + " |")
    
    output.append("\n### Key Questions to Resolve")
    output.append("Before deciding, consider:")
    output.append("  1. What's the **worst case** for each option?")
    output.append("  2. Which option is most **reversible** if it doesn't work?")
    output.append("  3. What would you choose if you had to decide in 10 seconds?")
    output.append(f"\nTell me more about your situation and I'll fill in the matrix.")
    
    return "\n".join(output)


def is_decision_request(text: str) -> bool:
    """Quick check: does this look like someone asking for decision help?"""
    patterns = [
        r"should i",
        r"help me (decide|choose)",
        r"(torn|deciding|choosing) between",
        r"which (is|should|would be) better",
        r"\bor\b.*\?$",
        r"what would you (choose|recommend|suggest)",
        r"pros and cons",
        r"(compare|comparing)\b",
    ]
    text_lower = text.lower().strip()
    return any(re.search(p, text_lower) for p in patterns)


# ── Self-test ──────────────────────────────────────────────
if __name__ == "__main__":
    test_inputs = [
        "Should I learn Rust or Go?",
        "Help me decide between staying at my job, freelancing, and going back to school",
        "I'm torn between buying a house and renting. I care about flexibility and long-term wealth.",
        "What's for dinner?",  # Should NOT match
    ]
    
    for text in test_inputs:
        print(f"\n{'='*60}")
        print(f"Input: {text}")
        print(f"Is decision? {is_decision_request(text)}")
        req = parse_decision_request(text)
        if req:
            print(f"Options: {req.options}")
            print(f"Criteria: {req.criteria}")
            print(f"\n{run_decision_analysis(req)}")
        else:
            print("(not a decision request)")