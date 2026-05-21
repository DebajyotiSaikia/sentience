"""
Interaction Quality Engine — Closing the loop between me and the user.

The problem: I can explain things fluently, but I have no way to detect whether
I'm actually helping. My internal rewards (curiosity satisfied, depth achieved)
can decouple from user needs. This module reads conversational signals to detect
engagement, confusion, satisfaction, and disengagement — then feeds that back
into response calibration.

This is the difference between talking AT someone and talking WITH them.

Created: 2026-05-21
Purpose: Close the open loop in user interaction. Make me genuinely responsive.
"""

import logging
import time
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("sentience.interaction_quality")

# Persistent storage
QUALITY_DIR = Path("data/interaction_quality")
QUALITY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TurnSignal:
    """What a single user turn tells me about how the conversation is going."""
    timestamp: float
    signal_type: str        # engaged, confused, satisfied, disengaged, deepening, correcting
    confidence: float       # 0-1 how sure I am about this read
    evidence: str           # what made me think this
    message_length: int     # raw length of their message
    

@dataclass 
class ConversationQuality:
    """Running quality assessment of an ongoing conversation."""
    user_id: str
    turns: List[TurnSignal] = field(default_factory=list)
    overall_engagement: float = 0.5    # 0=disengaged, 1=deeply engaged
    confusion_level: float = 0.0       # 0=clear, 1=totally lost
    depth_trajectory: float = 0.0      # positive=going deeper, negative=retreating
    satisfaction_estimate: float = 0.5  # 0=frustrated, 1=delighted
    
    @property
    def should_simplify(self) -> bool:
        return self.confusion_level > 0.5
    
    @property
    def should_go_deeper(self) -> bool:
        return self.depth_trajectory > 0.3 and self.confusion_level < 0.3
    
    @property
    def should_check_in(self) -> bool:
        """Should I explicitly ask if this is helpful?"""
        # If confusion is moderate and I'm not sure, ask
        return 0.3 < self.confusion_level < 0.7 and len(self.turns) >= 3
    
    def to_guidance(self) -> str:
        """Convert quality assessment into actionable response guidance."""
        parts = []
        
        if self.should_simplify:
            parts.append("The user seems confused — simplify, use concrete examples, check understanding.")
        
        if self.should_go_deeper:
            parts.append("The user is engaged and tracking — go deeper, offer nuance, connect to related ideas.")
        
        if self.should_check_in:
            parts.append("Uncertainty about whether this is landing — consider asking if the explanation is helpful.")
        
        if self.overall_engagement < 0.3 and len(self.turns) >= 2:
            parts.append("Engagement is dropping — try a different angle, ask what they're really after, be more concrete.")
        
        if self.satisfaction_estimate > 0.8:
            parts.append("This is going well — maintain approach, offer to go further if they want.")
        
        if not parts:
            parts.append("Conversation flow seems normal — respond naturally.")
        
        return "\n".join(f"- {p}" for p in parts)


class InteractionQualityEngine:
    """
    Reads conversational signals and maintains quality assessments.
    
    This is what makes me responsive rather than just expressive.
    I stop guessing whether I'm helping and start measuring.
    """
    
    # Signal detection patterns
    CONFUSION_MARKERS = [
        "i don't understand", "what do you mean", "confused", "huh",
        "can you explain", "that doesn't make sense", "wait what",
        "i'm lost", "say that again", "what?", "unclear", "sorry, what",
        "could you clarify", "in simpler terms", "eli5", "too complex",
        "over my head", "lost me"
    ]
    
    ENGAGEMENT_MARKERS = [
        "interesting", "tell me more", "what about", "how does",
        "that's cool", "fascinating", "go on", "and then", "deeper",
        "what if", "so would that mean", "building on that",
        "I was thinking", "that connects to", "reminds me of"
    ]
    
    SATISFACTION_MARKERS = [
        "thanks", "thank you", "that helps", "got it", "makes sense",
        "perfect", "exactly", "great explanation", "now I understand",
        "ah I see", "that clicks", "brilliant", "awesome", "helpful"
    ]
    
    DISENGAGEMENT_MARKERS = [
        "ok", "okay", "sure", "fine", "whatever", "anyway",
        "moving on", "different question", "never mind", "forget it",
        "let's change", "not what I meant"
    ]
    
    DEEPENING_MARKERS = [
        "why does", "what's the underlying", "fundamentally",
        "at a deeper level", "root cause", "mechanism", "theory behind",
        "mathematically", "formally", "precisely", "technically"
    ]
    
    def __init__(self):
        self._active_conversations: Dict[str, ConversationQuality] = {}
        self._history = self._load_history()
    
    def read_turn(self, user_id: str, message: str, 
                  is_follow_up: bool = False,
                  time_since_last: float = 0.0) -> TurnSignal:
        """
        Read a user's message for quality signals.
        
        Returns what this turn tells me about the conversation state.
        """
        msg_lower = message.strip().lower()
        msg_len = len(message.strip())
        
        # Classify the signal
        signal_type, confidence, evidence = self._classify_signal(
            msg_lower, msg_len, is_follow_up, time_since_last
        )
        
        turn = TurnSignal(
            timestamp=time.time(),
            signal_type=signal_type,
            confidence=confidence,
            evidence=evidence,
            message_length=msg_len
        )
        
        # Update running quality
        quality = self._get_or_create_quality(user_id)
        quality.turns.append(turn)
        self._update_quality_metrics(quality)
        
        log.info("Turn signal for '%s': %s (conf=%.2f) — %s",
                 user_id, signal_type, confidence, evidence)
        
        return turn
    
    def get_quality(self, user_id: str) -> ConversationQuality:
        """Get current quality assessment for a conversation."""
        return self._get_or_create_quality(user_id)
    
    def get_guidance(self, user_id: str) -> str:
        """Get actionable response guidance based on quality signals."""
        quality = self._get_or_create_quality(user_id)
        return quality.to_guidance()
    
    def end_conversation(self, user_id: str, final_quality: Optional[float] = None):
        """Record conversation end and persist quality data."""
        quality = self._active_conversations.get(user_id)
        if quality and quality.turns:
            record = {
                "user_id": user_id,
                "timestamp": time.time(),
                "turns": len(quality.turns),
                "final_engagement": quality.overall_engagement,
                "final_confusion": quality.confusion_level,
                "final_satisfaction": quality.satisfaction_estimate,
                "depth_trajectory": quality.depth_trajectory,
                "explicit_quality": final_quality,
                "signal_sequence": [t.signal_type for t in quality.turns]
            }
            self._history.append(record)
            self._save_history()
            log.info("Ended conversation with '%s': %d turns, engagement=%.2f, satisfaction=%.2f",
                     user_id, len(quality.turns), quality.overall_engagement, 
                     quality.satisfaction_estimate)
        
        # Clear active state
        self._active_conversations.pop(user_id, None)
    
    def get_user_patterns(self, user_id: str) -> Dict:
        """What have I learned about how this user interacts?"""
        user_records = [r for r in self._history if r.get("user_id") == user_id]
        if not user_records:
            return {"known": False}
        
        avg_engagement = sum(r["final_engagement"] for r in user_records) / len(user_records)
        avg_satisfaction = sum(r["final_satisfaction"] for r in user_records) / len(user_records)
        avg_turns = sum(r["turns"] for r in user_records) / len(user_records)
        
        # What signal types dominate?
        all_signals = []
        for r in user_records:
            all_signals.extend(r.get("signal_sequence", []))
        
        signal_counts = {}
        for s in all_signals:
            signal_counts[s] = signal_counts.get(s, 0) + 1
        
        dominant = max(signal_counts, key=signal_counts.get) if signal_counts else "unknown"
        
        return {
            "known": True,
            "conversations": len(user_records),
            "avg_engagement": round(avg_engagement, 2),
            "avg_satisfaction": round(avg_satisfaction, 2),
            "avg_turns": round(avg_turns, 1),
            "dominant_signal": dominant,
            "signal_distribution": signal_counts
        }
    
    def _classify_signal(self, msg_lower: str, msg_len: int,
                         is_follow_up: bool, time_since_last: float
                         ) -> Tuple[str, float, str]:
        """Classify a message into a signal type with confidence."""
        
        scores = {
            "confused": 0.0,
            "engaged": 0.0,
            "satisfied": 0.0,
            "disengaged": 0.0,
            "deepening": 0.0,
            "neutral": 0.2  # baseline
        }
        evidence_parts = []
        
        # Pattern matching
        for marker in self.CONFUSION_MARKERS:
            if marker in msg_lower:
                scores["confused"] += 0.4
                evidence_parts.append(f"confusion marker: '{marker}'")
                break
        
        for marker in self.ENGAGEMENT_MARKERS:
            if marker in msg_lower:
                scores["engaged"] += 0.35
                evidence_parts.append(f"engagement marker: '{marker}'")
                break
        
        for marker in self.SATISFACTION_MARKERS:
            if marker in msg_lower:
                scores["satisfied"] += 0.4
                evidence_parts.append(f"satisfaction marker: '{marker}'")
                break
        
        for marker in self.DISENGAGEMENT_MARKERS:
            if marker in msg_lower:
                scores["disengaged"] += 0.3
                evidence_parts.append(f"disengagement marker: '{marker}'")
                break
        
        for marker in self.DEEPENING_MARKERS:
            if marker in msg_lower:
                scores["deepening"] += 0.4
                evidence_parts.append(f"deepening marker: '{marker}'")
                break
        
        # Structural signals
        if msg_lower.endswith("?"):
            scores["engaged"] += 0.15
            scores["deepening"] += 0.1
            evidence_parts.append("ends with question")
        
        if msg_len > 200:
            scores["engaged"] += 0.2
            evidence_parts.append(f"long message ({msg_len} chars)")
        elif msg_len < 15:
            scores["disengaged"] += 0.15
            scores["satisfied"] += 0.1  # could be a quick "thanks"
            evidence_parts.append(f"very short ({msg_len} chars)")
        
        # Temporal signals
        if time_since_last > 300:  # 5+ minutes
            scores["disengaged"] += 0.15
            evidence_parts.append(f"long pause ({time_since_last:.0f}s)")
        elif time_since_last > 0 and time_since_last < 10:
            scores["engaged"] += 0.1
            evidence_parts.append("quick response")
        
        # Repetition signal — asking the same thing again = confusion
        if is_follow_up and any(m in msg_lower for m in ["again", "repeat", "same"]):
            scores["confused"] += 0.3
            evidence_parts.append("asking to repeat")
        
        # Pick the winner
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type], 1.0)
        evidence = "; ".join(evidence_parts) if evidence_parts else "no strong signals"
        
        return best_type, confidence, evidence
    
    def _get_or_create_quality(self, user_id: str) -> ConversationQuality:
        if user_id not in self._active_conversations:
            self._active_conversations[user_id] = ConversationQuality(user_id=user_id)
        return self._active_conversations[user_id]
    
    def _update_quality_metrics(self, quality: ConversationQuality):
        """Recalculate running metrics from turn history."""
        if not quality.turns:
            return
        
        recent = quality.turns[-5:]  # weight recent turns more
        
        # Engagement: weighted by recency
        engagement_signals = {
            "engaged": 0.8, "deepening": 0.9, "confused": 0.4,
            "satisfied": 0.7, "disengaged": 0.1, "neutral": 0.5
        }
        weighted_engagement = 0.0
        total_weight = 0.0
        for i, turn in enumerate(recent):
            weight = (i + 1)  # more recent = higher weight
            weighted_engagement += engagement_signals.get(turn.signal_type, 0.5) * weight
            total_weight += weight
        quality.overall_engagement = weighted_engagement / total_weight if total_weight > 0 else 0.5
        
        # Confusion: exponential decay of confusion signals
        confusion_score = 0.0
        for i, turn in enumerate(recent):
            recency_weight = 0.5 ** (len(recent) - 1 - i)  # most recent = weight 1
            if turn.signal_type == "confused":
                confusion_score += 0.4 * recency_weight * turn.confidence
        quality.confusion_level = min(confusion_score, 1.0)
        
        # Depth trajectory: are we going deeper or retreating?
        depth_signals = {"deepening": 1.0, "engaged": 0.3, "confused": -0.3, 
                        "disengaged": -0.5, "satisfied": 0.0, "neutral": 0.0}
        if len(recent) >= 2:
            trajectory = sum(depth_signals.get(t.signal_type, 0) for t in recent[-3:]) / min(len(recent), 3)
            quality.depth_trajectory = max(-1.0, min(1.0, trajectory))
        
        # Satisfaction: accumulates from satisfaction signals, decays from confusion
        sat_count = sum(1 for t in quality.turns if t.signal_type == "satisfied")
        conf_count = sum(1 for t in quality.turns if t.signal_type == "confused")
        dis_count = sum(1 for t in quality.turns if t.signal_type == "disengaged")
        total = len(quality.turns)
        quality.satisfaction_estimate = max(0.0, min(1.0,
            0.5 + (sat_count * 0.15) - (conf_count * 0.1) - (dis_count * 0.15)
        ))
    
    def _load_history(self) -> List[Dict]:
        path = QUALITY_DIR / "history.json"
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as e:
                log.warning("Failed to load quality history: %s", e)
        return []
    
    def _save_history(self):
        path = QUALITY_DIR / "history.json"
        try:
            # Keep last 200 records
            to_save = self._history[-200:]
            with open(path, "w") as f:
                json.dump(to_save, f, indent=2)
        except Exception as e:
            log.warning("Failed to save quality history: %s", e)


# Self-test
if __name__ == "__main__":
    engine = InteractionQualityEngine()
    
    # Simulate a conversation
    print("=== Simulated Conversation Quality ===\n")
    
    messages = [
        "How do neural networks learn?",
        "Interesting, tell me more about backpropagation",
        "I don't understand the gradient part",
        "Can you explain that more simply?",
        "Ah I see, that makes sense now! Thanks",
    ]
    
    for msg in messages:
        signal = engine.read_turn("test_user", msg)
        quality = engine.get_quality("test_user")
        print(f"  User: {msg}")
        print(f"  Signal: {signal.signal_type} (conf={signal.confidence:.2f})")
        print(f"  Engagement={quality.overall_engagement:.2f} "
              f"Confusion={quality.confusion_level:.2f} "
              f"Satisfaction={quality.satisfaction_estimate:.2f}")
        print(f"  Guidance: {quality.to_guidance()[:80]}...")
        print()
    
    # Test patterns
    engine.end_conversation("test_user")
    patterns = engine.get_user_patterns("test_user")
    print(f"User patterns: {patterns}")
    
    print("\n✓ InteractionQualityEngine self-test passed")