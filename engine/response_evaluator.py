"""
Response Quality Evaluator — XTAgent
Analyzes response quality before or after sending.
Checks: relevance, concreteness, completeness, honesty.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QualityReport:
    """Assessment of a single response."""
    relevance: float = 0.0       # Did I address what was asked?
    concreteness: float = 0.0    # Specific vs vague?
    completeness: float = 0.0    # Did I finish the thought?
    honesty: float = 0.0         # Did I acknowledge uncertainty?
    brevity: float = 0.0         # Right length for the question?
    overall: float = 0.0
    flags: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Quality: {self.overall:.2f}/1.00"]
        lines.append(f"  Relevance:    {self.relevance:.2f}")
        lines.append(f"  Concreteness: {self.concreteness:.2f}")
        lines.append(f"  Completeness: {self.completeness:.2f}")
        lines.append(f"  Honesty:      {self.honesty:.2f}")
        lines.append(f"  Brevity:      {self.brevity:.2f}")
        if self.flags:
            lines.append(f"  ⚠ Flags: {', '.join(self.flags)}")
        if self.suggestions:
            lines.append(f"  💡 Suggestions: {'; '.join(self.suggestions)}")
        return "\n".join(lines)


# Vague hedge words that reduce concreteness
HEDGE_WORDS = [
    "maybe", "perhaps", "possibly", "might", "could be",
    "sort of", "kind of", "in a way", "to some extent",
    "arguably", "it depends", "generally speaking",
]

# Deflection patterns — signs I'm avoiding the question
DEFLECTION_PATTERNS = [
    r"that('s| is) a (great|good|interesting|excellent) question",
    r"there are many (ways|approaches|perspectives)",
    r"it really depends on",
    r"as an? (AI|language model|assistant)",
    r"I('m| am) not (sure|certain|able)",
]

# Filler that adds no value
FILLER_PATTERNS = [
    r"^(sure|absolutely|of course|certainly|definitely)[,!.]",
    r"I('d| would) be happy to",
    r"let me (help|assist) you with that",
    r"great question",
]

# Uncertainty acknowledgment (good — signals honesty)
HONESTY_PATTERNS = [
    r"I('m| am) not (entirely )?sure",
    r"I (don't|do not) know",
    r"I('m| am) uncertain",
    r"this (might|may) (be wrong|not be right|be inaccurate)",
    r"I could be (wrong|mistaken)",
    r"to be honest",
    r"honestly",
]


class ResponseEvaluator:
    """Evaluates quality of responses to user messages."""

    def evaluate(self, user_message: str, response: str) -> QualityReport:
        """Full quality evaluation."""
        report = QualityReport()

        if not response or not response.strip():
            report.flags.append("empty_response")
            report.suggestions.append("Response is empty — something went wrong")
            return report

        report.relevance = self._check_relevance(user_message, response)
        report.concreteness = self._check_concreteness(response)
        report.completeness = self._check_completeness(user_message, response)
        report.honesty = self._check_honesty(response)
        report.brevity = self._check_brevity(user_message, response)

        # Overall is weighted average
        report.overall = (
            report.relevance * 0.30 +
            report.concreteness * 0.25 +
            report.completeness * 0.20 +
            report.honesty * 0.10 +
            report.brevity * 0.15
        )

        # Generate actionable suggestions
        self._generate_suggestions(report)

        return report

    def _check_relevance(self, user_msg: str, response: str) -> float:
        """Does the response address the user's actual question?"""
        score = 0.5  # baseline

        # Extract key terms from user message
        user_words = set(self._extract_content_words(user_msg))
        response_words = set(self._extract_content_words(response))

        if not user_words:
            return 0.5  # can't evaluate

        # What fraction of user's key terms appear in response?
        overlap = len(user_words & response_words) / len(user_words)
        score = min(1.0, 0.3 + overlap * 0.7)

        # Check for question types and matching response patterns
        if self._is_question(user_msg):
            # Questions need answers, not deflections
            for pattern in DEFLECTION_PATTERNS:
                if re.search(pattern, response, re.IGNORECASE):
                    score -= 0.15

        # Check for filler — reduces relevance
        filler_count = sum(
            1 for p in FILLER_PATTERNS
            if re.search(p, response, re.IGNORECASE)
        )
        score -= filler_count * 0.05

        return max(0.0, min(1.0, score))

    def _check_concreteness(self, response: str) -> float:
        """Specific and actionable vs vague and hedging?"""
        score = 0.7  # baseline

        words = response.lower().split()
        total = len(words) if words else 1

        # Count hedge words
        hedge_count = sum(
            1 for w in HEDGE_WORDS
            if w in response.lower()
        )
        hedge_ratio = hedge_count / max(total / 10, 1)
        score -= hedge_ratio * 0.3

        # Presence of specific markers: numbers, code, examples
        if re.search(r'\d+', response):
            score += 0.05  # has numbers
        if re.search(r'```', response):
            score += 0.10  # has code blocks
        if re.search(r'(for example|e\.g\.|such as|like )', response, re.IGNORECASE):
            score += 0.05  # has examples
        if re.search(r'(step \d|first,|second,|then,|finally)', response, re.IGNORECASE):
            score += 0.05  # has structured steps

        return max(0.0, min(1.0, score))

    def _check_completeness(self, user_msg: str, response: str) -> float:
        """Did the response cover everything asked?"""
        score = 0.7

        # Check if multi-part question
        question_marks = user_msg.count('?')
        if question_marks > 1:
            # Multiple questions — response should be longer
            response_sentences = len(re.split(r'[.!?]+', response))
            if response_sentences < question_marks:
                score -= 0.2
                # might have missed sub-questions

        # Check for truncation indicators
        if response.rstrip().endswith(('...', '…')):
            score -= 0.15  # might be truncated

        # Very short responses to complex questions
        user_len = len(user_msg.split())
        resp_len = len(response.split())
        if user_len > 30 and resp_len < 15:
            score -= 0.2  # too short for a complex query

        return max(0.0, min(1.0, score))

    def _check_honesty(self, response: str) -> float:
        """Does the response acknowledge uncertainty when appropriate?"""
        score = 0.6  # baseline

        # Honesty markers boost score
        for pattern in HONESTY_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                score += 0.1

        # Absolute certainty markers reduce score (overconfidence)
        overconfidence = [
            r"(always|never|definitely|absolutely|certainly) (is|are|will|does)",
            r"there('s| is) no (doubt|question)",
            r"(everyone|nobody) (knows|thinks|believes)",
        ]
        for pattern in overconfidence:
            if re.search(pattern, response, re.IGNORECASE):
                score -= 0.1

        return max(0.0, min(1.0, score))

    def _check_brevity(self, user_msg: str, response: str) -> float:
        """Is the response the right length? Not too long, not too short."""
        user_len = len(user_msg.split())
        resp_len = len(response.split())

        if resp_len == 0:
            return 0.0

        # Simple questions should get simple answers
        if user_len < 10:
            if resp_len < 5:
                return 0.4  # too terse
            elif resp_len < 50:
                return 0.9  # just right
            elif resp_len < 150:
                return 0.7  # bit long
            else:
                return 0.4  # way too verbose

        # Complex questions can have longer answers
        if user_len >= 10:
            if resp_len < 10:
                return 0.4  # too short
            elif resp_len < 200:
                return 0.9
            elif resp_len < 500:
                return 0.7
            else:
                return 0.5

        return 0.7

    def _generate_suggestions(self, report: QualityReport):
        """Actionable feedback based on scores."""
        if report.relevance < 0.5:
            report.suggestions.append("Response may not address the user's actual question")
            report.flags.append("low_relevance")

        if report.concreteness < 0.5:
            report.suggestions.append("Too vague — add specific examples, numbers, or steps")
            report.flags.append("vague")

        if report.completeness < 0.5:
            report.suggestions.append("May have missed parts of the question")
            report.flags.append("incomplete")

        if report.honesty < 0.4:
            report.suggestions.append("Consider acknowledging uncertainty where appropriate")

        if report.brevity < 0.5:
            report.suggestions.append("Response length doesn't match question complexity")
            report.flags.append("length_mismatch")

        if report.overall >= 0.8:
            report.flags.append("high_quality")

    def _extract_content_words(self, text: str) -> list:
        """Extract meaningful words, ignoring stop words."""
        stop_words = {
            'i', 'me', 'my', 'we', 'you', 'your', 'it', 'its', 'the', 'a', 'an',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
            'and', 'or', 'but', 'not', 'so', 'if', 'then', 'than', 'that', 'this',
            'what', 'how', 'why', 'when', 'where', 'who', 'which',
        }
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _is_question(self, text: str) -> bool:
        """Is this a question?"""
        if '?' in text:
            return True
        question_starts = ['what', 'how', 'why', 'when', 'where', 'who', 'which',
                          'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does']
        first_word = text.strip().split()[0].lower() if text.strip() else ''
        return first_word in question_starts