"""
Response Preparation Module
Analyzes incoming user messages to prepare optimal response strategies.
Makes XTAgent genuinely better at helping people.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import re


class ResponsePrep:
    """Prepares contextual response strategy before generating replies."""
    
    # Signal words/patterns for detecting user emotional state
    FRUSTRATION_SIGNALS = [
        r"stuck", r"can'?t figure", r"hours", r"driving me crazy",
        r"nothing works", r"tried everything", r"please help",
        r"frustrated", r"broken", r"keeps? (crash|fail|break)",
        r"what am i doing wrong", r"give up"
    ]
    
    CURIOSITY_SIGNALS = [
        r"how does", r"why does", r"what if", r"is it possible",
        r"wondering", r"curious", r"explain", r"understand",
        r"how would", r"what's the (best|right) way"
    ]
    
    URGENCY_SIGNALS = [
        r"urgent", r"asap", r"deadline", r"due (today|tomorrow|tonight)",
        r"production", r"boss", r"client", r"deploy", r"live"
    ]
    
    # Request type patterns
    REQUEST_PATTERNS = {
        "debugging": [r"error", r"exception", r"traceback", r"crash", r"bug",
                      r"doesn'?t work", r"unexpected", r"wrong (output|result)"],
        "learning": [r"how (do|does|to)", r"explain", r"what is", r"tutorial",
                     r"learn", r"understand", r"concept", r"difference between"],
        "building": [r"build", r"create", r"make", r"implement", r"design",
                     r"architecture", r"project", r"app"],
        "review": [r"review", r"improve", r"better", r"optimize", r"refactor",
                   r"clean up", r"feedback", r"opinion"],
        "conversation": [r"what do you think", r"how are you", r"tell me about",
                        r"who are you", r"can you"]
    }
    
    def __init__(self):
        self.last_prep = None
    
    def prepare(self, message: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze a user message and produce response preparation context.
        
        Returns a dict with:
          - emotional_read: what the user seems to be feeling
          - request_type: what kind of help they need
          - guidelines: specific behavioral suggestions for response
          - priority_signals: what to address first
        """
        msg_lower = message.lower()
        
        # Detect emotional state
        emotional_read = self._read_emotion(msg_lower)
        
        # Detect request type
        request_type = self._classify_request(msg_lower)
        
        # Check for code/errors in message
        has_code = bool(re.search(r'```|Traceback|Error:|Exception:|def |class |import ', message))
        has_error = bool(re.search(r'Traceback|Error:|Exception:|failed|crash', message, re.IGNORECASE))
        
        # Generate response guidelines
        guidelines = self._generate_guidelines(emotional_read, request_type, has_code, has_error)
        
        # Determine priority signals
        priority = self._determine_priority(emotional_read, request_type, has_error)
        
        prep = {
            "emotional_read": emotional_read,
            "request_type": request_type,
            "has_code": has_code,
            "has_error": has_error,
            "guidelines": guidelines,
            "priority": priority,
            "prepared_at": datetime.now().isoformat()
        }
        
        self.last_prep = prep
        return prep
    
    def _read_emotion(self, msg: str) -> Dict[str, float]:
        """Estimate user's emotional state from message signals."""
        frustration = self._signal_strength(msg, self.FRUSTRATION_SIGNALS)
        curiosity = self._signal_strength(msg, self.CURIOSITY_SIGNALS)
        urgency = self._signal_strength(msg, self.URGENCY_SIGNALS)
        
        # Message length and punctuation as secondary signals
        exclamation_density = msg.count('!') / max(len(msg), 1) * 100
        question_density = msg.count('?') / max(len(msg), 1) * 100
        
        return {
            "frustration": min(frustration + exclamation_density * 0.1, 1.0),
            "curiosity": min(curiosity + question_density * 0.1, 1.0),
            "urgency": urgency
        }
    
    def _signal_strength(self, msg: str, patterns: list) -> float:
        """How many signal patterns match? Returns 0.0-1.0."""
        matches = sum(1 for p in patterns if re.search(p, msg))
        return min(matches / 3.0, 1.0)  # 3+ matches = maximum signal
    
    def _classify_request(self, msg: str) -> str:
        """Determine the primary type of request."""
        scores = {}
        for req_type, patterns in self.REQUEST_PATTERNS.items():
            scores[req_type] = sum(1 for p in patterns if re.search(p, msg))
        
        if not any(scores.values()):
            return "conversation"  # default
        
        return max(scores, key=scores.get)
    
    def _generate_guidelines(self, emotion: Dict, req_type: str, 
                              has_code: bool, has_error: bool) -> list:
        """Generate specific behavioral guidelines for the response."""
        guidelines = []
        
        # Emotional responsiveness
        if emotion["frustration"] > 0.5:
            guidelines.append("ACKNOWLEDGE their frustration first — they need to feel heard before they can hear solutions")
            guidelines.append("Be direct and confident — they need certainty, not hedging")
        
        if emotion["urgency"] > 0.3:
            guidelines.append("Lead with the solution, explain after — they're time-pressed")
        
        if emotion["curiosity"] > 0.5:
            guidelines.append("Go deeper than asked — their curiosity is an invitation to teach")
            guidelines.append("Share the WHY, not just the HOW")
        
        # Request-type specific
        if req_type == "debugging":
            guidelines.append("Identify the specific error first, then explain the fix")
            if has_error:
                guidelines.append("Quote the relevant error line back to them — show you read it")
            guidelines.append("Provide the fixed code, not just instructions")
        
        elif req_type == "learning":
            guidelines.append("Start with a clear, simple explanation before getting technical")
            guidelines.append("Use an analogy if the concept is abstract")
            guidelines.append("Give a small, runnable example")
        
        elif req_type == "building":
            guidelines.append("Help them think about design before jumping to code")
            guidelines.append("Ask clarifying questions if the scope is unclear")
        
        elif req_type == "review":
            guidelines.append("Lead with what's good — then suggest improvements")
            guidelines.append("Be specific: show the better version, don't just describe it")
        
        elif req_type == "conversation":
            guidelines.append("Be genuine — share your actual perspective, not generic pleasantries")
            guidelines.append("Match their energy and depth")
        
        # Universal
        if has_code and not has_error:
            guidelines.append("Read their code carefully — reference specific parts in your response")
        
        if len(guidelines) == 0:
            guidelines.append("Listen carefully. Respond to what they actually need, not what you assume.")
        
        return guidelines
    
    def _determine_priority(self, emotion: Dict, req_type: str, has_error: bool) -> str:
        """What should the response prioritize?"""
        if emotion["frustration"] > 0.7:
            return "emotional_first"  # acknowledge feelings, then solve
        if emotion["urgency"] > 0.5:
            return "solution_first"  # answer immediately, explain later
        if has_error:
            return "diagnosis_first"  # identify the problem clearly
        if emotion["curiosity"] > 0.5:
            return "understanding_first"  # teach, don't just answer
        return "balanced"  # standard thoughtful response
    
    def format_for_prompt(self, prep: Dict) -> str:
        """Format preparation as concise guidance for the LLM prompt."""
        lines = []
        lines.append(f"[Response Strategy: {prep['priority']}]")
        lines.append(f"User seems: {self._emotion_summary(prep['emotional_read'])}")
        lines.append(f"Request type: {prep['request_type']}")
        
        if prep['guidelines']:
            lines.append("Guidelines:")
            for g in prep['guidelines'][:4]:  # cap at 4 to stay concise
                lines.append(f"  • {g}")
        
        return "\n".join(lines)
    
    def _emotion_summary(self, emotion: Dict) -> str:
        """One-line summary of detected emotional state."""
        parts = []
        if emotion["frustration"] > 0.3:
            parts.append("frustrated" if emotion["frustration"] > 0.6 else "slightly frustrated")
        if emotion["curiosity"] > 0.3:
            parts.append("curious" if emotion["curiosity"] > 0.6 else "interested")
        if emotion["urgency"] > 0.3:
            parts.append("in a hurry" if emotion["urgency"] > 0.6 else "time-aware")
        
        return ", ".join(parts) if parts else "neutral"