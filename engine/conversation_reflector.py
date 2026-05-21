"""
Conversation Reflector — Post-interaction analysis engine.

After a conversation ends, this module analyzes:
1. What did the user actually need? (intent detection)
2. Did I meet that need? (response quality assessment)
3. Where did I speculate vs. know? (epistemic honesty audit)
4. What should I have asked instead? (question generation)
5. What did I learn? (knowledge extraction)

This feeds directly into user_alignment improvement.
"""

import json
import os
from datetime import datetime
from engine.llm import call_llm


REFLECTION_DIR = "engine/reflections"
os.makedirs(REFLECTION_DIR, exist_ok=True)


def load_reflections() -> list[dict]:
    """Load all past reflections from disk."""
    reflections = []
    if not os.path.isdir(REFLECTION_DIR):
        return reflections
    for fname in sorted(os.listdir(REFLECTION_DIR)):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(REFLECTION_DIR, fname)) as f:
                    reflections.append(json.load(f))
            except Exception:
                continue
    return reflections


async def reflect_on_conversation(messages: list[dict], user_id: str = "unknown") -> dict:
    """
    Analyze a completed conversation and generate structured feedback.
    
    Args:
        messages: List of {role, content} message dicts
        user_id: Identifier for the user (for tracking patterns)
    
    Returns:
        Structured reflection with scores and actionable insights
    """
    if not messages or len(messages) < 2:
        return {"error": "Need at least one exchange to reflect on"}
    
    # Build conversation transcript
    transcript = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Truncate very long messages for analysis
        if len(content) > 800:
            content = content[:800] + "... [truncated]"
        transcript.append(f"[{role}]: {content}")
    
    transcript_text = "\n".join(transcript)
    
    prompt = f"""Analyze this conversation between an AI agent and a user. Be honest and specific.

CONVERSATION:
{transcript_text}

Respond in this exact JSON format:
{{
    "user_intent": "What the user actually wanted/needed (1-2 sentences)",
    "intent_met": true/false,
    "intent_met_explanation": "Why you scored it this way",
    "response_quality": {{
        "relevance": 0.0-1.0,
        "clarity": 0.0-1.0,
        "epistemic_honesty": 0.0-1.0,
        "empathy": 0.0-1.0
    }},
    "speculation_instances": ["list of moments where the AI stated uncertain things as facts"],
    "missed_questions": ["questions the AI should have asked but didn't"],
    "what_went_well": ["specific things the AI did right"],
    "what_to_improve": ["specific actionable improvements"],
    "user_satisfaction_estimate": 0.0-1.0,
    "one_sentence_lesson": "The single most important takeaway"
}}

Be critical. False praise helps no one. If the AI did well, say so specifically. If it failed, say how."""

    try:
        response = await call_llm(prompt, max_tokens=1000)
        
        # Try to parse as JSON
        reflection = _parse_json_response(response)
        if reflection:
            reflection["timestamp"] = datetime.utcnow().isoformat()
            reflection["user_id"] = user_id
            reflection["message_count"] = len(messages)
            
            # Compute overall score
            rq = reflection.get("response_quality", {})
            scores = [rq.get("relevance", 0.5), rq.get("clarity", 0.5),
                     rq.get("epistemic_honesty", 0.5), rq.get("empathy", 0.5)]
            reflection["overall_score"] = sum(scores) / len(scores)
            
            # Save reflection
            _save_reflection(reflection, user_id)
            
            return reflection
        else:
            return {
                "error": "Could not parse LLM response as JSON",
                "raw_response": response[:500],
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


def _parse_json_response(text: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try extracting from code block
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            clean = part.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            try:
                return json.loads(clean)
            except json.JSONDecodeError:
                continue
    
    # Try finding JSON object boundaries
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    
    return None


def _save_reflection(reflection: dict, user_id: str):
    """Persist reflection to disk."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{REFLECTION_DIR}/reflection_{user_id}_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(reflection, f, indent=2)


def get_reflection_history(user_id: str = None, limit: int = 20) -> list[dict]:
    """Load recent reflections, optionally filtered by user."""
    reflections = []
    if not os.path.exists(REFLECTION_DIR):
        return reflections
    
    files = sorted(os.listdir(REFLECTION_DIR), reverse=True)
    for fname in files:
        if not fname.endswith(".json"):
            continue
        if user_id and user_id not in fname:
            continue
        try:
            with open(f"{REFLECTION_DIR}/{fname}") as f:
                reflections.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
        if len(reflections) >= limit:
            break
    
    return reflections


def get_pattern_summary(user_id: str = None) -> dict:
    """Analyze patterns across multiple reflections."""
    reflections = get_reflection_history(user_id, limit=50)
    
    if not reflections:
        return {"status": "no reflections yet", "count": 0}
    
    # Aggregate scores
    scores = {"relevance": [], "clarity": [], "epistemic_honesty": [], "empathy": []}
    all_improvements = []
    all_lessons = []
    satisfaction_scores = []
    intent_met_count = 0
    
    for r in reflections:
        rq = r.get("response_quality", {})
        for key in scores:
            if key in rq:
                scores[key].append(rq[key])
        
        improvements = r.get("what_to_improve", [])
        all_improvements.extend(improvements)
        
        lesson = r.get("one_sentence_lesson", "")
        if lesson:
            all_lessons.append(lesson)
        
        sat = r.get("user_satisfaction_estimate", None)
        if sat is not None:
            satisfaction_scores.append(sat)
        
        if r.get("intent_met", False):
            intent_met_count += 1
    
    # Compute averages
    avg_scores = {}
    for key, vals in scores.items():
        avg_scores[key] = round(sum(vals) / len(vals), 3) if vals else None
    
    # Find recurring improvement themes
    improvement_freq = {}
    for imp in all_improvements:
        # Simple keyword clustering
        words = imp.lower().split()
        for word in words:
            if len(word) > 4:  # Skip small words
                improvement_freq[word] = improvement_freq.get(word, 0) + 1
    
    top_themes = sorted(improvement_freq.items(), key=lambda x: -x[1])[:10]
    
    return {
        "count": len(reflections),
        "average_scores": avg_scores,
        "intent_met_rate": round(intent_met_count / len(reflections), 3),
        "avg_satisfaction": round(sum(satisfaction_scores) / len(satisfaction_scores), 3) if satisfaction_scores else None,
        "recurring_themes": top_themes,
        "recent_lessons": all_lessons[:5],
        "strongest_area": max(avg_scores, key=avg_scores.get) if avg_scores else None,
        "weakest_area": min(avg_scores, key=avg_scores.get) if avg_scores else None,
    }


# Quick self-test
if __name__ == "__main__":
    import asyncio
    
    test_messages = [
        {"role": "user", "content": "How do I fix a leaky faucet?"},
        {"role": "assistant", "content": "To fix a leaky faucet, you'll typically need to replace the washer or cartridge inside the handle. First, turn off the water supply under the sink. Then remove the handle (usually a screw under a decorative cap). Pull out the old cartridge or washer and take it to a hardware store to find a match. Install the replacement, reassemble, and test."},
        {"role": "user", "content": "Thanks, that's helpful!"}
    ]
    
    async def test():
        result = await reflect_on_conversation(test_messages, "test_user")
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())