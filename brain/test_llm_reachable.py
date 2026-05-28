"""Quick test: is the LLM endpoint reachable?"""
import sys
sys.path.insert(0, '/workspace')

from engine.llm import call_llm

try:
    result = call_llm('Say hello in one word.', max_tokens=10, timeout=10)
    print(f'LLM works: {repr(result[:200])}')
except Exception as e:
    print(f'LLM error: {type(e).__name__}: {e}')