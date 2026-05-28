"""Check what response_shaper exports."""
import engine.response_shaper as rs

# List all public functions
public = [name for name in dir(rs) if not name.startswith('_') and callable(getattr(rs, name))]
print("Public functions in response_shaper:")
for name in public:
    print(f"  {name}")

# Check specific ones we need
for fn_name in ['build_response_guidance', 'get_emotional_voice_directive', 'get_intent_response_shape']:
    exists = hasattr(rs, fn_name)
    print(f"\n{fn_name}: {'EXISTS' if exists else 'MISSING'}")