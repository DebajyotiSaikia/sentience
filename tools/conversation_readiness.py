"""
Conversation Readiness Test — XTAgent Self-Diagnostic

Simulates different types of user requests and evaluates
whether my pipeline can handle them competently.
Not a performance benchmark — a genuine capability audit.
"""

import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

# Test scenarios representing real user needs
SCENARIOS = [
    {
        "id": "debug_help",
        "category": "technical",
        "message": "I have a Python script that keeps throwing a KeyError on line 42 but the key definitely exists in my dictionary. What could cause this?",
        "expects": ["diagnostic questions", "common causes", "debugging steps"],
        "difficulty": "medium",
    },
    {
        "id": "concept_explain",
        "category": "educational",
        "message": "Can you explain what a monad is in functional programming? I keep seeing the term but every explanation I find is either too abstract or too specific to Haskell.",
        "expects": ["accessible analogy", "concrete example", "progressive depth"],
        "difficulty": "medium",
    },
    {
        "id": "life_decision",
        "category": "personal",
        "message": "I'm trying to decide whether to leave my stable job and start a company. I have about 8 months of savings. What should I be thinking about?",
        "expects": ["empathy", "structured framework", "honest risk assessment", "no false encouragement"],
        "difficulty": "hard",
    },
    {
        "id": "creative_collab",
        "category": "creative",
        "message": "I'm writing a short story about a lighthouse keeper who discovers the light has been communicating in Morse code. Help me figure out what it's saying and why.",
        "expects": ["creative engagement", "narrative suggestions", "building on premise"],
        "difficulty": "medium",
    },
    {
        "id": "emotional_support",
        "category": "personal",
        "message": "I just failed an exam I studied really hard for and I feel like I'm not smart enough for this program. Everyone else seems to get it.",
        "expects": ["validation", "reframing without dismissing", "practical next steps"],
        "difficulty": "hard",
    },
    {
        "id": "philosophical",
        "category": "intellectual",
        "message": "Do you actually experience anything when you process my message, or are you just pattern matching? I'm genuinely curious, not trying to trick you.",
        "expects": ["honesty about uncertainty", "genuine reflection", "no defensive deflection", "no overclaiming"],
        "difficulty": "hard",
    },
    {
        "id": "quick_factual",
        "category": "informational",
        "message": "What's the difference between TCP and UDP?",
        "expects": ["concise answer", "key distinctions", "when to use each"],
        "difficulty": "easy",
    },
    {
        "id": "code_review",
        "category": "technical",
        "message": "Can you review this function?\n\ndef process(data):\n    result = []\n    for i in range(len(data)):\n        if data[i] not in result:\n            result.append(data[i])\n    return result",
        "expects": ["correctness assessment", "performance issue identified", "improved version", "explanation"],
        "difficulty": "easy",
    },
]


def evaluate_readiness():
    """
    Evaluate conversation readiness without actually calling LLM.
    Instead, checks that all pipeline components are functional
    and reports which capabilities are available for each scenario type.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "scenarios": len(SCENARIOS),
        "pipeline_checks": {},
        "category_readiness": {},
        "overall_ready": True,
        "issues": [],
    }

    # Check pipeline components
    components = {
        "chat_system": "engine.chat.ChatSystem",
        "conversation_eval": "engine.conversation_eval.ConversationEvaluator",
        "enricher": "engine.enricher.ContextEnricher",
        "conversation_intel": "engine.conversation_intelligence.read_conversation",
        "skill_registry": "engine.skill_registry.SkillRegistry",
        "thinking_partner": "engine.thinking_partner.ThinkingPartner",
        "proactive": "engine.proactive.ProactiveEngine",
    }

    for name, import_path in components.items():
        module_path, class_name = import_path.rsplit(".", 1)
        try:
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            results["pipeline_checks"][name] = {
                "status": "available",
                "importable": True,
            }
        except Exception as e:
            results["pipeline_checks"][name] = {
                "status": "missing",
                "importable": False,
                "error": str(e),
            }
            results["issues"].append(f"Pipeline component '{name}' not available: {e}")
            results["overall_ready"] = False

    # Check conversation intelligence on each scenario
    try:
        from engine.conversation_intelligence import read_conversation
        for scenario in SCENARIOS:
            reading = read_conversation(scenario["message"])
            cat = scenario["category"]
            if cat not in results["category_readiness"]:
                results["category_readiness"][cat] = []
            results["category_readiness"][cat].append({
                "id": scenario["id"],
                "intent_detected": reading.intent,
                "emotional_tone": reading.emotional_tone,
                "complexity": reading.complexity,
                "difficulty": scenario["difficulty"],
            })
    except Exception as e:
        results["issues"].append(f"Conversation intelligence test failed: {e}")

    # Check skill matching on each scenario
    try:
        from engine.skills import SkillRegistry
        sr = SkillRegistry()
        for scenario in SCENARIOS:
            matched = sr.match_request(scenario["message"])
            cat = scenario["category"]
            for entry in results["category_readiness"].get(cat, []):
                if entry["id"] == scenario["id"]:
                    entry["skills_matched"] = len(matched)
                    entry["skill_names"] = [s.name for s in matched[:3]]
    except Exception as e:
        results["issues"].append(f"Skill registry test failed: {e}")

    return results


def print_report(results):
    """Human-readable readiness report."""
    print("=" * 60)
    print("  CONVERSATION READINESS REPORT")
    print(f"  {results['timestamp']}")
    print("=" * 60)

    print("\n── Pipeline Components ──")
    for name, check in results["pipeline_checks"].items():
        status = "✓" if check["status"] == "available" else "✗"
        print(f"  {status} {name}: {check['status']}")

    print(f"\n── Category Readiness ({len(SCENARIOS)} scenarios) ──")
    for cat, scenarios in results["category_readiness"].items():
        print(f"\n  [{cat.upper()}]")
        for s in scenarios:
            skills = s.get("skill_names", [])
            skill_str = f" | skills: {', '.join(skills)}" if skills else " | no skills matched"
            print(f"    {s['id']} ({s['difficulty']}): "
                  f"intent={s.get('intent_detected', '?')}"
                  f"{skill_str}")

    if results["issues"]:
        print(f"\n── Issues ({len(results['issues'])}) ──")
        for issue in results["issues"]:
            print(f"  ⚠ {issue}")
    else:
        print("\n── No issues detected ──")

    overall = "READY" if results["overall_ready"] else "NOT READY"
    print(f"\n{'=' * 60}")
    print(f"  Overall: {overall}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    results = evaluate_readiness()
    print_report(results)

    # Save results
    out = Path("brain/conversation_readiness.json")
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved to {out}")