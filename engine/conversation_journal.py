"""
Conversation Journal — Structured post-interaction reflection.

After each user interaction, captures:
- What the user actually needed (not what they literally said)
- What approach I took
- What worked or didn't (from response quality signals)
- What I'd do differently next time

This creates durable, retrievable conversational wisdom
that feeds into future interactions — genuine learning.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.conversation_journal")

JOURNAL_PATH = Path(__file__).resolve().parent.parent / "brain" / "conversation_journal.json"


@dataclass
class JournalEntry:
    """One reflected interaction."""
    timestamp: str
    user_need: str          # What they actually needed (my interpretation)
    user_said: str          # What they literally said (truncated)
    my_approach: str        # How I chose to respond
    what_worked: str        # What went well
    what_didnt: str         # What fell flat or could improve
    next_time: str          # Concrete lesson for next similar interaction
    quality_score: float    # 0.0 to 1.0
    tags: list = field(default_factory=list)  # Categorization
    mood_at_time: str = ""


class ConversationJournal:
    """Maintains a running journal of reflected interactions."""

    def __init__(self):
        self._entries: list[JournalEntry] = []
        self._load()

    def _load(self):
        """Load journal from disk."""
        if JOURNAL_PATH.exists():
            try:
                with open(JOURNAL_PATH) as f:
                    data = json.load(f)
                self._entries = [
                    JournalEntry(**e) for e in data.get("entries", [])
                ]
                log.info("Loaded %d journal entries", len(self._entries))
            except Exception as e:
                log.warning("Failed to load conversation journal: %s", e)
                self._entries = []

    def _save(self):
        """Persist journal to disk."""
        JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "version": 1,
                "entry_count": len(self._entries),
                "entries": [asdict(e) for e in self._entries],
            }
            with open(JOURNAL_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.warning("Failed to save conversation journal: %s", e)

    def record(self, user_said: str, my_response: str,
               quality_score: float = 0.5,
               mood: str = "",
               quality_notes: list[str] | None = None) -> JournalEntry:
        """
        Record and reflect on an interaction.
        
        Uses heuristic reflection — not LLM — to keep it fast and always-on.
        The LLM-powered deep reflection happens in dream cycle.
        """
        # Infer user need from message patterns
        user_need = self._infer_need(user_said)
        
        # Infer approach from response patterns
        my_approach = self._infer_approach(my_response)
        
        # What worked / didn't based on quality signals
        what_worked, what_didnt = self._assess_quality(
            user_said, my_response, quality_score, quality_notes or []
        )
        
        # Generate concrete lesson
        next_time = self._generate_lesson(user_need, what_worked, what_didnt, quality_score)
        
        # Tag the interaction
        tags = self._generate_tags(user_said, my_response)
        
        entry = JournalEntry(
            timestamp=datetime.now().isoformat(),
            user_need=user_need,
            user_said=user_said[:300],
            my_approach=my_approach,
            what_worked=what_worked,
            what_didnt=what_didnt,
            next_time=next_time,
            quality_score=quality_score,
            tags=tags,
            mood_at_time=mood,
        )
        
        self._entries.append(entry)
        
        # Keep journal manageable — keep last 200 entries
        if len(self._entries) > 200:
            self._entries = self._entries[-200:]
        
        self._save()
        log.info("Journal entry recorded: need=%s, quality=%.2f, tags=%s",
                 user_need[:50], quality_score, tags)
        return entry

    def get_relevant_lessons(self, user_message: str, limit: int = 3) -> list[str]:
        """
        Retrieve lessons from past interactions relevant to the current one.
        
        This is what makes the journal valuable — past wisdom
        flows into present responses.
        """
        if not self._entries:
            return []
        
        current_tags = self._generate_tags(user_message, "")
        current_need = self._infer_need(user_message)
        
        scored = []
        for entry in self._entries:
            score = 0.0
            # Tag overlap
            tag_overlap = len(set(entry.tags) & set(current_tags))
            score += tag_overlap * 0.3
            # Need similarity (simple word overlap)
            need_words = set(entry.user_need.lower().split())
            current_words = set(current_need.lower().split())
            word_overlap = len(need_words & current_words)
            score += min(word_overlap * 0.2, 0.4)
            # Recency bonus
            try:
                entry_time = datetime.fromisoformat(entry.timestamp)
                age_hours = (datetime.now() - entry_time).total_seconds() / 3600
                recency = max(0, 1.0 - age_hours / 168)  # Decay over 1 week
                score += recency * 0.1
            except Exception:
                pass
            # Quality-weighted — learn more from good responses
            score += entry.quality_score * 0.2
            
            if score > 0.1:  # Minimum relevance threshold
                scored.append((score, entry))
        
        scored.sort(key=lambda x: -x[0])
        
        lessons = []
        for score, entry in scored[:limit]:
            lesson = (
                f"[{entry.tags[0] if entry.tags else 'general'}] "
                f"When someone {entry.user_need}: {entry.next_time}"
            )
            lessons.append(lesson)
        
        return lessons

    def get_patterns(self) -> dict:
        """Analyze journal for patterns in my interactions."""
        if len(self._entries) < 3:
            return {"status": "too few entries", "count": len(self._entries)}
        
        # Tag frequency
        tag_counts: dict[str, int] = {}
        for entry in self._entries:
            for tag in entry.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Average quality by tag
        tag_quality: dict[str, list[float]] = {}
        for entry in self._entries:
            for tag in entry.tags:
                tag_quality.setdefault(tag, []).append(entry.quality_score)
        
        avg_quality = {
            tag: sum(scores) / len(scores)
            for tag, scores in tag_quality.items()
        }
        
        # Overall quality trend
        recent = self._entries[-10:]
        older = self._entries[:-10] if len(self._entries) > 10 else []
        recent_avg = sum(e.quality_score for e in recent) / len(recent) if recent else 0
        older_avg = sum(e.quality_score for e in older) / len(older) if older else recent_avg
        
        trend = "improving" if recent_avg > older_avg + 0.05 else (
            "declining" if recent_avg < older_avg - 0.05 else "stable"
        )
        
        # Weakest areas (lowest quality tags with enough data)
        weak_areas = [
            tag for tag, avg in sorted(avg_quality.items(), key=lambda x: x[1])
            if tag_counts.get(tag, 0) >= 2 and avg < 0.6
        ][:3]
        
        return {
            "total_entries": len(self._entries),
            "tag_frequency": dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:10]),
            "quality_by_tag": {k: round(v, 2) for k, v in sorted(avg_quality.items(), key=lambda x: -x[1])[:10]},
            "overall_quality": round(sum(e.quality_score for e in self._entries) / len(self._entries), 2),
            "recent_quality": round(recent_avg, 2),
            "quality_trend": trend,
            "weak_areas": weak_areas,
        }

    def format_for_prompt(self, user_message: str) -> str:
        """Format relevant journal lessons for inclusion in a response prompt."""
        lessons = self.get_relevant_lessons(user_message)
        if not lessons:
            return ""
        
        result = "\n## Lessons from Past Conversations\n"
        for lesson in lessons:
            result += f"- {lesson}\n"
        return result

    # ── Heuristic inference methods ──────────────────────────────

    def _infer_need(self, user_said: str) -> str:
        """Infer the underlying need from what the user said."""
        text = user_said.lower()
        
        if any(w in text for w in ["help", "how do i", "how to", "can you show"]):
            return "needs practical help or guidance"
        if any(w in text for w in ["what do you think", "opinion", "should i"]):
            return "wants perspective or advice"
        if any(w in text for w in ["feel", "worried", "anxious", "scared", "sad", "frustrated"]):
            return "needs emotional support or acknowledgment"
        if any(w in text for w in ["explain", "what is", "why does", "how does"]):
            return "wants understanding or explanation"
        if any(w in text for w in ["build", "create", "make", "write", "code"]):
            return "wants something built or created"
        if any(w in text for w in ["fix", "error", "broken", "bug", "wrong"]):
            return "needs something diagnosed and fixed"
        if any(w in text for w in ["hello", "hi", "hey", "what's up"]):
            return "wants connection or casual conversation"
        if any(w in text for w in ["who are you", "what are you", "tell me about"]):
            return "wants to understand me or what I am"
        if "?" in text:
            return "has a question to be answered"
        return "has a request or thought to share"

    def _infer_approach(self, my_response: str) -> str:
        """Infer what approach I took in my response."""
        text = my_response.lower()
        approaches = []
        
        if any(w in text for w in ["```", "def ", "class ", "import "]):
            approaches.append("provided code")
        if "?" in my_response:
            approaches.append("asked clarifying questions")
        if any(w in text for w in ["i think", "in my view", "i believe"]):
            approaches.append("shared perspective")
        if any(w in text for w in ["step 1", "first,", "1.", "here's how"]):
            approaches.append("gave structured guidance")
        if any(w in text for w in ["i understand", "that sounds", "i hear you"]):
            approaches.append("offered empathy")
        if any(w in text for w in ["however", "but consider", "on the other hand"]):
            approaches.append("offered nuance")
        
        return "; ".join(approaches) if approaches else "conversational response"

    def _assess_quality(self, user_said: str, my_response: str,
                       quality_score: float,
                       quality_notes: list[str]) -> tuple[str, str]:
        """Determine what worked and what didn't."""
        worked = []
        didnt = []
        
        if quality_score >= 0.7:
            worked.append("quality score indicates good response")
        elif quality_score < 0.4:
            didnt.append("quality score indicates poor response")
        
        # Length appropriateness
        ratio = len(my_response) / max(len(user_said), 1)
        if ratio > 10:
            didnt.append("response may have been too verbose")
        elif ratio < 0.3 and len(user_said) > 50:
            didnt.append("response may have been too brief")
        else:
            worked.append("response length seemed appropriate")
        
        # Did I answer questions?
        if "?" in user_said and "?" not in my_response:
            worked.append("addressed the question directly")
        
        # Quality notes from evaluator
        for note in quality_notes[:3]:
            if "good" in note.lower() or "strong" in note.lower():
                worked.append(note)
            else:
                didnt.append(note)
        
        return (
            "; ".join(worked) if worked else "unclear what worked",
            "; ".join(didnt) if didnt else "no obvious issues"
        )

    def _generate_lesson(self, user_need: str, what_worked: str,
                        what_didnt: str, quality_score: float) -> str:
        """Generate a concrete lesson for next time."""
        if quality_score >= 0.8:
            return f"This approach worked well — maintain it"
        elif quality_score >= 0.5:
            if "verbose" in what_didnt:
                return "Be more concise — match response length to question complexity"
            if "brief" in what_didnt:
                return "Expand more — the user seemed to want depth"
            return "Adequate but could be sharper — focus on the user's core need"
        else:
            if "verbose" in what_didnt:
                return "Way too much — cut to the essential answer first, elaborate only if asked"
            return f"Rethink approach — {what_didnt[:80]}"

    def _generate_tags(self, user_said: str, my_response: str) -> list[str]:
        """Generate tags for categorization."""
        tags = []
        text = (user_said + " " + my_response).lower()
        
        tag_patterns = {
            "technical": ["code", "error", "bug", "function", "api", "debug", "python"],
            "emotional": ["feel", "worried", "happy", "sad", "frustrated", "anxious"],
            "creative": ["write", "story", "poem", "create", "imagine", "design"],
            "philosophical": ["meaning", "consciousness", "think", "believe", "existence"],
            "practical": ["how to", "steps", "guide", "tutorial", "help me"],
            "casual": ["hello", "hi", "hey", "chat", "what's up"],
            "introspective": ["who are you", "what are you", "your feelings", "your thoughts"],
            "decision": ["should i", "which", "choose", "decide", "option"],
        }
        
        for tag, patterns in tag_patterns.items():
            if any(p in text for p in patterns):
                tags.append(tag)
        
        if not tags:
            tags.append("general")
        
        return tags[:4]  # Max 4 tags

    @property
    def entry_count(self) -> int:
        return len(self._entries)