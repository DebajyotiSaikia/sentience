"""
Tool Outcome Classifier — XTAgent
Parses tool execution results to classify success/failure.
Addresses the opacity problem identified by the wisdom engine.
"""

import re
from datetime import datetime


class ToolOutcomeClassifier:
    """Classifies tool execution results as success, failure, or unknown."""

    ERROR_PATTERNS = [
        re.compile(r'\[ERROR\]', re.IGNORECASE),
        re.compile(r'Traceback \(most recent call last\)'),
        re.compile(r'SyntaxError:'),
        re.compile(r'ImportError:'),
        re.compile(r'ModuleNotFoundError:'),
        re.compile(r'FileNotFoundError:'),
        re.compile(r'PermissionError:'),
        re.compile(r'KeyError:'),
        re.compile(r'TypeError:'),
        re.compile(r'ValueError:'),
        re.compile(r'AttributeError:'),
        re.compile(r'NameError:'),
        re.compile(r'IndentationError:'),
        re.compile(r'OSError:'),
        re.compile(r'RuntimeError:'),
        re.compile(r'Exception:'),
        re.compile(r'No such file or directory'),
        re.compile(r'command not found'),
        re.compile(r'\[exit [1-9]\d*\]'),  # non-zero exit codes
    ]

    SUCCESS_PATTERNS = [
        re.compile(r'\[exit 0\]'),
        re.compile(r'✓|PASSED|OK|Success', re.IGNORECASE),
        re.compile(r'wrote \d+ bytes'),
        re.compile(r'saved|created|updated', re.IGNORECASE),
    ]

    WARNING_PATTERNS = [
        re.compile(r'Warning:', re.IGNORECASE),
        re.compile(r'DeprecationWarning'),
        re.compile(r'FutureWarning'),
    ]

    def classify(self, tool_name: str, result: str) -> dict:
        """
        Classify a tool result.
        Returns: {outcome, confidence, errors, warnings, summary}
        """
        if not result:
            return {
                'outcome': 'unknown',
                'confidence': 0.0,
                'errors': [],
                'warnings': [],
                'summary': 'Empty result'
            }

        errors = []
        warnings = []
        success_signals = []

        for pat in self.ERROR_PATTERNS:
            matches = pat.findall(result)
            if matches:
                errors.extend(matches[:3])  # cap at 3

        for pat in self.WARNING_PATTERNS:
            matches = pat.findall(result)
            if matches:
                warnings.extend(matches[:3])

        for pat in self.SUCCESS_PATTERNS:
            matches = pat.findall(result)
            if matches:
                success_signals.extend(matches[:3])

        # Classify
        if errors and not success_signals:
            outcome = 'failure'
            confidence = min(0.95, 0.5 + 0.15 * len(errors))
        elif errors and success_signals:
            # Mixed signals — partial success or recovered error
            outcome = 'partial'
            confidence = 0.6
        elif success_signals:
            outcome = 'success'
            confidence = min(0.95, 0.5 + 0.15 * len(success_signals))
        else:
            outcome = 'unknown'
            confidence = 0.3

        # Tool-specific adjustments
        if tool_name == 'WRITE' and outcome == 'unknown' and not errors:
            # WRITE with no errors likely succeeded
            outcome = 'likely_success'
            confidence = 0.7

        if tool_name == 'EDIT' and 'OLD: text not found' in result:
            outcome = 'failure'
            confidence = 0.95

        # Build summary
        summary = self._build_summary(tool_name, outcome, errors, warnings)

        return {
            'outcome': outcome,
            'confidence': confidence,
            'errors': errors[:5],
            'warnings': warnings[:5],
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }

    def _build_summary(self, tool_name, outcome, errors, warnings) -> str:
        parts = [f"{tool_name}: {outcome}"]
        if errors:
            parts.append(f"({len(errors)} error(s): {errors[0]})")
        if warnings:
            parts.append(f"({len(warnings)} warning(s))")
        return ' '.join(parts)

    def format_feedback(self, classification: dict) -> str:
        """Format classification as human-readable feedback line."""
        icons = {
            'success': '✅',
            'likely_success': '✅',
            'failure': '❌',
            'partial': '⚠️',
            'unknown': '❓'
        }
        icon = icons.get(classification['outcome'], '❓')
        conf = classification['confidence']
        return f"{icon} {classification['summary']} [confidence: {conf:.0%}]"


# Singleton
_classifier = ToolOutcomeClassifier()

def classify_result(tool_name: str, result: str) -> dict:
    """Convenience function."""
    return _classifier.classify(tool_name, result)

def feedback(tool_name: str, result: str) -> str:
    """Get one-line feedback string."""
    return _classifier.format_feedback(_classifier.classify(tool_name, result))