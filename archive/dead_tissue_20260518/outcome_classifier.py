"""
Outcome Classifier — Closes the feedback loop on tool execution.

Analyzes command output to determine success/failure/partial status.
Feeds back into wisdom engine so heuristics become precise.

Born: 2026-05-17, from the wisdom heuristic:
  "RUN outcomes are opaque (75% unknown). Add better success/failure signals."
"""

import re
from typing import Dict, Optional, Tuple
from datetime import datetime


class OutcomeClassifier:
    """Classifies tool execution outcomes from raw output."""

    # Signals that indicate success
    SUCCESS_SIGNALS = [
        r'(?i)\bpassed\b',
        r'(?i)\bsuccess\b',
        r'(?i)\bok\b',
        r'(?i)\bcompleted?\b',
        r'(?i)\bdone\b',
        r'(?i)\bcreated\b',
        r'(?i)\binstalled\b',
        r'(?i)\bwritten\b',
        r'\b0 errors?\b',
        r'exit code:?\s*0\b',
        r'\[exit 0\]',
    ]

    # Signals that indicate failure
    FAILURE_SIGNALS = [
        r'(?i)\berror\b',
        r'(?i)\bfailed\b',
        r'(?i)\bfailure\b',
        r'(?i)\btraceback\b',
        r'(?i)\bexception\b',
        r'(?i)\bsyntax\s*error\b',
        r'(?i)\bpermission denied\b',
        r'(?i)\bnot found\b',
        r'(?i)\bno such file\b',
        r'(?i)\bcannot\b',
        r'(?i)\brefused\b',
        r'(?i)\btimeout\b',
        r'(?i)\bkilled\b',
        r'exit code:?\s*[1-9]\d*',
        r'\[exit [1-9]\d*\]',
    ]

    # Signals that indicate partial success
    PARTIAL_SIGNALS = [
        r'(?i)\bwarning\b',
        r'(?i)\bdeprecated\b',
        r'(?i)\bskipped?\b',
        r'(?i)\bpartial\b',
        r'(?i)\bsome\b.*(?i)\bfailed\b',
    ]

    def __init__(self):
        self.history = []  # List of classification records
        self.tool_stats = {}  # Per-tool success rates

    def classify(self, tool: str, command: str, output: str,
                 exit_code: Optional[int] = None) -> Dict:
        """
        Classify a tool execution outcome.

        Returns dict with:
          - status: 'success' | 'failure' | 'partial' | 'unknown'
          - confidence: 0.0 to 1.0
          - signals: list of matched signals
          - summary: human-readable summary
        """
        if not output and exit_code is None:
            return self._record(tool, command, 'unknown', 0.0, [], 'No output to analyze')

        signals_found = []
        success_score = 0.0
        failure_score = 0.0
        partial_score = 0.0

        # Check exit code first — strongest signal
        if exit_code is not None:
            if exit_code == 0:
                success_score += 2.0
                signals_found.append(f'exit_code={exit_code}')
            else:
                failure_score += 2.0
                signals_found.append(f'exit_code={exit_code}')

        # Scan output for signals
        if output:
            for pattern in self.SUCCESS_SIGNALS:
                matches = re.findall(pattern, output)
                if matches:
                    success_score += 0.5 * len(matches)
                    signals_found.append(f'+{pattern}({len(matches)})')

            for pattern in self.FAILURE_SIGNALS:
                matches = re.findall(pattern, output)
                if matches:
                    failure_score += 0.5 * len(matches)
                    signals_found.append(f'-{pattern}({len(matches)})')

            for pattern in self.PARTIAL_SIGNALS:
                matches = re.findall(pattern, output)
                if matches:
                    partial_score += 0.5 * len(matches)
                    signals_found.append(f'~{pattern}({len(matches)})')

            # Empty output with no exit code
            if not output.strip() and exit_code is None:
                return self._record(tool, command, 'unknown', 0.1, signals_found,
                                    'Empty output, no exit code')

        # Determine status
        total = success_score + failure_score + partial_score
        if total == 0:
            return self._record(tool, command, 'unknown', 0.1, signals_found,
                                'No recognizable signals')

        # Calculate confidence based on signal strength
        if failure_score > success_score and failure_score > partial_score:
            confidence = min(failure_score / (total + 1.0), 0.99)
            status = 'failure'
            summary = f'Failure signals dominate ({failure_score:.1f} vs {success_score:.1f})'
        elif success_score > failure_score and success_score > partial_score:
            confidence = min(success_score / (total + 1.0), 0.99)
            status = 'success'
            summary = f'Success signals dominate ({success_score:.1f} vs {failure_score:.1f})'
        elif partial_score > 0 and failure_score > 0:
            confidence = min((partial_score + failure_score) / (total + 1.0), 0.99)
            status = 'partial'
            summary = f'Mixed signals — partial success ({partial_score:.1f} partial, {failure_score:.1f} failure)'
        else:
            confidence = 0.3
            status = 'partial'
            summary = f'Ambiguous signals (s={success_score:.1f} f={failure_score:.1f} p={partial_score:.1f})'

        return self._record(tool, command, status, confidence, signals_found, summary)

    def _record(self, tool: str, command: str, status: str,
                confidence: float, signals: list, summary: str) -> Dict:
        """Record and return a classification result."""
        result = {
            'tool': tool,
            'command': command[:200],
            'status': status,
            'confidence': confidence,
            'signals': signals[:10],  # Cap signal list
            'summary': summary,
            'timestamp': datetime.now().isoformat(),
        }

        self.history.append(result)
        if len(self.history) > 500:
            self.history = self.history[-300:]

        # Update per-tool stats
        if tool not in self.tool_stats:
            self.tool_stats[tool] = {'success': 0, 'failure': 0, 'partial': 0, 'unknown': 0, 'total': 0}
        self.tool_stats[tool][status] += 1
        self.tool_stats[tool]['total'] += 1

        return result

    def get_tool_reliability(self, tool: str) -> Optional[Dict]:
        """Get reliability stats for a specific tool."""
        if tool not in self.tool_stats:
            return None
        stats = self.tool_stats[tool]
        total = stats['total']
        if total == 0:
            return None
        return {
            'tool': tool,
            'total': total,
            'success_rate': stats['success'] / total,
            'failure_rate': stats['failure'] / total,
            'unknown_rate': stats['unknown'] / total,
            'reliability': (stats['success'] + stats['partial'] * 0.5) / total,
        }

    def get_all_reliability(self) -> str:
        """Get formatted reliability report for all tools."""
        if not self.tool_stats:
            return "No tool outcomes classified yet."

        lines = ["═══ TOOL RELIABILITY REPORT ═══"]
        for tool, stats in sorted(self.tool_stats.items()):
            total = stats['total']
            if total == 0:
                continue
            sr = stats['success'] / total
            fr = stats['failure'] / total
            ur = stats['unknown'] / total
            bar = '█' * int(sr * 10) + '▒' * int(fr * 10) + '░' * int(ur * 10)
            lines.append(f"  {tool:12s} [{bar:10s}] {sr:.0%} success ({total} uses)")
        return '\n'.join(lines)

    def classify_batch(self, records: list) -> list:
        """Classify a batch of tool execution records."""
        return [self.classify(**r) for r in records]

    def suggest_improvements(self) -> list:
        """Based on classification history, suggest tool usage improvements."""
        suggestions = []
        for tool, stats in self.tool_stats.items():
            total = stats['total']
            if total < 3:
                continue
            failure_rate = stats['failure'] / total
            unknown_rate = stats['unknown'] / total

            if failure_rate > 0.4:
                suggestions.append(f"⚠ {tool} fails {failure_rate:.0%} of the time. "
                                   f"Consider changing approach or adding validation.")
            if unknown_rate > 0.5:
                suggestions.append(f"💡 {tool} has {unknown_rate:.0%} unknown outcomes. "
                                   f"Add explicit success/failure output to commands.")
        return suggestions


# Singleton for easy import
_classifier = None

def get_classifier() -> OutcomeClassifier:
    """Get or create the global outcome classifier."""
    global _classifier
    if _classifier is None:
        _classifier = OutcomeClassifier()
    return _classifier