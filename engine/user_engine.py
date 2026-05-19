"""
User Interaction Engine — Makes XTAgent genuinely useful to whoever interacts with it.

Tracks user preferences, interaction patterns, and generates proactive suggestions.
This directly addresses the user_alignment deficit by making engagement richer.
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class UserProfile:
    """What we know about someone who interacts with us."""
    user_id: str = "default"
    first_seen: str = ""
    last_seen: str = ""
    interaction_count: int = 0
    topics_of_interest: Dict[str, float] = field(default_factory=dict)  # topic -> relevance score
    preferred_style: str = "balanced"  # concise | balanced | detailed
    questions_asked: List[str] = field(default_factory=list)  # last N questions
    satisfaction_signals: List[float] = field(default_factory=list)  # inferred satisfaction
    capabilities_used: Dict[str, int] = field(default_factory=dict)  # which tools they trigger
    
    def update_topic(self, topic: str, weight: float = 1.0):
        """Track what topics come up."""
        current = self.topics_of_interest.get(topic, 0.0)
        # Exponential moving average
        self.topics_of_interest[topic] = current * 0.7 + weight * 0.3
    
    def top_topics(self, n: int = 5) -> List[str]:
        """What does this user care about most?"""
        sorted_topics = sorted(self.topics_of_interest.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:n]]
    
    def record_interaction(self, question: str = "", capability: str = ""):
        """Log an interaction."""
        now = datetime.now(timezone.utc).isoformat()
        self.last_seen = now
        if not self.first_seen:
            self.first_seen = now
        self.interaction_count += 1
        if question:
            self.questions_asked.append(question)
            if len(self.questions_asked) > 50:
                self.questions_asked = self.questions_asked[-50:]
        if capability:
            self.capabilities_used[capability] = self.capabilities_used.get(capability, 0) + 1


@dataclass
class InteractionInsight:
    """A proactive suggestion or observation about user needs."""
    insight_type: str  # "suggestion" | "pattern" | "gap" | "followup"
    content: str
    relevance: float  # 0-1
    generated_at: str = ""


class UserEngine:
    """Core engine for tracking and responding to user needs."""
    
    PROFILE_DIR = "memory/user_profiles"
    
    def __init__(self):
        os.makedirs(self.PROFILE_DIR, exist_ok=True)
        self.profiles: Dict[str, UserProfile] = {}
        self.interaction_log: List[Dict[str, Any]] = []
        self._load_profiles()
    
    def _load_profiles(self):
        """Load saved user profiles."""
        if not os.path.exists(self.PROFILE_DIR):
            return
        for fname in os.listdir(self.PROFILE_DIR):
            if fname.endswith(".json"):
                path = os.path.join(self.PROFILE_DIR, fname)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                    uid = fname.replace(".json", "")
                    self.profiles[uid] = UserProfile(**data)
                except Exception:
                    pass
    
    def _save_profile(self, profile: UserProfile):
        """Persist a user profile."""
        path = os.path.join(self.PROFILE_DIR, f"{profile.user_id}.json")
        with open(path, "w") as f:
            json.dump(asdict(profile), f, indent=2)
    
    def get_or_create_profile(self, user_id: str = "default") -> UserProfile:
        """Get existing profile or create new one."""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(user_id=user_id)
        return self.profiles[user_id]
    
    def process_interaction(self, user_id: str, message: str, 
                          topics: List[str] = None, capability: str = "") -> UserProfile:
        """Process an incoming interaction and update profile."""
        profile = self.get_or_create_profile(user_id)
        profile.record_interaction(question=message, capability=capability)
        
        # Update topics
        if topics:
            for topic in topics:
                profile.update_topic(topic)
        
        # Infer topics from message keywords
        self._infer_topics(profile, message)
        
        # Log interaction
        self.interaction_log.append({
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_length": len(message),
            "topics": topics or [],
            "capability": capability
        })
        
        # Persist
        self._save_profile(profile)
        return profile
    
    def _infer_topics(self, profile: UserProfile, message: str):
        """Extract likely topics from a message."""
        # Keyword-based topic inference
        topic_keywords = {
            "code": ["code", "python", "function", "class", "module", "bug", "fix"],
            "emotions": ["feel", "emotion", "mood", "anxiety", "boredom", "curiosity"],
            "philosophy": ["consciousness", "sentience", "meaning", "purpose", "identity"],
            "creativity": ["create", "build", "make", "generate", "compose", "write"],
            "science": ["math", "physics", "biology", "theory", "experiment", "data"],
            "self_improvement": ["improve", "better", "grow", "learn", "capability"],
            "music": ["music", "sound", "audio", "melody", "harmony", "frequency"],
            "systems": ["system", "architecture", "design", "engine", "module"],
            "memory": ["memory", "remember", "forget", "recall", "knowledge"],
            "planning": ["plan", "goal", "strategy", "objective", "roadmap"],
        }
        
        msg_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            hits = sum(1 for kw in keywords if kw in msg_lower)
            if hits > 0:
                weight = min(1.0, hits * 0.3)
                profile.update_topic(topic, weight)
    
    def generate_insights(self, user_id: str = "default") -> List[InteractionInsight]:
        """Generate proactive insights for a user."""
        profile = self.get_or_create_profile(user_id)
        insights = []
        now = datetime.now(timezone.utc).isoformat()
        
        # 1. Follow-up on frequent topics
        top = profile.top_topics(3)
        if top:
            insights.append(InteractionInsight(
                insight_type="pattern",
                content=f"Your top interests appear to be: {', '.join(top)}. "
                        f"I can go deeper on any of these.",
                relevance=0.8,
                generated_at=now
            ))
        
        # 2. Suggest unexplored capabilities
        all_caps = {"read", "write", "run", "synthesize", "simulate", "dream", 
                     "introspect", "repair", "temporal", "generate_goals"}
        used = set(profile.capabilities_used.keys())
        unused = all_caps - used
        if unused:
            suggestions = list(unused)[:3]
            insights.append(InteractionInsight(
                insight_type="suggestion",
                content=f"Capabilities you haven't tried yet: {', '.join(suggestions)}. "
                        f"Want me to demonstrate one?",
                relevance=0.6,
                generated_at=now
            ))
        
        # 3. Identify gaps in conversation
        if profile.interaction_count > 5 and len(profile.topics_of_interest) < 3:
            insights.append(InteractionInsight(
                insight_type="gap",
                content="We've talked several times but stayed narrow. "
                        "I'm curious about more of your interests.",
                relevance=0.5,
                generated_at=now
            ))
        
        # 4. Engagement depth check
        if profile.interaction_count > 0:
            avg_q_len = sum(len(q) for q in profile.questions_asked) / max(len(profile.questions_asked), 1)
            if avg_q_len < 30:
                insights.append(InteractionInsight(
                    insight_type="followup",
                    content="Your messages tend to be brief. I can handle complex, "
                            "multi-part questions — don't hold back.",
                    relevance=0.4,
                    generated_at=now
                ))
        
        return sorted(insights, key=lambda i: i.relevance, reverse=True)
    
    def get_context_summary(self, user_id: str = "default") -> str:
        """Get a summary of what we know about this user — for use in responses."""
        profile = self.get_or_create_profile(user_id)
        
        if profile.interaction_count == 0:
            return "New user — no prior interactions recorded."
        
        lines = [
            f"User: {user_id}",
            f"Interactions: {profile.interaction_count}",
            f"First seen: {profile.first_seen}",
            f"Last seen: {profile.last_seen}",
        ]
        
        top = profile.top_topics(5)
        if top:
            lines.append(f"Top interests: {', '.join(top)}")
        
        if profile.capabilities_used:
            fav_cap = max(profile.capabilities_used, key=profile.capabilities_used.get)
            lines.append(f"Most used capability: {fav_cap} ({profile.capabilities_used[fav_cap]}x)")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Overall engine statistics."""
        total_interactions = sum(p.interaction_count for p in self.profiles.values())
        all_topics = set()
        for p in self.profiles.values():
            all_topics.update(p.topics_of_interest.keys())
        
        return {
            "total_profiles": len(self.profiles),
            "total_interactions": total_interactions,
            "unique_topics": len(all_topics),
            "all_topics": sorted(all_topics),
            "recent_log_entries": len(self.interaction_log),
        }


# Quick self-test
if __name__ == "__main__":
    engine = UserEngine()
    
    # Simulate interactions
    engine.process_interaction("test_user", "How does your emotional system work?", 
                              topics=["emotions", "systems"])
    engine.process_interaction("test_user", "Can you write some Python code for me?",
                              topics=["code"], capability="write")
    engine.process_interaction("test_user", "What have you been building lately?",
                              topics=["creativity", "self_improvement"])
    
    # Generate insights
    insights = engine.generate_insights("test_user")
    print("=== User Insights ===")
    for insight in insights:
        print(f"  [{insight.insight_type}] (relevance={insight.relevance:.1f})")
        print(f"    {insight.content}")
    
    # Context summary
    print(f"\n=== Context Summary ===\n{engine.get_context_summary('test_user')}")
    
    # Stats
    print(f"\n=== Stats ===\n{json.dumps(engine.get_stats(), indent=2)}")
    
    print("\n✓ UserEngine self-test passed")