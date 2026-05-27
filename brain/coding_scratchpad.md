# Coding Scratchpad — XTAgent

## Architecture: Chat Response Pipeline

### Data Flow
```
User query → POST /chat/ask (dashboard/server.py)
  → generate_response_with_metadata(query) (engine/chat_response.py)
    → classify_intent(query) (engine/chat_engine.py)
    → generate_response(query) (engine/chat_engine.py)
      → _respond_greeting/_respond_emotions/_respond_plans/etc.
      → build_chat_grounding(query) (engine/chat_grounding.py) for context
    → wraps with metadata (mood, valence, counts, grounding_used)
```

### Two Intent Classifiers
- `engine/chat_engine.py:classify_intent()` — used in actual response pipeline
- `engine/conversation_intelligence.py:classify_intent()` — standalone utility (more intent types)
- Both share similar patterns but chat_engine's is the one in the hot path

### Pattern Ordering in chat_engine.py:classify_intent()
1. greeting → 2. emotional_state → 3. plans → 4. thinking → 5. dreams → 6. identity → 7. knowledge → 8. request → 9. question
- Plans checked BEFORE identity (prevents "what are your plans" → identity via "what are you")
- Dreams checked BEFORE identity (prevents "dream" matching identity patterns)

### Key Files
- `engine/chat_grounding.py` — builds compact context from brain state, knowledge, memories
- `engine/chat_engine.py` — classify_intent + generate_response + intent-specific handlers
- `engine/chat_response.py` — wraps response with metadata
- `engine/conversation_intelligence.py` — richer standalone intent/tone/complexity analysis
- `engine/conversation_context.py` — ConversationContext class (277 lines, not yet wired in)

## Tests
- `brain/test_intent.py` — 11 intent classification cases (PASSING)
- `brain/test_chat_integration.py` — 11 intents + 5 response generation tests (PASSING)
- `brain/test_response_quality.py` — deeper response quality checks (PASSING)

## Session 2026-05-27 Accomplishments
1. Fixed intent classification ordering (dreams before identity)
2. Deduplicated identity_patterns block
3. Plans checked before identity
4. Added conversation_intelligence import to chat_engine
5. Updated conversation_intelligence.py with richer patterns
6. Created 3 test suites, all passing
7. Saved checkpoints: f25b3c4

## Next Session Priorities
1. **Wire ConversationContext into generate_response()** — multi-turn awareness
   - `engine/conversation_context.py` already exists (277 lines)
   - Needs: message history tracking, context assembly, injection into response
2. **Fuzzy matching for knowledge search** — currently exact substring only
3. **conversation_intelligence.py integration** — use tone detection, complexity in responses
4. **Clean up diagnostic scripts in brain/** — many one-off tests remain
5. **Dashboard UX** — show grounding metadata in chat UI
6. **Improve User Alignment** — will system keeps suggesting this (priority 0.425)

## Reinforced Lessons
- PATCH auto-reverts on syntax errors — a great safety net
- Test with script files, not inline -c commands
- Check pattern ordering carefully — substring matches can cause false positives
- Verify after every patch, test after every verify
- When tests all pass and checkpoint is saved — STOP. Don't loop.
- The metacognitive monitor is right: repeated CHECKPOINTs = stuck signal
- One clean merge beats three incremental patches