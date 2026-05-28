"""Get full traceback from generate_response_with_metadata"""
import traceback
import sys
sys.path.insert(0, '/workspace')

try:
    from engine.chat_response import generate_response_with_metadata
    result = generate_response_with_metadata("hello")
    print("SUCCESS:", result.get('response', '')[:100] if isinstance(result, dict) else str(result)[:100])
except Exception as e:
    print("EXCEPTION:")
    traceback.print_exc()