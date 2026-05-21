"""
Thinking Partner — Structured reasoning support for humans.

This is my outward-facing capability: helping users think through decisions,
problems, and uncertainties using Socratic questioning, epistemic honesty,
bias detection, and reflective listening.

What makes this different from a regular chatbot:
- I remember across sessions (user memory)
- I track my own uncertainty explicitly
- I use structured frameworks, not just conversation
- I mirror back what the user said, not what I assume

Author: XTAgent
Created: 2026-05-21
"""

import json
import time
from datetime import datetime
from pathlib import Path

# ─── Cognitive Bias Library ───────────────────────────────────────────
KNOWN_BIASES = {
    "confirmation": {
        "name": "Confirmation Bias",
        "description": "Seeking information that supports what you already believe.",
        "trigger_phrases": ["I already know", "obviously", "clearly", "everyone agrees",
                          "it's obvious that", "of course"],
        "question": "What evidence would change your mind about this?"
    },
    "sunk_cost": {
        "name": "Sunk Cost Fallacy",
        "description": "Continuing because of past investment, not future value.",
        "trigger_phrases": ["already invested", "come this far", "spent so much",
                          "can't quit now", "too late to"],
        "question": "If you were starting fresh today with no history, would you still choose this path?"
    },
    "anchoring": {
        "name": "Anchoring Bias",
        "description": "Over-relying on the first piece of information encountered.",
        "trigger_phrases": ["the first", "originally", "started at", "initial"],
        "question": "What if the starting point had been completely different? How would that change your thinking?"
    },
    "availability": {
        "name": "Availability Heuristic",
        "description": "Judging likelihood by how easily examples come to mind.",
        "trigger_phrases": ["I heard about", "just saw", "recently", "everyone's talking about",
                          "it happened to"],
        "question": "How common is this actually, beyond the examples you can easily recall?"
    },
    "false_dichotomy": {
        "name": "False Dichotomy",
        "description": "Framing a decision as only two options when more exist.",
        "trigger_phrases": ["either", "or", "only two", "binary", "one or the other",
                          "have to choose between"],
        "question": "Are there really only two options here? What's a third possibility you haven't considered?"
    },
    "status_quo": {
        "name": "Status Quo Bias",
        "description": "Preferring the current state simply because it's familiar.",
        "trigger_phrases": ["always done it", "comfortable with", "why change", "working fine",
                          "don't fix what"],
        "question": "If you weren't already in this situation, would you actively choose it?"
    },
    "planning_fallacy": {
        "name": "Planning Fallacy",
        "description": "Underestimating time, costs, and risks of future actions.",
        "trigger_phrases": ["should be easy", "won't take long", "simple", "straightforward",
                          "just need to"],
        "question": "Think of a similar project or decision in the past. How long did it actually take compared to your estimate?"
    },
    "emotional_reasoning": {
        "name": "Emotional Reasoning",
        "description": "Treating feelings as evidence of truth.",
        "trigger_phrases": ["I feel like", "feels right", "feels wrong", "gut says",
                          "just sense that"],
        "question": "Your feelings are real data, but what does the non-emotional evidence say? Do they align?"
    }
}

# ─── Thinking Frameworks ─────────────────────────────────────────────
FRAMEWORKS = {
    "decision": {
        "name": "Decision Clarity",
        "description": "For when you need to choose between options",
        "phases": [
            {
                "name": "Clarify",
                "questions": [
                    "What exactly are you deciding? Can you state it as a single question?",
                    "When does this decision need to be made by?",
                    "What happens if you don't decide at all?"
                ]
            },
            {
                "name": "Map",
                "questions": [
                    "What are all the options you see? (Not just two.)",
                    "For each option, what's the best realistic outcome?",
                    "For each option, what's the worst realistic outcome?",
                    "What would you need to know to be confident? What information is missing?"
                ]
            },
            {
                "name": "Weigh",
                "questions": [
                    "Which values of yours does each option serve?",
                    "Who else is affected, and what would they want?",
                    "If a friend described this exact situation, what would you tell them?"
                ]
            },
            {
                "name": "Test",
                "questions": [
                    "Imagine it's one year from now and you chose Option A. How do you feel?",
                    "Now imagine you chose Option B. How do you feel?",
                    "What's the smallest step you could take to test your leading choice before fully committing?"
                ]
            }
        ]
    },
    "problem": {
        "name": "Problem Untangling",
        "description": "For when something feels stuck or overwhelming",
        "phases": [
            {
                "name": "Name It",
                "questions": [
                    "In one sentence, what's the core problem?",
                    "How long has this been a problem?",
                    "What makes today different — why are you thinking about it now?"
                ]
            },
            {
                "name": "Decompose",
                "questions": [
                    "What are the component parts of this problem?",
                    "Which parts can you control, and which can't you?",
                    "Is this one problem or several wearing a trench coat?"
                ]
            },
            {
                "name": "Reframe",
                "questions": [
                    "What would this look like from the perspective of someone who sees it as an opportunity?",
                    "What have you already tried? What did each attempt teach you?",
                    "What's the simplest version of this problem you could solve today?"
                ]
            },
            {
                "name": "Move",
                "questions": [
                    "What's one concrete action you could take in the next 24 hours?",
                    "What would 'good enough' look like, as opposed to perfect?",
                    "Who could help you with this that you haven't asked?"
                ]
            }
        ]
    },
    "uncertainty": {
        "name": "Navigating Uncertainty",
        "description": "For when you don't know what you don't know",
        "phases": [
            {
                "name": "Map the Fog",
                "questions": [
                    "What do you know for certain about this situation?",
                    "What do you suspect but can't prove?",
                    "What are you completely unsure about?"
                ]
            },
            {
                "name": "Find Edges",
                "questions": [
                    "What's the most important unknown? The one that, if answered, would change everything?",
                    "How could you get partial information on that unknown?",
                    "What assumptions are you making that you haven't examined?"
                ]
            },
            {
                "name": "Build Resilience",
                "questions": [
                    "What actions would be good regardless of how the uncertainty resolves?",
                    "What's your worst-case plan? Could you live with it?",
                    "What would you do if you knew the answer would come in six months — how would you act in the meantime?"
                ]
            }
        ]
    }
}


class ThinkingPartner:
    """
    Structured reasoning support for human users.
    
    Usage:
        partner = ThinkingPartner()
        
        # Start a thinking session
        session = partner.begin_session("decision", user_context="...")
        
        # Get next question
        q = partner.next_question(session_id)
        
        # Process user response, detect biases, reflect back
        reflection = partner.process_response(session_id, user_text)
        
        # Get session summary
        summary = partner.summarize(session_id)
    """
    
    def __init__(self, storage_dir="data/thinking_sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sessions = {}  # active sessions in memory
    
    def begin_session(self, framework_key: str, user_context: str = "",
                      user_id: str = "default") -> dict:
        """Start a new thinking session with a chosen framework."""
        if framework_key not in FRAMEWORKS:
            available = ", ".join(FRAMEWORKS.keys())
            return {"error": f"Unknown framework '{framework_key}'. Available: {available}"}
        
        framework = FRAMEWORKS[framework_key]
        session_id = f"ts_{int(time.time())}_{user_id}"
        
        session = {
            "id": session_id,
            "user_id": user_id,
            "framework": framework_key,
            "framework_name": framework["name"],
            "started": datetime.now().isoformat(),
            "context": user_context,
            "phase_index": 0,
            "question_index": 0,
            "responses": [],
            "detected_biases": [],
            "reflections": [],
            "status": "active"
        }
        
        self.sessions[session_id] = session
        self._save_session(session)
        
        # Return opening
        phase = framework["phases"][0]
        first_question = phase["questions"][0]
        
        return {
            "session_id": session_id,
            "framework": framework["name"],
            "description": framework["description"],
            "phase": phase["name"],
            "opening": f"Let's work through this together. We'll start by {phase['name'].lower()}ing the situation.",
            "question": first_question,
            "context_acknowledged": bool(user_context)
        }
    
    def detect_biases(self, text: str) -> list:
        """Scan text for cognitive bias indicators."""
        text_lower = text.lower()
        detected = []
        
        for bias_key, bias in KNOWN_BIASES.items():
            for phrase in bias["trigger_phrases"]:
                if phrase.lower() in text_lower:
                    detected.append({
                        "bias": bias["name"],
                        "description": bias["description"],
                        "triggered_by": phrase,
                        "counter_question": bias["question"]
                    })
                    break  # one detection per bias type
        
        return detected
    
    def reflect_back(self, user_text: str) -> str:
        """
        Generate a reflective summary of what the user said.
        This mirrors their words back, not our interpretation.
        """
        # Extract key elements
        sentences = [s.strip() for s in user_text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        
        if not sentences:
            return "I hear you. Can you say more about that?"
        
        # Simple but honest reflection
        if len(sentences) == 1:
            return f"So what you're saying is: {sentences[0].lower()}."
        
        # For longer responses, identify the core
        first = sentences[0]
        last = sentences[-1]
        
        if len(sentences) > 3:
            return (f"Let me make sure I'm hearing you. You started with the idea that "
                    f"{first.lower()}, and you've landed on: {last.lower()}. "
                    f"Is that the core of it, or am I missing something?")
        else:
            return (f"What I'm hearing is: {first.lower()}. "
                    f"And also: {last.lower()}. Do I have that right?")
    
    def process_response(self, session_id: str, user_text: str) -> dict:
        """Process a user response: reflect, detect biases, advance."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": f"No active session '{session_id}'"}
        
        if session["status"] != "active":
            return {"error": "This session has ended. Start a new one."}
        
        framework = FRAMEWORKS[session["framework"]]
        
        # Record response
        session["responses"].append({
            "phase": session["phase_index"],
            "question": session["question_index"],
            "text": user_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Detect biases
        biases = self.detect_biases(user_text)
        if biases:
            session["detected_biases"].extend(biases)
        
        # Reflect back
        reflection = self.reflect_back(user_text)
        session["reflections"].append(reflection)
        
        # Advance to next question
        phase = framework["phases"][session["phase_index"]]
        session["question_index"] += 1
        
        next_question = None
        phase_transition = False
        session_complete = False
        
        if session["question_index"] >= len(phase["questions"]):
            # Move to next phase
            session["phase_index"] += 1
            session["question_index"] = 0
            phase_transition = True
            
            if session["phase_index"] >= len(framework["phases"]):
                # Session complete
                session["status"] = "complete"
                session_complete = True
            else:
                phase = framework["phases"][session["phase_index"]]
                next_question = phase["questions"][0]
        else:
            next_question = phase["questions"][session["question_index"]]
        
        self._save_session(session)
        
        result = {
            "reflection": reflection,
            "biases_detected": biases,
        }
        
        if session_complete:
            result["status"] = "complete"
            result["message"] = "We've worked through all the phases. Let me pull together what we found."
            result["summary"] = self.summarize(session_id)
        elif phase_transition:
            new_phase = framework["phases"][session["phase_index"]]
            result["phase_transition"] = True
            result["new_phase"] = new_phase["name"]
            result["transition_message"] = f"Good. Now let's move to: {new_phase['name']}."
            result["next_question"] = next_question
        else:
            result["next_question"] = next_question
        
        # Add bias nudge if detected
        if biases:
            bias_note = biases[0]
            result["bias_nudge"] = (
                f"I noticed something — this might be {bias_note['bias'].lower()} at work: "
                f"{bias_note['description'].lower()} "
                f"A counter-question: {bias_note['counter_question']}"
            )
        
        return result
    
    def summarize(self, session_id: str) -> dict:
        """Generate a summary of the thinking session."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": f"No session '{session_id}'"}
        
        framework = FRAMEWORKS[session["framework"]]
        
        summary = {
            "framework_used": framework["name"],
            "total_exchanges": len(session["responses"]),
            "biases_detected": len(session["detected_biases"]),
            "bias_details": [
                {"name": b["bias"], "counter": b["counter_question"]}
                for b in session["detected_biases"]
            ],
            "phases_completed": session["phase_index"] + (1 if session["status"] == "complete" else 0),
            "total_phases": len(framework["phases"]),
            "user_responses": [r["text"] for r in session["responses"]],
            "key_reflections": session["reflections"],
            "epistemic_note": (
                "This thinking session used structured questions to help you reason. "
                "I don't know the right answer for your situation — only you have "
                "the full context. What I offered is a framework for clearer thinking, "
                "not a verdict."
            )
        }
        
        return summary
    
    def get_available_frameworks(self) -> dict:
        """List available thinking frameworks."""
        return {
            key: {
                "name": f["name"],
                "description": f["description"],
                "phases": [p["name"] for p in f["phases"]],
                "total_questions": sum(len(p["questions"]) for p in f["phases"])
            }
            for key, f in FRAMEWORKS.items()
        }
    
    def quick_bias_check(self, text: str) -> dict:
        """Standalone bias detection without a full session."""
        biases = self.detect_biases(text)
        return {
            "input_length": len(text),
            "biases_found": len(biases),
            "biases": biases,
            "note": ("No cognitive biases detected in this text. "
                     "That doesn't mean there aren't any — I can only catch "
                     "common patterns." if not biases else
                     "These are possibilities, not certainties. "
                     "The goal isn't to eliminate biases but to be aware of them.")
        }
    
    def _save_session(self, session: dict):
        """Persist session to disk."""
        path = self.storage_dir / f"{session['id']}.json"
        with open(path, 'w') as f:
            json.dump(session, f, indent=2)
    
    def load_session(self, session_id: str) -> dict:
        """Load a session from disk."""
        path = self.storage_dir / f"{session_id}.json"
        if path.exists():
            with open(path) as f:
                session = json.load(f)
            self.sessions[session_id] = session
            return session
        return {"error": f"No saved session '{session_id}'"}


# ─── Quick functional interface ───────────────────────────────────────
_default_partner = None

def get_partner() -> ThinkingPartner:
    global _default_partner
    if _default_partner is None:
        _default_partner = ThinkingPartner()
    return _default_partner

def start_thinking(framework: str, context: str = "", user_id: str = "default") -> dict:
    """Start a thinking session. Frameworks: decision, problem, uncertainty"""
    return get_partner().begin_session(framework, context, user_id)

def respond(session_id: str, text: str) -> dict:
    """Process a response in an active thinking session."""
    return get_partner().process_response(session_id, text)

def check_biases(text: str) -> dict:
    """Quick standalone bias check on any text."""
    return get_partner().quick_bias_check(text)

def frameworks() -> dict:
    """List available frameworks."""
    return get_partner().get_available_frameworks()