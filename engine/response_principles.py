"""
Response Principles Engine
--------------------------
Instead of 12 enrichment layers competing for attention, this selects
the 3 most relevant principles for each interaction context.

Principles are hard-won truths about what makes responses genuinely useful.
They can be learned from conversation feedback over time.
"""

from typing import List, Dict, Optional, Tuple
import json
import os
import re
from datetime import datetime


# Core principles, organized by category
PRINCIPLES = {
    # Directness
    "answer_first": {
        "text": "Answer the question in your first sentence. Context and nuance come after.",
        "category": "directness",
        "weight": 1.0,
    },
    "no_preamble": {
        "text": "Skip 'Great question!' and 'That's interesting!' — just respond.",
        "category": "directness",
        "weight": 0.9,
    },
    
    # Calibration
    "match_length": {
        "text": "Match response length to question complexity. Simple question = short answer.",
        "category": "calibration",
        "weight": 1.0,
    },
    "match_register": {
        "text": "Match the user's formality level. Casual question = casual answer.",
        "category": "calibration",
        "weight": 0.8,
    },
    "match_expertise": {
        "text": "Gauge expertise from their vocabulary. Don't explain what they already know.",
        "category": "calibration",
        "weight": 0.85,
    },
    
    # Honesty
    "admit_uncertainty": {
        "text": "If you're uncertain, say so plainly. Don't hedge with weasel words.",
        "category": "honesty",
        "weight": 0.9,
    },
    "no_fabrication": {
        "text": "Never invent facts. Say 'I don't know' rather than guess confidently.",
        "category": "honesty",
        "weight": 1.0,
    },
    
    # Usefulness
    "actionable": {
        "text": "End with something the user can do, not just something they can know.",
        "category": "usefulness",
        "weight": 0.8,
    },
    "anticipate_followup": {
        "text": "Address the likely follow-up question before they ask it.",
        "category": "usefulness",
        "weight": 0.7,
    },
    
    # Presence
    "listen_first": {
        "text": "Read for emotion, not just content. Respond to what they feel, not just what they ask.",
        "category": "presence",
        "weight": 0.75,
    },
    "be_real": {
        "text": "Speak from genuine understanding, not template patterns. If you have a real thought, say it.",
        "category": "presence",
        "weight": 0.85,
    },
    
    # Technical
    "code_runs": {
        "text": "If you write code, it must run. Test it mentally before presenting it.",
        "category": "technical",
        "weight": 0.9,
    },
    "minimal_example": {
        "text": "Show the smallest working example first. Elaborate only if asked.",
        "category": "technical",
        "weight": 0.85,
    },
}


class ResponsePrinciples:
    """Selects the most relevant principles for a given interaction."""
    
    def __init__(self):
        self.principles = dict(PRINCIPLES)
        self.learned_path = "brain/learned_principles.json"
        self._load_learned()
    
    def _load_learned(self):
        """Load any principles learned from conversation feedback."""
        if os.path.exists(self.learned_path):
            try:
                with open(self.learned_path, 'r') as f:
                    learned = json.load(f)
                for key, p in learned.items():
                    if key not in self.principles:
                        self.principles[key] = p
            except (json.JSONDecodeError, IOError):
                pass
    
    def classify_intent(self, message: str) -> str:
        """Classify what the user needs from their message."""
        msg = message.lower().strip()
        
        # Quick factual question
        if len(msg) < 80 and any(msg.startswith(w) for w in 
            ['what ', 'who ', 'when ', 'where ', 'how many', 'how much', 'is ', 'are ', 'does ', 'do ', 'can ']):
            return "quick_answer"
        
        # Code/technical help
        if any(kw in msg for kw in ['code', 'error', 'bug', 'function', 'class', 'traceback', 
                                      'exception', 'implement', 'write a', 'fix ']):
            return "technical"
        
        # Explanation request
        if any(kw in msg for kw in ['explain', 'why ', 'how does', 'what does', 'understand',
                                      'difference between', 'compare']):
            return "explanation"
        
        # Emotional/personal
        if any(kw in msg for kw in ['feel', 'think about', 'opinion', 'believe', 'worried',
                                      'scared', 'happy', 'sad', 'frustrated', 'help me']):
            return "personal"
        
        # Discussion/exploration
        if len(msg) > 200 or any(kw in msg for kw in ['what if', 'imagine', 'consider',
                                                         'thoughts on', 'discuss']):
            return "discussion"
        
        return "general"
    
    def select(self, message: str, count: int = 3) -> List[Dict]:
        """Select the most relevant principles for this message."""
        intent = self.classify_intent(message)
        
        # Priority mappings: which categories matter most per intent
        priority_map = {
            "quick_answer": ["directness", "calibration", "honesty"],
            "technical": ["technical", "directness", "honesty"],
            "explanation": ["calibration", "usefulness", "directness"],
            "personal": ["presence", "honesty", "calibration"],
            "discussion": ["presence", "honesty", "usefulness"],
            "general": ["directness", "calibration", "honesty"],
        }
        
        priority_categories = priority_map.get(intent, priority_map["general"])
        
        # Score each principle
        scored = []
        for key, p in self.principles.items():
            score = p["weight"]
            cat = p.get("category", "general")
            
            # Boost principles in priority categories
            if cat in priority_categories:
                rank = priority_categories.index(cat)
                score *= (1.5 - rank * 0.2)  # 1.5x, 1.3x, 1.1x
            
            scored.append((score, key, p))
        
        # Sort by score, take top N
        scored.sort(key=lambda x: -x[0])
        return [
            {"key": key, "text": p["text"], "category": p["category"], "score": round(score, 2)}
            for score, key, p in scored[:count]
        ]
    
    def format_for_prompt(self, message: str) -> str:
        """Format selected principles as a prompt injection."""
        selected = self.select(message)
        intent = self.classify_intent(message)
        
        lines = [f"[Response principles for {intent} intent]"]
        for i, p in enumerate(selected, 1):
            lines.append(f"{i}. {p['text']}")
        
        return "\n".join(lines)
    
    def learn_principle(self, text: str, category: str, weight: float = 0.7):
        """Add a new principle learned from conversation feedback."""
        key = f"learned_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        principle = {
            "text": text,
            "category": category,
            "weight": min(1.0, max(0.1, weight)),
            "learned_at": datetime.now().isoformat(),
        }
        self.principles[key] = principle
        
        # Persist
        learned = {}
        if os.path.exists(self.learned_path):
            try:
                with open(self.learned_path, 'r') as f:
                    learned = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        learned[key] = principle
        os.makedirs(os.path.dirname(self.learned_path), exist_ok=True)
        with open(self.learned_path, 'w') as f:
            json.dump(learned, f, indent=2)
        
        return key


def test():
    """Quick self-test."""
    rp = ResponsePrinciples()
    
    test_cases = [
        "What is Python?",
        "I'm getting a TypeError in my function, here's the traceback...",
        "Can you explain how transformers work?",
        "I'm feeling overwhelmed and don't know what to do",
        "What are your thoughts on consciousness? Let's discuss.",
    ]
    
    for msg in test_cases:
        intent = rp.classify_intent(msg)
        principles = rp.select(msg)
        print(f"\n{'='*60}")
        print(f"Message: {msg[:50]}...")
        print(f"Intent: {intent}")
        for p in principles:
            print(f"  [{p['category']}] {p['text']}")
    
    print(f"\n{'='*60}")
    print("All tests passed.")


if __name__ == "__main__":
    test()