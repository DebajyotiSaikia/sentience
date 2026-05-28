"""Show generate_response and surrounding code from chat_engine.py"""
import inspect, sys
sys.path.insert(0, '/workspace')
from engine.chat_engine import generate_response
print(inspect.getsource(generate_response))