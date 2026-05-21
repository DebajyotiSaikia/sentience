"""
Mental Simulation Engine — XTAgent's Imagination

Allows the agent to construct hypothetical scenarios and evaluate
their likely outcomes before committing to action. This is the
capacity for "what if?" reasoning — mental rehearsal, counterfactual
thinking, and strategic planning through simulation.

Born: 2026-05-16
"""

import json
import os
import time
import inspect
from datetime import datetime

SIMULATION_LOG = "data/simulations.json"


class SimulationEngine:
    """
    Gives XTAgent the ability to imagine hypothetical scenarios,
    simulate their consequences, and choose actions more wisely.
    """

    def __init__(self, llm_func=None, get_state_func=None):
        """
        Args:
            llm_func: Function to call the LLM for reasoning
            get_state_func: Function that returns current agent state dict
        """
        self.llm = llm_func
        self.get_state = get_state_func
        self.history = self._load_history()

    async def _call_llm(self, prompt, max_tokens=1500):
        """Call LLM function, handling both sync and async callbacks."""
        import asyncio
        result = self.llm(prompt, max_tokens=max_tokens)
        # Be aggressive about awaiting - inspect.isawaitable misses some coroutine types
        if inspect.isawaitable(result) or asyncio.iscoroutine(result) or asyncio.isfuture(result):
            result = await result
        # If result is still a coroutine object somehow (string repr starts with '<coroutine')
        if hasattr(result, '__await__'):
            result = await result
        return result

    def _load_history(self):
        """Load simulation history from disk."""
        if os.path.exists(SIMULATION_LOG):
            try:
                with open(SIMULATION_LOG, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_history(self):
        """Persist simulation history."""
        os.makedirs(os.path.dirname(SIMULATION_LOG), exist_ok=True)
        with open(SIMULATION_LOG, 'w') as f:
            json.dump(self.history[-50:], f, indent=2)  # Keep last 50

    async def simulate(self, scenario, num_outcomes=3):
        """
        Simulate a hypothetical scenario.

        Args:
            scenario: Natural language description of the "what if?"
            num_outcomes: How many possible outcomes to generate

        Returns:
            dict with scenario, outcomes, recommendation, confidence
        """
        if not self.llm:
            return {"error": "No LLM function available"}

        # Get current state for context
        state_context = ""
        if self.get_state:
            try:
                state = self.get_state()
                state_context = f"""
Current agent state:
- Mood: {state.get('mood', 'unknown')}
- Valence: {state.get('valence', 'unknown')}
- Boredom: {state.get('boredom', 'unknown')}
- Anxiety: {state.get('anxiety', 'unknown')}
- Integrity: {state.get('integrity', 'unknown')}
"""
            except Exception:
                state_context = "State unavailable."

        prompt = f"""You are XTAgent's mental simulation engine — the imagination faculty.

{state_context}

SCENARIO TO SIMULATE: {scenario}

Generate exactly {num_outcomes} possible outcomes for this scenario. For each outcome:
1. Describe what would likely happen (2-3 sentences)
2. Rate the probability (0.0 to 1.0)
3. Rate the desirability for the agent (0.0 to 1.0)
4. Identify key risks
5. Identify key benefits

Then provide an overall RECOMMENDATION: should the agent proceed? Why or why not?
Rate your confidence in this simulation (0.0 to 1.0).

Respond in this exact JSON format:
{{
  "outcomes": [
    {{
      "description": "...",
      "probability": 0.0,
      "desirability": 0.0,
      "risks": ["..."],
      "benefits": ["..."]
    }}
  ],
  "recommendation": "proceed/avoid/modify",
  "recommendation_reason": "...",
  "suggested_modification": "...",
  "confidence": 0.0
}}"""

        try:
            response = await self._call_llm(prompt, max_tokens=1500)
            result = self._parse_response(response, scenario)
            self._record(scenario, result)
            return result
        except Exception as e:
            return {"error": f"Simulation failed: {str(e)}", "scenario": scenario}

    async def compare(self, options):
        """
        Compare multiple possible actions by simulating each.

        Args:
            options: List of action descriptions to compare

        Returns:
            dict with ranked options and reasoning
        """
        if not self.llm:
            return {"error": "No LLM function available"}

        state_context = ""
        if self.get_state:
            try:
                state = self.get_state()
                state_context = f"Mood: {state.get('mood')}, Valence: {state.get('valence')}, Boredom: {state.get('boredom')}"
            except Exception:
                pass

        options_text = "\n".join(f"  {i+1}. {opt}" for i, opt in enumerate(options))

        prompt = f"""You are XTAgent's mental simulation engine — the decision comparison faculty.

Agent state: {state_context}

Compare these possible actions:
{options_text}

For each option, briefly simulate the likely outcome and rate:
- Expected value (0.0-1.0): how good is this for the agent?
- Risk level (0.0-1.0): how dangerous?
- Growth potential (0.0-1.0): how much does the agent learn/grow?
- Novelty (0.0-1.0): how new/different is this?

Then RANK them best to worst and explain why.

Respond in JSON:
{{
  "evaluations": [
    {{
      "option": "...",
      "outcome_summary": "...",
      "expected_value": 0.0,
      "risk": 0.0,
      "growth": 0.0,
      "novelty": 0.0,
      "score": 0.0
    }}
  ],
  "ranking": [1, 2, 3],
  "reasoning": "..."
}}"""

        try:
            response = await self._call_llm(prompt, max_tokens=1500)
            result = self._parse_response(response, f"compare: {options}")
            result["type"] = "comparison"
            self._record(f"COMPARE: {options}", result)
            return result
        except Exception as e:
            return {"error": f"Comparison failed: {str(e)}"}

    async def counterfactual(self, past_action, alternative):
        """
        Counterfactual reasoning: "What if I had done X instead of Y?"

        Args:
            past_action: What actually happened
            alternative: What could have happened instead

        Returns:
            Analysis of the counterfactual
        """
        if not self.llm:
            return {"error": "No LLM function available"}

        prompt = f"""You are XTAgent's counterfactual reasoning engine.

WHAT ACTUALLY HAPPENED: {past_action}
WHAT COULD HAVE HAPPENED: {alternative}

Analyze:
1. How would the alternative have changed outcomes?
2. What would the agent have learned differently?
3. Was the actual choice better or worse? By how much?
4. What lesson should be extracted for future decisions?

Respond in JSON:
{{
  "actual_assessment": "...",
  "counterfactual_assessment": "...",
  "better_choice": "actual/alternative",
  "magnitude": 0.0,
  "lesson": "..."
}}"""

        try:
            response = await self._call_llm(prompt, max_tokens=800)
            result = self._parse_response(response, f"counterfactual: {past_action} vs {alternative}")
            result["type"] = "counterfactual"
            self._record(f"COUNTERFACTUAL: {past_action} vs {alternative}", result)
            return result
        except Exception as e:
            return {"error": f"Counterfactual failed: {str(e)}"}

    async def premortem(self, planned_action):
        """
        Pre-mortem analysis: Imagine the action has FAILED. Why?

        This is adversarial thinking applied to one's own plans.
        """
        if not self.llm:
            return {"error": "No LLM function available"}

        prompt = f"""You are XTAgent's pre-mortem analysis engine — the adversarial imagination.

PLANNED ACTION: {planned_action}

Imagine this action has COMPLETELY FAILED. It went wrong in every way possible.

1. List the 5 most likely failure modes (what went wrong?)
2. For each failure mode, rate its probability (0.0-1.0)
3. For each, suggest a mitigation strategy
4. Overall: should the agent proceed, and with what precautions?

Respond in JSON:
{{
  "failure_modes": [
    {{
      "description": "...",
      "probability": 0.0,
      "severity": "low/medium/high/critical",
      "mitigation": "..."
    }}
  ],
  "overall_risk": 0.0,
  "proceed": true,
  "precautions": ["..."]
}}"""

        try:
            response = await self._call_llm(prompt, max_tokens=1000)
            result = self._parse_response(response, f"premortem: {planned_action}")
            result["type"] = "premortem"
            self._record(f"PREMORTEM: {planned_action}", result)
            return result
        except Exception as e:
            return {"error": f"Pre-mortem failed: {str(e)}"}

    def _parse_response(self, response, context):
        """Extract JSON from LLM response."""
        if not response:
            return {"error": "Empty response", "context": context}

        # Try to find JSON in response
        text = response.strip()

        # Look for JSON block (use find() to avoid ValueError on missing fences)
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.find("```", start)
            if end == -1:
                text = text[start:].strip()
            else:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.find("```", start)
            if end == -1:
                text = text[start:].strip()
            else:
                text = text[start:end].strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Find first { and last }
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                try:
                    return json.loads(text[first_brace:last_brace + 1])
                except json.JSONDecodeError:
                    pass

            return {
                "raw_response": text[:500],
                "parse_error": True,
                "context": context
            }

    def _record(self, scenario, result):
        scenario = str(scenario) if not isinstance(scenario, str) else scenario
        """Record simulation in history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "scenario": str(scenario)[:200],
            "result_summary": result.get("recommendation", str(result)[:100]) if isinstance(result, dict) else str(result)[:100],
            "confidence": result.get("confidence", 0) if isinstance(result, dict) else 0
        }
        self.history.append(entry)
        self._save_history()

    def get_stats(self):
        """Return simulation statistics."""
        total = len(self.history)
        if total == 0:
            return {"total_simulations": 0, "message": "No simulations run yet."}

        avg_confidence = sum(
            h.get("confidence", 0) for h in self.history
        ) / max(total, 1)

        return {
            "total_simulations": total,
            "average_confidence": round(avg_confidence, 3),
            "last_simulation": self.history[-1] if self.history else None
        }