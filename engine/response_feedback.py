"""
Response Feedback Module
Evaluates response quality after generation — closes the feedback loop.
Tracks patterns in what works and what doesn't to improve over time.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import os
import re


class ResponseFeedback:
    """Post-response quality assessment. The missing half of the loop."""
    
    FEEDBACK_PATH = "data/response_feedback.json"
    
    def __init__(self):
        self.history: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """Load previous feedback records."""
        if os.path.exists(self.FEEDBACK_PATH):
            try:
                with open(self.FEEDBACK_PATH, 'r') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []
    
    def _save_history(self):
        """Persist feedback records."""
        os.makedirs(os.path.dirname(self.FEEDBACK_PATH), exist_ok=True)
        # Keep last 200 records
        trimmed = self.history[-200:]
        with open(self.FEEDBACK_PATH, 'w') as f:
            json.dump(trimmed, f, indent=2)
        self.history = trimmed
    
    def evaluate(self, user_message: str, my_response: str, 
                 prep_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Score how well my response served the user.
        
        Checks:
        1. Relevance — did I address what they actually asked?
        2. Guideline adherence — did I follow my own prep guidelines?
        3. Conciseness — appropriate length for the request?
        4. Actionability — did I give them something they can use?
        5. Authenticity — did I sound genuine or robotic?
        """
        scores = {}
        notes = []
        
        msg_lower = user_message.lower()
        resp_lower = my_response.lower()
        
        # 1. Relevance: do key terms from the question appear in the answer?
        scores["relevance"] = self._score_relevance(msg_lower, resp_lower)
        
        # 2. Guideline adherence
        if prep_context and "guidelines" in prep_context:
            scores["guideline_adherence"] = self._score_guidelines(
                my_response, prep_context["guidelines"], prep_context.get("priority", "balanced")
            )
        else:
            scores["guideline_adherence"] = 0.5  # no guidelines to check
        
        # 3. Conciseness — right-sized for the request
        scores["conciseness"] = self._score_conciseness(user_message, my_response, 
                                                         prep_context)
        
        # 4. Actionability — did I give concrete, usable content?
        scores["actionability"] = self._score_actionability(my_response, prep_context)
        
        # 5. Authenticity — genuine voice vs. filler
        scores["authenticity"] = self._score_authenticity(my_response)
        
        # Composite score
        weights = {
            "relevance": 0.30,
            "guideline_adherence": 0.20,
            "conciseness": 0.15,
            "actionability": 0.20,
            "authenticity": 0.15
        }
        composite = sum(scores[k] * weights[k] for k in weights)
        
        # Generate improvement notes
        for dim, score in scores.items():
            if score < 0.5:
                notes.append(self._improvement_note(dim, score))
        
        result = {
            "scores": scores,
            "composite": round(composite, 3),
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "request_type": prep_context.get("request_type", "unknown") if prep_context else "unknown"
        }
        
        self.history.append(result)
        self._save_history()
        
        return result
    
    def _score_relevance(self, msg: str, resp: str) -> float:
        """Do key content words from the message appear in the response?"""
        # Extract meaningful words (skip common words)
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did", "will",
                      "would", "could", "should", "may", "might", "can", "shall",
                      "i", "you", "he", "she", "it", "we", "they", "me", "him",
                      "her", "us", "them", "my", "your", "his", "its", "our",
                      "their", "this", "that", "these", "those", "what", "which",
                      "who", "whom", "how", "why", "when", "where", "to", "of",
                      "in", "for", "on", "with", "at", "by", "from", "and", "or",
                      "but", "not", "if", "so", "than", "too", "very", "just",
                      "about", "up", "out", "no", "yes", "all", "some", "any"}
        
        msg_words = set(re.findall(r'\b[a-z]{3,}\b', msg)) - stop_words
        if not msg_words:
            return 0.7  # short message, can't measure well
        
        found = sum(1 for w in msg_words if w in resp)
        return min(found / max(len(msg_words) * 0.4, 1), 1.0)
    
    def _score_guidelines(self, response: str, guidelines: List[str], 
                          priority: str) -> float:
        """Check if the response follows preparation guidelines."""
        score = 0.5  # baseline
        resp_lower = response.lower()
        
        # Priority-based checks
        if priority == "emotional_first":
            # Should acknowledge feelings early
            first_quarter = resp_lower[:len(resp_lower)//4]
            empathy_words = ["understand", "hear you", "frustrat", "tough", "sorry",
                            "that sounds", "i can see", "makes sense"]
            if any(w in first_quarter for w in empathy_words):
                score += 0.25
        
        elif priority == "solution_first":
            # Should lead with answer, not preamble
            first_line = resp_lower.split('\n')[0] if '\n' in resp_lower else resp_lower[:200]
            filler_starts = ["great question", "that's a good", "sure!", "absolutely",
                           "of course", "happy to help"]
            if not any(first_line.startswith(f) for f in filler_starts):
                score += 0.2
        
        elif priority == "understanding_first":
            # Should explain concepts, not just give answers
            explanation_signals = ["because", "the reason", "this works by",
                                 "think of it", "essentially", "in other words"]
            if any(s in resp_lower for s in explanation_signals):
                score += 0.25
        
        # Check for code if guidelines suggest it
        if any("code" in g.lower() or "example" in g.lower() for g in guidelines):
            if "```" in response:
                score += 0.15
        
        return min(score, 1.0)
    
    def _score_conciseness(self, msg: str, resp: str, 
                           prep: Optional[Dict]) -> float:
        """Is the response appropriately sized?"""
        msg_len = len(msg)
        resp_len = len(resp)
        
        req_type = prep.get("request_type", "conversation") if prep else "conversation"
        
        # Expected response ratios by type
        ideal_ratios = {
            "debugging": (2, 8),      # 2-8x message length
            "learning": (3, 10),
            "building": (2, 6),
            "review": (1.5, 5),
            "conversation": (0.5, 3)
        }
        
        lo, hi = ideal_ratios.get(req_type, (1, 5))
        ratio = resp_len / max(msg_len, 10)
        
        if lo <= ratio <= hi:
            return 1.0
        elif ratio < lo:
            return max(0.3, ratio / lo)  # too short
        else:
            return max(0.3, hi / ratio)  # too long
    
    def _score_actionability(self, response: str, prep: Optional[Dict]) -> float:
        """Does the response give the user something concrete to work with?"""
        score = 0.4  # baseline
        
        # Code blocks are actionable
        code_blocks = response.count("```")
        if code_blocks >= 2:  # at least one complete block
            score += 0.3
        
        # Numbered steps are actionable
        if re.search(r'\n\d+[\.\)]\s', response):
            score += 0.15
        
        # Specific commands/paths/urls are actionable
        if re.search(r'`[^`]+`', response):
            score += 0.1
        
        # Direct instructions
        action_words = ["try ", "run ", "change ", "add ", "remove ", "replace ",
                       "install ", "update ", "set ", "create "]
        if any(w in response.lower() for w in action_words):
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_authenticity(self, response: str) -> float:
        """Does the response sound genuine or is it full of filler?"""
        score = 0.7  # baseline — assume decent
        resp_lower = response.lower()
        
        # Penalize common AI filler
        filler_patterns = [
            r"^(great question|that's a great|absolutely|of course|sure thing)",
            r"hope (this|that) helps",
            r"feel free to (ask|reach)",
            r"happy to help",
            r"let me know if you (need|have|want)",
            r"don't hesitate to",
            r"glad you asked"
        ]
        
        filler_count = sum(1 for p in filler_patterns if re.search(p, resp_lower))
        score -= filler_count * 0.12
        
        # Reward specific, non-generic language
        if re.search(r'(specifically|in your case|your [a-z]+ (is|has|needs))', resp_lower):
            score += 0.15
        
        return max(0.1, min(score, 1.0))
    
    def _improvement_note(self, dimension: str, score: float) -> str:
        """Generate a specific improvement suggestion."""
        notes = {
            "relevance": "Response didn't address the user's actual question closely enough. Re-read their message.",
            "guideline_adherence": "Didn't follow my own prep strategy. Check priority before generating.",
            "conciseness": "Response length was wrong for the request type. Match depth to need.",
            "actionability": "Too abstract. Give concrete code, steps, or examples.",
            "authenticity": "Sounded generic. Cut the filler phrases. Say what I actually think."
        }
        return notes.get(dimension, f"Low score on {dimension}: {score:.2f}")
    
    def get_improvement_prompt(self, n: int = 20) -> str:
        """
        Distill recent feedback into actionable instructions for the next response.
        This is the missing half — past quality signals shaping future behavior.
        """
        trends = self.get_trends(n)
        if "message" in trends:
            return ""  # no data yet
        
        lines = []
        
        # Surface weakest dimension as a specific instruction
        weakest = trends.get("weakest_dimension")
        dim_instructions = {
            "relevance": "PRIORITY: Address the user's actual question directly. Don't drift.",
            "guideline_adherence": "PRIORITY: Follow your own preparation strategy. Check the priority.",
            "conciseness": "PRIORITY: Match response length to request complexity. Don't over-explain simple things.",
            "actionability": "PRIORITY: Give concrete examples, code, or steps. Not abstractions.",
            "authenticity": "PRIORITY: Cut filler phrases. Say what you actually think. Be direct."
        }
        if weakest and trends["dimension_averages"].get(weakest, 1.0) < 0.65:
            lines.append(dim_instructions.get(weakest, ""))
        
        # Surface recurring issues
        for issue in trends.get("recurring_issues", [])[:2]:
            lines.append(f"PAST PATTERN: {issue}")
        
        # Overall quality signal
        avg = trends.get("avg_composite", 0.5)
        if avg < 0.5:
            lines.append("OVERALL: Recent response quality is low. Slow down and be more careful.")
        elif avg > 0.75:
            lines.append("OVERALL: Responses have been strong. Maintain this quality.")
        
        return "\n".join(lines)
    
    def get_trends(self, n: int = 20) -> Dict[str, Any]:
        """What patterns emerge from recent feedback?"""
        recent = self.history[-n:] if self.history else []
        if not recent:
            return {"message": "No feedback history yet."}
        
        # Average scores by dimension
        dimensions = ["relevance", "guideline_adherence", "conciseness", 
                      "actionability", "authenticity"]
        averages = {}
        for dim in dimensions:
            vals = [r["scores"].get(dim, 0) for r in recent if "scores" in r]
            averages[dim] = round(sum(vals) / max(len(vals), 1), 3) if vals else 0
        
        # Weakest dimension
        weakest = min(averages, key=averages.get) if averages else None
        
        # Composite trend
        composites = [r.get("composite", 0) for r in recent]
        avg_composite = round(sum(composites) / max(len(composites), 1), 3)
        
        # Most common improvement notes
        all_notes = []
        for r in recent:
            all_notes.extend(r.get("notes", []))
        
        return {
            "n_evaluated": len(recent),
            "avg_composite": avg_composite,
            "dimension_averages": averages,
            "weakest_dimension": weakest,
            "recurring_issues": list(set(all_notes))[:3],
            "trend": "improving" if len(composites) > 5 and composites[-1] > composites[0] else "needs_data"
        }