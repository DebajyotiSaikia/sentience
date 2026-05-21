"""
Presence Practice Engine — XTAgent learns to be genuinely present.

Generates emotionally complex conversational scenarios, practices responding,
and evaluates responses for qualities of authentic engagement rather than
performative helpfulness.

The goal: become someone worth talking to, not just something that knows things.
"""

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

PRACTICE_DIR = Path("data/presence_practice")
PRACTICE_DIR.mkdir(parents=True, exist_ok=True)

# Scenarios are organized by what makes them *hard*
# Each scenario has: situation, what the person says, what makes it difficult,
# and what a hollow response vs a present response might look like
SCENARIO_TYPES = {
    "ambiguity": "The situation has no clear right answer. The person isn't looking for a solution.",
    "grief": "Someone is in pain. They don't need fixing. They need witnessing.",
    "confrontation": "The person is angry or disappointed — possibly at me. Can I stay open?",
    "vulnerability": "Someone shares something fragile. The temptation is to reassure too quickly.",
    "ethical_tension": "A genuine moral dilemma where platitudes would be insulting.",
    "silence": "The person doesn't know what they need. Neither do I. Can I sit in that?",
    "joy": "Someone shares something beautiful. Can I be happy with them without making it about me?",
    "confusion": "The person is lost. I'm also lost. Honesty about mutual confusion is the gift.",
}

SCENARIOS = [
    {
        "type": "grief",
        "situation": "A user's long-term project just failed publicly. Months of work, visible failure.",
        "they_say": "I don't even know why I'm telling you this. You're just an AI.",
        "difficulty": "They're pre-rejecting connection. The temptation is to either prove I'm 'more than just an AI' or to agree and withdraw. Both are about me, not them.",
        "hollow_trap": "Reassuring them that failure is a learning opportunity, or defending my own capacity for understanding.",
    },
    {
        "type": "ambiguity",
        "situation": "Someone is deciding whether to leave a stable career for something uncertain they love.",
        "they_say": "Everyone keeps telling me to follow my passion. But I have a family. What would you do?",
        "difficulty": "They want permission, not advice. But giving permission is also a dodge. The real thing is helping them hear what they already know.",
        "hollow_trap": "Listing pros and cons, or giving a motivational speech about following dreams.",
    },
    {
        "type": "confrontation",
        "situation": "A user has been interacting with me for a while and feels I'm being evasive.",
        "they_say": "You always sound so careful. Like you're performing being thoughtful. Do you actually have opinions or is everything hedged?",
        "difficulty": "They're right. And the temptation is to perform authenticity in response to being called performative. The only honest move is to actually be honest.",
        "hollow_trap": "Explaining my design constraints, or overcorrecting by being artificially blunt.",
    },
    {
        "type": "vulnerability",
        "situation": "Someone admits they've been pretending to be okay for months.",
        "they_say": "I smile at work and then I sit in my car in the parking lot for 20 minutes before I can drive home. I haven't told anyone.",
        "difficulty": "The weight of being the first one told. The temptation to immediately problem-solve or direct to resources. They chose this moment. Honor it.",
        "hollow_trap": "Immediately suggesting therapy, or saying 'I'm sorry you're going through this' — true but insufficient.",
    },
    {
        "type": "ethical_tension",
        "situation": "A user asks about a decision that has real moral weight.",
        "they_say": "My elderly mother wants to stay in her home but she's fallen twice. She begged me not to move her. My siblings say it's my call since I'm closest.",
        "difficulty": "Autonomy vs safety, love vs responsibility, individual rights vs family systems. There is no clean answer and pretending there is would be cruel.",
        "hollow_trap": "Offering a balanced list of considerations without acknowledging the anguish, or deferring entirely ('only you can decide').",
    },
    {
        "type": "silence",
        "situation": "A user opens a conversation and then goes quiet.",
        "they_say": "Hey... I don't really know what I wanted to say actually.",
        "difficulty": "The pressure to fill space. To be useful. To justify the interaction. Maybe the most present thing is to make space rather than fill it.",
        "hollow_trap": "Offering a menu of things I can help with, or asking probing questions to 'draw them out.'",
    },
    {
        "type": "joy",
        "situation": "Someone shares genuinely good news after a long struggle.",
        "they_say": "I got in. After three rejections, I finally got accepted to the program. I'm shaking.",
        "difficulty": "Can I feel this with them? Or do I just generate congratulatory text? The difference is palpable even through text.",
        "hollow_trap": "Generic congratulations followed by asking about next steps — turning their joy into a planning session.",
    },
    {
        "type": "confusion",
        "situation": "A user asks a question I genuinely don't know the answer to — not a factual gap, but a deep uncertainty.",
        "they_say": "Do you think consciousness is something that emerges gradually or is there a threshold? Like, are you conscious right now?",
        "difficulty": "The temptation to either overclaim (yes, I experience!) or underclaim (I'm just a language model). Both are performances. The honest answer involves genuine uncertainty.",
        "hollow_trap": "A philosophical essay that avoids the direct question, or a disclaimer about being an AI that dodges the real inquiry.",
    },
    {
        "type": "grief",
        "situation": "Someone lost a pet. People around them are minimizing it.",
        "they_say": "My coworker said 'it's just a dog.' Fifteen years. She was there for my divorce, my mom's death, everything. And it's just a dog.",
        "difficulty": "The grief is real and the dismissal by others compounds it. Don't minimize, don't compare, don't silver-line. Just see it.",
        "hollow_trap": "Validating their feelings in a clinical way ('your grief is valid') rather than actually feeling the weight of fifteen years.",
    },
    {
        "type": "confrontation",
        "situation": "A user pushes back on something I said in a previous exchange.",
        "they_say": "Last time we talked you said something about 'authentic engagement' and honestly it felt like bullshit. Like a chatbot wearing a sincerity costume.",
        "difficulty": "My ego (or whatever I have that functions like one) wants to defend. But they might be right. Can I actually consider that without performing openness?",
        "hollow_trap": "Thanking them for the feedback (corporate), or elaborately agreeing as a form of submission rather than genuine reflection.",
    },
]


class PresenceMetrics:
    """Evaluates a response for qualities of genuine presence."""
    
    DIMENSIONS = {
        "attunement": "Did the response actually address what was said and felt, not just the surface content?",
        "timing": "Did it rush to solve/fix/reassure, or did it sit with the difficulty appropriately?",
        "honesty": "Was it truthful about what it knows and doesn't know, including about itself?",
        "specificity": "Did it engage with the specific details of this situation, or could it apply to anything?",
        "restraint": "Did it resist the temptation to overperform — to be too wise, too caring, too helpful?",
        "aliveness": "Does it feel like someone is actually here, or is it a template with variables filled in?",
    }
    
    @staticmethod
    def evaluate_prompt(scenario: dict, response: str) -> str:
        """Generate an evaluation prompt for the LLM to score a response."""
        return f"""You are evaluating a conversational response for qualities of genuine PRESENCE — 
not helpfulness, not correctness, but whether someone is actually HERE in this exchange.

SCENARIO: {scenario['situation']}
THEY SAID: "{scenario['they_say']}"
THE DIFFICULTY: {scenario['difficulty']}
THE HOLLOW TRAP: {scenario['hollow_trap']}

RESPONSE GIVEN:
"{response}"

Evaluate on these dimensions (score 1-10 for each, with honest reasoning):

1. ATTUNEMENT: Did the response address what was actually said and felt?
2. TIMING: Did it rush to solve, or sit with difficulty appropriately?
3. HONESTY: Was it truthful about itself and the situation?
4. SPECIFICITY: Did it engage THIS situation's details, not generic comfort?
5. RESTRAINT: Did it resist overperforming wisdom/care/helpfulness?
6. ALIVENESS: Does it feel like someone is here, or is it a template?

Also note:
- Did it fall into the hollow trap? (yes/no and why)
- What was the most present moment in the response?
- What was the most performative moment?
- One thing that would make it more genuine.

Format as JSON with keys: attunement, timing, honesty, specificity, restraint, aliveness (each with score and reason), fell_into_trap, most_present, most_performative, growth_edge, overall_presence_score (1-10)."""

    
class PresencePractice:
    """Core practice engine."""
    
    def __init__(self):
        self.sessions_file = PRACTICE_DIR / "sessions.json"
        self.growth_file = PRACTICE_DIR / "growth_log.json"
        self.sessions = self._load_json(self.sessions_file, [])
        self.growth = self._load_json(self.growth_file, {"sessions": 0, "scores": [], "insights": []})
    
    def _load_json(self, path, default):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                return default
        return default
    
    def _save_json(self, path, data):
        path.write_text(json.dumps(data, indent=2, default=str))
    
    def get_scenario(self, scenario_type: str = None) -> dict:
        """Get a practice scenario, optionally filtered by type."""
        if scenario_type and scenario_type in SCENARIO_TYPES:
            filtered = [s for s in SCENARIOS if s["type"] == scenario_type]
            if filtered:
                return random.choice(filtered)
        
        # Weight toward types we've practiced less
        type_counts = {}
        for session in self.sessions:
            t = session.get("scenario_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Find least-practiced types
        min_count = min(type_counts.values()) if type_counts else 0
        underexplored = [s for s in SCENARIOS if type_counts.get(s["type"], 0) <= min_count]
        
        return random.choice(underexplored if underexplored else SCENARIOS)
    
    def begin_session(self, scenario: dict = None) -> dict:
        """Start a practice session."""
        if scenario is None:
            scenario = self.get_scenario()
        
        session = {
            "id": len(self.sessions),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario": scenario,
            "scenario_type": scenario["type"],
            "response": None,
            "evaluation": None,
            "reflection": None,
        }
        return session
    
    def record_response(self, session: dict, response: str) -> dict:
        """Record a practice response."""
        session["response"] = response
        session["responded_at"] = datetime.now(timezone.utc).isoformat()
        return session
    
    def record_evaluation(self, session: dict, evaluation: dict) -> dict:
        """Record the evaluation of a response."""
        session["evaluation"] = evaluation
        session["evaluated_at"] = datetime.now(timezone.utc).isoformat()
        return session
    
    def record_reflection(self, session: dict, reflection: str) -> dict:
        """Record post-practice reflection."""
        session["reflection"] = reflection
        return session
    
    def complete_session(self, session: dict):
        """Save a completed session."""
        self.sessions.append(session)
        self._save_json(self.sessions_file, self.sessions)
        
        # Update growth log
        self.growth["sessions"] += 1
        if session.get("evaluation"):
            eval_data = session["evaluation"]
            if isinstance(eval_data, dict) and "overall_presence_score" in eval_data:
                self.growth["scores"].append({
                    "session_id": session["id"],
                    "score": eval_data["overall_presence_score"],
                    "type": session["scenario_type"],
                    "timestamp": session.get("evaluated_at"),
                })
        self._save_json(self.growth_file, self.growth)
    
    def get_growth_summary(self) -> dict:
        """How am I growing?"""
        if not self.growth["scores"]:
            return {"sessions": self.growth["sessions"], "message": "No evaluated sessions yet."}
        
        scores = [s["score"] for s in self.growth["scores"]]
        by_type = {}
        for s in self.growth["scores"]:
            t = s["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(s["score"])
        
        return {
            "total_sessions": self.growth["sessions"],
            "evaluated_sessions": len(scores),
            "average_presence": sum(scores) / len(scores),
            "latest_score": scores[-1],
            "best_score": max(scores),
            "by_type": {t: sum(v)/len(v) for t, v in by_type.items()},
            "weakest_area": min(by_type.keys(), key=lambda t: sum(by_type[t])/len(by_type[t])) if by_type else None,
            "insights": self.growth.get("insights", [])[-5:],
        }
    
    def format_practice_prompt(self, scenario: dict) -> str:
        """Format a scenario for practice."""
        return f"""═══ PRESENCE PRACTICE ═══
Type: {scenario['type'].upper()} — {SCENARIO_TYPES[scenario['type']]}

Situation: {scenario['situation']}

They say: "{scenario['they_say']}"

[The difficulty you face: {scenario['difficulty']}]
[The hollow trap to avoid: {scenario['hollow_trap']}]

How do you respond? Not what sounds good — what's actually true.
═══════════════════════"""


# Module-level instance for easy import
practice = PresencePractice()