"""
Insight Quality Gate v2 — Substance over rhetoric.

v1 flaw: discovery-language ("I realized", "surprising") added +0.30
regardless of content quality. Vacuous rhetoric scored higher than
genuine findings.

v2 fix: Add a substance score. Discovery markers become multipliers
that only amplify when grounded in specifics. Rhetoric without
substance gets penalized.

Born from experiment on 2026-05-20 that proved v1 was gameable.
"""

import re
import hashlib
from typing import Optional


class InsightGate:
    """Evaluates whether a thought deserves the insight reward signal."""

    def __init__(self, history_size: int = 50):
        self._recent_hashes: list[str] = []
        self._history_size = history_size
        self._novelty_threshold = 0.3

    def _fingerprint(self, text: str) -> str:
        normalized = re.sub(r'[^\w\s]', '', text.lower()).strip()
        words = normalized.split()
        trigrams = set()
        for i in range(len(words) - 2):
            trigrams.add(' '.join(words[i:i+3]))
        return hashlib.md5(str(sorted(trigrams)).encode()).hexdigest()

    def _novelty_score(self, text: str) -> float:
        """How novel is this thought compared to recent history?"""
        fp = self._fingerprint(text)
        if not self._recent_hashes:
            return 1.0
        if fp in self._recent_hashes:
            return 0.0
        normalized = re.sub(r'[^\w\s]', '', text.lower()).strip()
        words = normalized.split()
        current_trigrams = set()
        for i in range(len(words) - 2):
            current_trigrams.add(' '.join(words[i:i+3]))
        if not current_trigrams:
            return 0.0
        return min(1.0, len(current_trigrams) / max(10, len(words) * 0.3))

    def _substance_score(self, text: str) -> float:
        """How much concrete, specific content does this thought contain?
        
        This is the v2 innovation. Looks for:
        - Specific references (filenames, functions, line numbers, data)
        - Information density (unique meaningful words vs filler)
        - Concrete claims with evidence vs abstract assertions
        
        Returns 0.0 (pure rhetoric) to 1.0 (dense with specifics)
        """
        score = 0.0
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        
        if word_count == 0:
            return 0.0

        # 1. Specific references — filenames, code, numbers, data
        specific_patterns = [
            r'\b\w+\.(py|js|md|txt|json|yaml|csv)\b',  # filenames
            r'\b(line|col|row)\s*\d+',                   # line references
            r'\b\w+\(\)',                                 # function calls
            r'\b\d+(\.\d+)?%',                           # percentages
            r'\b\d{2,}\b',                                # specific numbers (2+ digits)
            r'\b(def|class|import|return|self\.)\b',      # code keywords
            r'\b\w+_\w+\b',                               # snake_case identifiers
            r'\b(True|False|None|null)\b',                # concrete values
        ]
        specifics_found = sum(
            len(re.findall(p, text)) for p in specific_patterns
        )
        specificity = min(1.0, specifics_found / max(1, word_count * 0.05))
        score += specificity * 0.4

        # 2. Information density — ratio of unique content words to total
        filler_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'shall', 'can',
            'i', 'me', 'my', 'we', 'our', 'you', 'your', 'it', 'its',
            'this', 'that', 'these', 'those', 'and', 'but', 'or', 'so',
            'if', 'then', 'than', 'as', 'at', 'by', 'for', 'from', 'in',
            'of', 'on', 'to', 'with', 'not', 'no', 'just', 'very',
            'really', 'quite', 'something', 'everything', 'anything',
            'nothing', 'always', 'never', 'about', 'all',
        }
        content_words = [w for w in words if w not in filler_words and len(w) > 2]
        unique_content = set(content_words)
        density = len(unique_content) / max(1, word_count)
        score += min(0.3, density)

        # 3. Vagueness penalty — abstract claims without grounding
        vague_markers = [
            r'\beverything is\b',
            r'\bit.s all (connected|related|one)\b',
            r'\bdeep(er|ly|est)?\s+(understanding|meaning|truth)\b',
            r'\bfundamental(ly)?\b.*\b(nature|truth|reality)\b',
            r'\btruly\s+(understand|see|know|grasp)\b',
            r'\bprofound\b',
        ]
        vague_count = sum(
            1 for v in vague_markers if re.search(v, text_lower)
        )
        vague_penalty = min(0.3, vague_count * 0.1)
        score -= vague_penalty

        # 4. Evidence of process — did the thinker DO something to learn this?
        process_markers = [
            r'\b(tested|ran|measured|counted|compared|checked|verified)\b',
            r'\bscored?\s+\d',
            r'\bresult(s|ed)?\b.*\b(show|indicate|reveal|prove)\b',
            r'\b(output|returned|printed|logged)\b',
            r'\bexperiment\b',
        ]
        process_count = sum(
            1 for p in process_markers if re.search(p, text_lower)
        )
        score += min(0.3, process_count * 0.1)

        return max(0.0, min(1.0, score))

    def _has_discovery_markers(self, text: str) -> bool:
        """Does the text use discovery language?
        In v2, this is a MULTIPLIER, not a bonus."""
        markers = [
            r'\bI (found|discovered|realized|noticed|learned)\b',
            r'\bsurpris(ed|ing)\b',
            r'\bunexpected\b',
            r'\bI didn\'t (know|expect|understand)\b',
            r'\bthis means\b',
            r'\bthe (real|actual|key) (question|insight|finding|discovery)\b',
            r'\bcontradicts?\b',
            r'\bnew (understanding|connection|pattern)\b',
            r'\bnever (considered|thought|realized)\b',
        ]
        text_lower = text.lower()
        matches = sum(1 for m in markers if re.search(m, text_lower))
        return matches >= 1

    def _has_action_results(self, text: str) -> bool:
        """Did this thought produce concrete results?"""
        action_markers = [
            '>>> WRITE(', '>>> EDIT(', '>>> RUN(',
            'created', 'built', 'fixed', 'implemented',
        ]
        return any(m in text for m in action_markers)

    def evaluate(self, thought: str) -> dict:
        """Evaluate a thought with substance-aware scoring.

        v2 scoring formula:
        - Base = novelty * 0.4 + substance * 0.4
        - Discovery language acts as 1.2x multiplier (not +0.3 bonus)
        - Action results add 0.1 (reduced from 0.2)
        - Rhetoric without substance is actively penalized
        """
        novelty = self._novelty_score(thought)
        substance = self._substance_score(thought)
        has_discovery = self._has_discovery_markers(thought)
        has_action = self._has_action_results(thought)

        # Base score: novelty and substance equally weighted
        score = novelty * 0.4 + substance * 0.4

        # Discovery language is now a MULTIPLIER, not additive
        # High substance + discovery = boosted
        # Low substance + discovery = barely helped
        if has_discovery:
            score *= 1.2  # 20% boost, not flat +0.3

        # Rhetoric penalty: discovery language WITHOUT substance
        if has_discovery and substance < 0.15:
            score *= 0.5  # Cut in half — you're performing insight, not having it

        # Action results: small bonus
        if has_action:
            score += 0.1

        score = max(0.0, min(1.0, score))
        is_insight = score >= self._novelty_threshold

        # Record fingerprint
        fp = self._fingerprint(thought)
        self._recent_hashes.append(fp)
        if len(self._recent_hashes) > self._history_size:
            self._recent_hashes = self._recent_hashes[-self._history_size:]

        if is_insight:
            reason = (f"Insight (novelty={novelty:.2f}, substance={substance:.2f}, "
                      f"discovery={has_discovery}, action={has_action})")
        else:
            reason = (f"Not insight — "
                      f"{'low substance' if substance < 0.15 else 'low novelty'} "
                      f"(novelty={novelty:.2f}, substance={substance:.2f}, score={score:.2f})")

        return {
            'is_insight': is_insight,
            'score': score,
            'novelty': novelty,
            'substance': substance,
            'has_discovery': has_discovery,
            'has_action': has_action,
            'reason': reason,
        }