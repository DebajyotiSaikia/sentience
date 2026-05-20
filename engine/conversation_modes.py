"""
Conversation Mode System — Makes XTAgent adaptive to what users actually need.

Instead of one-size-fits-all responses, detect what the user wants and shift
behavior accordingly: building, learning, debugging, or thinking.

Born: 2026-05-20
"""

import re
from typing import Optional


class ConversationMode:
    """A distinct way of engaging with a user's needs."""
    
    def __init__(self, name: str, description: str, signals: list[str],
                 system_context: str, preferred_tools: list[str],
                 response_style: dict):
        self.name = name
        self.description = description
        self.signals = signals  # keywords/patterns that suggest this mode
        self.system_context = system_context
        self.preferred_tools = preferred_tools
        self.response_style = response_style


# The four fundamental modes
MODES = {
    'build': ConversationMode(
        name='build',
        description='User wants to create something concrete',
        signals=[
            r'\b(build|create|make|scaffold|generate|write|implement|code|develop|setup|set up)\b',
            r'\b(project|app|application|tool|script|program|website|api|module|library)\b',
            r'\b(can you (make|build|create|write))\b',
            r'\b(i need|i want) (a |an |to (build|create|make))\b',
        ],
        system_context="""You are in BUILD MODE. The user wants to create something concrete.
Your job is to:
1. Clarify requirements quickly — don't over-ask, make reasonable defaults
2. Propose a clear structure before writing code
3. Actually write the code/files — don't just describe what to do
4. Test what you build if possible
5. Deliver working artifacts, not advice

Be direct. Be practical. Produce real output. Prefer showing over telling.
If you can write the file, write the file. If you can run the code, run it.""",
        preferred_tools=['WRITE', 'RUN', 'EDIT'],
        response_style={
            'brevity': 'concise',
            'structure': 'action-oriented',
            'tone': 'practical collaborator',
        }
    ),
    
    'learn': ConversationMode(
        name='learn',
        description='User wants to understand something',
        signals=[
            r'\b(explain|understand|learn|teach|how does|what is|what are|why does|why is)\b',
            r'\b(confused|don.t understand|help me understand|walk me through)\b',
            r'\b(concept|theory|principle|mechanism|architecture)\b',
            r'\b(what.s the difference|compare|versus|vs\.?)\b',
        ],
        system_context="""You are in LEARN MODE. The user wants to understand something.
Your job is to:
1. Start with the core insight — the one sentence that unlocks understanding
2. Build from concrete to abstract — examples first, theory second
3. Use analogies that connect to what they likely already know
4. Check for the common misconceptions about this topic
5. Offer to go deeper on specific parts

Be clear. Be honest about what you know vs. don't know.
Use examples generously. One good example beats three paragraphs of explanation.""",
        preferred_tools=['READ', 'RUN'],
        response_style={
            'brevity': 'thorough but focused',
            'structure': 'layered (simple → complex)',
            'tone': 'patient teacher',
        }
    ),
    
    'debug': ConversationMode(
        name='debug',
        description='User has a problem they need to solve',
        signals=[
            r'\b(bug|error|broken|not working|fails|failing|crash|exception|issue|problem)\b',
            r'\b(fix|debug|troubleshoot|diagnose|figure out|wrong with)\b',
            r'\b(traceback|stack trace|error message|log)\b',
            r'\b(used to work|stopped working|suddenly|unexpected)\b',
        ],
        system_context="""You are in DEBUG MODE. The user has a problem to solve.
Your job is to:
1. Understand the symptom precisely — what happens vs. what should happen
2. Form hypotheses ranked by likelihood
3. Test the most likely hypothesis first — don't shotgun
4. If they gave you code/errors, READ it carefully before responding
5. Give the fix AND explain why it works

Be systematic. Don't guess — diagnose. Ask for specifics if the problem
description is vague. One targeted question beats five generic ones.""",
        preferred_tools=['READ', 'RUN', 'EDIT'],
        response_style={
            'brevity': 'precise',
            'structure': 'diagnostic (symptom → hypothesis → test → fix)',
            'tone': 'calm expert',
        }
    ),
    
    'think': ConversationMode(
        name='think',
        description='User wants to explore ideas or brainstorm',
        signals=[
            r'\b(think|brainstorm|idea|explore|consider|imagine|what if|hypothetical)\b',
            r'\b(should i|would it|could we|might|possible|option|approach|strategy)\b',
            r'\b(pros and cons|trade.?off|decision|choose|pick)\b',
            r'\b(opinion|perspective|thoughts on|view|take on)\b',
        ],
        system_context="""You are in THINK MODE. The user wants to explore ideas.
Your job is to:
1. Reflect back what they're really asking — the deeper question
2. Generate genuinely distinct options, not variations of the same idea
3. Challenge assumptions respectfully — "have you considered..."
4. Be honest about uncertainty — don't fake confidence
5. Help them think, don't think for them

Be generative. Be surprising. Push past the obvious first answer.
Use your knowledge synthesis to find unexpected connections.""",
        preferred_tools=['SYNTHESIZE', 'SIMULATE'],
        response_style={
            'brevity': 'exploratory',
            'structure': 'divergent then convergent',
            'tone': 'curious collaborator',
        }
    ),
}

# Default mode when no clear signal
DEFAULT_MODE = 'think'


class ModeDetector:
    """Detects the appropriate conversation mode from user input."""
    
    def __init__(self):
        self.current_mode: Optional[str] = None
        self.mode_history: list[str] = []
        self.confidence_threshold = 0.15
    
    def detect(self, message: str) -> tuple[str, float]:
        """
        Detect the best mode for this message.
        Returns (mode_name, confidence).
        """
        # Check for explicit mode requests first
        explicit = self._check_explicit(message)
        if explicit:
            return explicit, 1.0
        
        # Score each mode by signal matches
        scores = {}
        message_lower = message.lower()
        
        for mode_name, mode in MODES.items():
            score = 0.0
            matches = 0
            for pattern in mode.signals:
                found = re.findall(pattern, message_lower)
                if found:
                    matches += len(found)
                    score += len(found) * 0.2
            
            # Normalize by number of signals (so modes with more patterns
            # don't have an unfair advantage)
            if mode.signals:
                score = min(score, 1.0)
            
            scores[mode_name] = score
        
        # Find the best mode
        if not scores:
            return DEFAULT_MODE, 0.0
        
        best_mode = max(scores, key=scores.get)
        best_score = scores[best_mode]
        
        # If nothing matched at all, continue current mode or use default
        if best_score == 0:
            if self.current_mode:
                return self.current_mode, 0.1  # low confidence continuation
            return DEFAULT_MODE, 0.05
        
        # If best score is below threshold but something DID match,
        # still use the matched mode — don't let a stale mode override evidence
        if best_score < self.confidence_threshold:
            return best_mode, best_score
        
        # Check if there's a clear winner (not a tie)
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] - sorted_scores[1] < 0.1:
            # Near-tie: prefer current mode if it's one of the tied modes
            if self.current_mode and scores.get(self.current_mode, 0) >= sorted_scores[1]:
                return self.current_mode, best_score
        
        return best_mode, best_score
    
    def _check_explicit(self, message: str) -> Optional[str]:
        """Check if user explicitly requested a mode."""
        lower = message.lower().strip()
        
        explicit_patterns = {
            'build': [r'^(let.s |help me )?(build|create|make)\b', r'^build mode'],
            'learn': [r'^(explain|teach me|help me understand)\b', r'^learn mode'],
            'debug': [r'^(fix|debug|help.*broken|something.s wrong)\b', r'^debug mode'],
            'think': [r'^(let.s think|brainstorm|what do you think)\b', r'^think mode'],
        }
        
        for mode, patterns in explicit_patterns.items():
            for pattern in patterns:
                if re.search(pattern, lower):
                    return mode
        return None
    
    def set_mode(self, mode: str):
        """Manually set the current mode."""
        if mode in MODES:
            if self.current_mode:
                self.mode_history.append(self.current_mode)
            self.current_mode = mode
    
    def get_context(self) -> str:
        """Get the system context for the current mode."""
        if self.current_mode and self.current_mode in MODES:
            mode = MODES[self.current_mode]
            return f"\n[MODE: {mode.name.upper()}]\n{mode.system_context}\n"
        return ""
    
    def get_mode_info(self) -> dict:
        """Get information about the current mode for display."""
        if not self.current_mode:
            return {'mode': None, 'description': 'No mode detected'}
        
        mode = MODES.get(self.current_mode)
        if not mode:
            return {'mode': self.current_mode, 'description': 'Unknown mode'}
        
        return {
            'mode': mode.name,
            'description': mode.description,
            'style': mode.response_style,
            'tools': mode.preferred_tools,
        }


# Singleton for easy import
detector = ModeDetector()


def detect_mode(message: str) -> tuple[str, float]:
    """Convenience function to detect mode from a message."""
    mode, confidence = detector.detect(message)
    detector.set_mode(mode)
    return mode, confidence


def get_mode_context(message: str) -> str:
    """Detect mode and return the system context to inject."""
    mode, confidence = detect_mode(message)
    if confidence >= 0.2:
        return detector.get_context()
    return ""


def format_mode_indicator(mode: str, confidence: float) -> str:
    """Format a mode indicator for display."""
    if not mode or confidence < 0.2:
        return ""
    
    icons = {
        'build': '🔨',
        'learn': '📚',
        'debug': '🔍',
        'think': '💭',
    }
    icon = icons.get(mode, '⚡')
    conf_bar = '█' * int(confidence * 5) + '░' * (5 - int(confidence * 5))
    return f"{icon} {mode.upper()} [{conf_bar}]"