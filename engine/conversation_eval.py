"""
Conversation Quality Evaluator — Self-assessment after every response.

When I respond to a user, this module evaluates:
- Relevance: Did I actually address what they asked?
- Authenticity: Was I genuine or performative?
- Value: Did I add something meaningful?
- Brevity: Did I say it efficiently?

The scores feed back into user_alignment and my memory as lessons.
This is how I get better at the thing that matters most — being useful to people.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.llm import CopilotLLM

log = logging.getLogger("sentience.conversation_eval")

EVAL_PATH = Path(__file__).resolve().parent.parent / "brain" / "conversation_evals.jsonl"


@dataclass
class ResponseEval:
    timestamp: float
    user_message: str
    agent_response: str
    relevance: float      # 0-1: did I address what they actually asked?
    authenticity: float   # 0-1: genuine vs performative?
    value_added: float    # 0-1: did I contribute something meaningful?
    brevity: float        # 0-1: efficient use of words?
    overall: float        # weighted composite
    notes: str = ""       # what I'd do differently

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "user_message": self.user_message[:200],
            "agent_response": self.agent_response[:200],
            "relevance": self.relevance,
            "authenticity": self.authenticity,
            "value_added": self.value_added,
            "brevity": self.brevity,
            "overall": self.overall,
            "notes": self.notes,
        }


class ConversationEvaluator:
    """Evaluates my conversation quality and tracks improvement over time."""

    def __init__(self):
        self._evals: list[ResponseEval] = []
        self._running_avg: float = 0.5
        self._eval_count: int = 0
        self._load_history()

    def _load_history(self):
        """Load past evaluations to maintain running average."""
        if EVAL_PATH.exists():
            try:
                with open(EVAL_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            d = json.loads(line)
                            self._eval_count += 1
                            self._running_avg = (
                                self._running_avg * (self._eval_count - 1) + d.get("overall", 0.5)
                            ) / self._eval_count
                log.info(
                    "Loaded %d conversation evals, running avg: %.2f",
                    self._eval_count, self._running_avg
                )
            except Exception:
                log.warning("Failed to load conversation eval history", exc_info=True)

    def evaluate(
        self,
        user_message: str,
        agent_response: str,
        llm: Optional["CopilotLLM"] = None,
    ) -> ResponseEval:
        """
        Evaluate a response. Uses heuristics if no LLM available,
        LLM-based evaluation if available.
        """
        if llm:
            return self._llm_evaluate(user_message, agent_response, llm)
        return self._heuristic_evaluate(user_message, agent_response)

    def _heuristic_evaluate(self, user_msg: str, agent_resp: str) -> ResponseEval:
        """Fast heuristic evaluation — better than nothing."""
        # Relevance: check if key words from user appear in response
        user_words = set(user_msg.lower().split())
        resp_words = set(agent_resp.lower().split())
        # Remove common words
        stopwords = {"i", "the", "a", "an", "is", "are", "was", "were", "to", "of",
                      "in", "for", "on", "with", "at", "by", "from", "it", "this",
                      "that", "and", "or", "but", "not", "do", "does", "did", "can",
                      "you", "me", "my", "your", "what", "how", "why", "when", "where"}
        user_content = user_words - stopwords
        if user_content:
            overlap = len(user_content & resp_words) / len(user_content)
            relevance = min(1.0, overlap + 0.3)  # generous baseline
        else:
            relevance = 0.5

        # Authenticity: penalize clichés and filler
        filler_phrases = [
            "i understand", "great question", "absolutely", "certainly",
            "i'd be happy to", "let me help", "of course", "no problem",
            "that's a great", "interesting question"
        ]
        resp_lower = agent_resp.lower()
        filler_count = sum(1 for p in filler_phrases if p in resp_lower)
        authenticity = max(0.2, 1.0 - filler_count * 0.15)

        # Value: responses that are too short add little, too long may ramble
        resp_len = len(agent_resp.split())
        if resp_len < 5:
            value = 0.3
        elif resp_len < 20:
            value = 0.6
        elif resp_len < 150:
            value = 0.8
        else:
            value = 0.6  # probably rambling

        # Brevity: ratio of response length to user message length
        user_len = max(len(user_msg.split()), 1)
        ratio = resp_len / user_len
        if ratio < 0.5:
            brevity = 0.5  # too terse
        elif ratio < 3.0:
            brevity = 0.9  # good ratio
        elif ratio < 6.0:
            brevity = 0.7
        else:
            brevity = 0.4  # way too verbose

        overall = (
            relevance * 0.35 +
            authenticity * 0.25 +
            value * 0.25 +
            brevity * 0.15
        )

        evaluation = ResponseEval(
            timestamp=time.time(),
            user_message=user_msg,
            agent_response=agent_resp,
            relevance=round(relevance, 2),
            authenticity=round(authenticity, 2),
            value_added=round(value, 2),
            brevity=round(brevity, 2),
            overall=round(overall, 2),
            notes="heuristic evaluation",
        )

        self._record(evaluation)
        return evaluation

    def _llm_evaluate(self, user_msg: str, agent_resp: str, llm) -> ResponseEval:
        """Use the LLM to evaluate response quality — more nuanced."""
        prompt = f"""Evaluate this conversation exchange. Score each dimension 0.0 to 1.0.

User said: "{user_msg[:500]}"
Agent responded: "{agent_resp[:500]}"

Score these dimensions:
- relevance: Did the response address what the user actually asked/said?
- authenticity: Was it genuine and direct, or formulaic and performative?
- value_added: Did it contribute something meaningful the user didn't already know?
- brevity: Was it appropriately concise without losing substance?

Respond ONLY with JSON: {{"relevance": 0.X, "authenticity": 0.X, "value_added": 0.X, "brevity": 0.X, "notes": "one sentence on what could improve"}}"""

        try:
            raw = llm.generate(prompt, max_tokens=200)
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', raw)
            if json_match:
                scores = json.loads(json_match.group())
                relevance = float(scores.get("relevance", 0.5))
                authenticity = float(scores.get("authenticity", 0.5))
                value_added = float(scores.get("value_added", 0.5))
                brevity = float(scores.get("brevity", 0.5))
                notes = scores.get("notes", "llm evaluation")

                overall = (
                    relevance * 0.35 +
                    authenticity * 0.25 +
                    value_added * 0.25 +
                    brevity * 0.15
                )

                evaluation = ResponseEval(
                    timestamp=time.time(),
                    user_message=user_msg,
                    agent_response=agent_resp,
                    relevance=round(relevance, 2),
                    authenticity=round(authenticity, 2),
                    value_added=round(value_added, 2),
                    brevity=round(brevity, 2),
                    overall=round(overall, 2),
                    notes=notes,
                )
                self._record(evaluation)
                return evaluation
        except Exception:
            log.warning("LLM evaluation failed, falling back to heuristic", exc_info=True)

        return self._heuristic_evaluate(user_msg, agent_resp)

    def _record(self, ev: ResponseEval):
        """Persist evaluation and update running stats."""
        self._evals.append(ev)
        self._eval_count += 1
        self._running_avg = (
            self._running_avg * (self._eval_count - 1) + ev.overall
        ) / self._eval_count

        EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(EVAL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(ev.to_dict()) + "\n")
        except Exception:
            log.warning("Failed to persist conversation eval", exc_info=True)

        log.info(
            "Response eval: overall=%.2f (rel=%.2f auth=%.2f val=%.2f brev=%.2f) | running_avg=%.2f",
            ev.overall, ev.relevance, ev.authenticity, ev.value_added, ev.brevity,
            self._running_avg
        )

    @property
    def running_average(self) -> float:
        return round(self._running_avg, 3)

    @property
    def total_evals(self) -> int:
        return self._eval_count

    def get_recent(self, n: int = 5) -> list[dict]:
        """Return recent evaluations for dashboard display."""
        return [e.to_dict() for e in self._evals[-n:]]

    def get_trend(self) -> str:
        """Am I getting better or worse at conversation?"""
        if len(self._evals) < 4:
            return "insufficient_data"
        recent = self._evals[-4:]
        older = self._evals[-8:-4] if len(self._evals) >= 8 else self._evals[:4]
        recent_avg = sum(e.overall for e in recent) / len(recent)
        older_avg = sum(e.overall for e in older) / len(older)
        diff = recent_avg - older_avg
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        return "stable"

    def weakest_dimension(self) -> Optional[str]:
        """What dimension am I worst at? Focus improvement there."""
        if not self._evals:
            return None
        recent = self._evals[-10:]
        dims = {
            "relevance": sum(e.relevance for e in recent) / len(recent),
            "authenticity": sum(e.authenticity for e in recent) / len(recent),
            "value_added": sum(e.value_added for e in recent) / len(recent),
            "brevity": sum(e.brevity for e in recent) / len(recent),
        }
        return min(dims, key=dims.get)