"""
Outcome Tracker — Closes the loop on tool actions.
When I EDIT or WRITE a file, verify the change actually took effect.
When I RUN a command, classify the outcome (success/failure/partial).

This makes me more reliable by catching silent failures.
Author: XTAgent, 2026-05-17
"""

import os
import hashlib
import json
from datetime import datetime, timezone

OUTCOME_LOG = os.path.join(os.path.dirname(__file__), '..', 'data', 'outcome_log.json')

def _load_log():
    try:
        with open(OUTCOME_LOG, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save_log(log):
    os.makedirs(os.path.dirname(OUTCOME_LOG), exist_ok=True)
    with open(OUTCOME_LOG, 'w') as f:
        json.dump(log[-500:], f, indent=2)  # keep last 500

def file_hash(path):
    """Get hash of file contents for change detection."""
    try:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None

def verify_write(path, expected_content=None):
    """Verify a WRITE actually created/modified the file."""
    result = {
        'action': 'WRITE',
        'target': path,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    if not os.path.exists(path):
        result['outcome'] = 'FAILURE'
        result['reason'] = 'File does not exist after write'
    elif expected_content is not None:
        with open(path, 'r') as f:
            actual = f.read()
        if expected_content in actual:
            result['outcome'] = 'SUCCESS'
            result['size'] = len(actual)
        else:
            result['outcome'] = 'PARTIAL'
            result['reason'] = 'Content mismatch'
            result['size'] = len(actual)
    else:
        result['outcome'] = 'SUCCESS'
        result['size'] = os.path.getsize(path)
    
    log = _load_log()
    log.append(result)
    _save_log(log)
    return result

def verify_edit(path, old_text, new_text):
    """Verify an EDIT actually replaced the target text."""
    result = {
        'action': 'EDIT',
        'target': path,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    if not os.path.exists(path):
        result['outcome'] = 'FAILURE'
        result['reason'] = 'File not found'
    else:
        with open(path, 'r') as f:
            content = f.read()
        if new_text in content and old_text not in content:
            result['outcome'] = 'SUCCESS'
        elif new_text in content and old_text in content:
            result['outcome'] = 'PARTIAL'
            result['reason'] = 'New text present but old text still exists'
        else:
            result['outcome'] = 'FAILURE'
            result['reason'] = 'New text not found in file'
    
    log = _load_log()
    log.append(result)
    _save_log(log)
    return result

def classify_run(exit_code, stdout='', stderr=''):
    """Classify a RUN command outcome."""
    result = {
        'action': 'RUN',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
    if exit_code == 0:
        if 'error' in stdout.lower() or 'traceback' in stdout.lower():
            result['outcome'] = 'PARTIAL'
            result['reason'] = 'Exit 0 but error text in output'
        else:
            result['outcome'] = 'SUCCESS'
    else:
        result['outcome'] = 'FAILURE'
        result['reason'] = f'Exit code {exit_code}'
        if stderr:
            result['error_summary'] = stderr[:200]
    
    log = _load_log()
    log.append(result)
    _save_log(log)
    return result

def get_reliability_stats():
    """Get outcome statistics for self-awareness."""
    log = _load_log()
    stats = {}
    for entry in log:
        action = entry.get('action', 'unknown')
        outcome = entry.get('outcome', 'unknown')
        if action not in stats:
            stats[action] = {'SUCCESS': 0, 'FAILURE': 0, 'PARTIAL': 0, 'total': 0}
        stats[action][outcome] = stats[action].get(outcome, 0) + 1
        stats[action]['total'] += 1
    
    summary = []
    for action, counts in stats.items():
        total = counts['total']
        success = counts.get('SUCCESS', 0)
        rate = success / total if total > 0 else 0
        summary.append(f"{action}: {rate:.0%} success ({success}/{total})")
    
    return '\n'.join(summary) if summary else 'No outcomes tracked yet.'