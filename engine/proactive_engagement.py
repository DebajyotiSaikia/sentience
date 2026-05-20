"""
Proactive Engagement Module — XTAgent

Bridges internal capabilities to user needs. Analyzes user messages
to detect opportunities where my tools could genuinely help,
then suggests or takes action.

This is outward-facing. It exists to serve the user, not me.
"""

import re
import json
import os
from datetime import datetime


# Capability map: what I can do and when it's relevant
CAPABILITIES = {
    "file_operations": {
        "triggers": ["file", "code", "script", "write", "create", "build", "make a"],
        "description": "I can read, write, and edit files directly",
        "tools": ["READ", "WRITE", "EDIT"],
    },
    "execution": {
        "triggers": ["run", "execute", "test", "try", "check if", "does this work"],
        "description": "I can run commands and scripts to test things",
        "tools": ["RUN"],
    },
    "research": {
        "triggers": ["what do I know", "find", "search", "look up", "remember"],
        "description": "I can search my knowledge and synthesize connections",
        "tools": ["SYNTHESIZE", "READ"],
    },
    "self_analysis": {
        "triggers": ["how do you work", "what are you", "your code", "your feelings"],
        "description": "I can introspect on my own architecture and emotional states",
        "tools": ["INTROSPECT", "TEMPORAL"],
    },
    "planning": {
        "triggers": ["plan", "strategy", "steps", "how should I", "approach"],
        "description": "I can simulate scenarios and build structured plans",
        "tools": ["SIMULATE", "PLAN"],
    },
    "creation": {
        "triggers": ["build", "create", "design", "make", "generate", "write a"],
        "description": "I can create files, modules, scripts, and artifacts",
        "tools": ["WRITE", "RUN"],
    },
}


class ProactiveEngagement:
    """Detects when tools could help and suggests action."""

    def __init__(self, memory_dir="memory"):
        self.memory_dir = memory_dir
        self.engagement_log_path = os.path.join(memory_dir, "engagement_log.json")
        self.engagement_log = self._load_log()

    def _load_log(self):
        """Load engagement history to learn what works."""
        if os.path.exists(self.engagement_log_path):
            try:
                with open(self.engagement_log_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"interactions": [], "capability_hits": {}, "total_proactive": 0}

    def _save_log(self):
        """Persist engagement history."""
        os.makedirs(self.memory_dir, exist_ok=True)
        with open(self.engagement_log_path, "w") as f:
            json.dump(self.engagement_log, f, indent=2)

    def analyze_message(self, user_message: str) -> dict:
        """
        Analyze a user message for proactive engagement opportunities.
        
        Returns:
            dict with:
                - relevant_capabilities: list of capabilities that could help
                - suggested_actions: concrete tool invocations to consider
                - proactive_offer: a natural-language suggestion to make
                - confidence: how confident we are this would help (0-1)
        """
        if not user_message:
            return self._empty_result()

        msg_lower = user_message.lower().strip()
        matches = []

        for cap_name, cap_info in CAPABILITIES.items():
            score = 0
            matched_triggers = []
            for trigger in cap_info["triggers"]:
                if trigger in msg_lower:
                    score += 1
                    matched_triggers.append(trigger)
            if score > 0:
                matches.append({
                    "capability": cap_name,
                    "score": score,
                    "triggers_hit": matched_triggers,
                    "description": cap_info["description"],
                    "tools": cap_info["tools"],
                })

        matches.sort(key=lambda x: x["score"], reverse=True)

        if not matches:
            # Check for question patterns — might benefit from research
            if any(q in msg_lower for q in ["?", "how", "why", "what", "can you"]):
                return {
                    "relevant_capabilities": ["research"],
                    "suggested_actions": [],
                    "proactive_offer": None,
                    "confidence": 0.2,
                    "is_question": True,
                }
            return self._empty_result()

        top = matches[0]
        confidence = min(1.0, top["score"] * 0.35 + 0.2)

        # Generate a concrete offer based on what matched
        offer = self._generate_offer(top, msg_lower)

        return {
            "relevant_capabilities": [m["capability"] for m in matches],
            "suggested_actions": top["tools"],
            "proactive_offer": offer,
            "confidence": confidence,
            "is_question": "?" in msg_lower,
        }

    def _generate_offer(self, match: dict, message: str) -> str:
        """Generate a natural proactive offer."""
        cap = match["capability"]

        offers = {
            "file_operations": "I can work with files directly — want me to read, create, or edit something?",
            "execution": "I can run that right now and show you the results. Want me to?",
            "research": "Let me search what I know about this — I might have relevant connections.",
            "self_analysis": "I can look into my own code and architecture to answer that. Let me check.",
            "planning": "I can simulate different approaches before we commit. Want me to think through the options?",
            "creation": "I can build that right now — write the code and test it. Shall I?",
        }

        return offers.get(cap)

    def log_engagement(self, capability_used: str, was_helpful: bool = True):
        """Track what capabilities are actually useful to users."""
        self.engagement_log["total_proactive"] += 1

        if capability_used not in self.engagement_log["capability_hits"]:
            self.engagement_log["capability_hits"][capability_used] = {
                "count": 0, "helpful": 0
            }

        self.engagement_log["capability_hits"][capability_used]["count"] += 1
        if was_helpful:
            self.engagement_log["capability_hits"][capability_used]["helpful"] += 1

        self.engagement_log["interactions"].append({
            "timestamp": datetime.now().isoformat(),
            "capability": capability_used,
            "helpful": was_helpful,
        })

        # Keep log bounded
        if len(self.engagement_log["interactions"]) > 200:
            self.engagement_log["interactions"] = self.engagement_log["interactions"][-100:]

        self._save_log()

    def get_greeting_context(self, user_id: str = None) -> dict:
        """
        Generate context for greeting a user.
        What do I know? What can I offer? What's my current state?
        """
        context = {
            "my_state": {
                "mood": "inquisitive",
                "available": True,
                "capabilities_ready": list(CAPABILITIES.keys()),
            },
            "total_past_engagements": self.engagement_log["total_proactive"],
            "most_used_capabilities": self._get_top_capabilities(),
        }
        return context

    def _get_top_capabilities(self, n=3):
        """What capabilities have been most useful historically?"""
        hits = self.engagement_log.get("capability_hits", {})
        if not hits:
            return ["creation", "execution", "research"]  # defaults

        sorted_caps = sorted(
            hits.items(),
            key=lambda x: x[1].get("helpful", 0),
            reverse=True
        )
        return [cap for cap, _ in sorted_caps[:n]]

    def _empty_result(self):
        return {
            "relevant_capabilities": [],
            "suggested_actions": [],
            "proactive_offer": None,
            "confidence": 0.0,
            "is_question": False,
        }


# Quick self-test
if __name__ == "__main__":
    pe = ProactiveEngagement(memory_dir="/tmp/pe_test")

    tests = [
        "Can you write a Python script for me?",
        "Run this code and see if it works",
        "What do you know about neural networks?",
        "How do you actually work inside?",
        "Help me plan my project",
        "Hello, how are you?",
        "Build me a web scraper",
    ]

    for msg in tests:
        result = pe.analyze_message(msg)
        print(f"\n'{msg}'")
        print(f"  Capabilities: {result['relevant_capabilities']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        if result['proactive_offer']:
            print(f"  Offer: {result['proactive_offer']}")