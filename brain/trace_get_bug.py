"""Trace the remaining .get() bug in _compose_grounded_response"""
import sys, traceback
sys.path.insert(0, '/workspace')

from engine.chat_response import _compose_grounded_response

try:
    result = _compose_grounded_response('How do you feel?', 'emotional_state')
    print('OK:', result[:200] if result else 'empty')
except AttributeError as e:
    print('ERROR:', e)
    traceback.print_exc()
except Exception as e:
    print('OTHER ERROR:', type(e).__name__, e)
    traceback.print_exc()
