"""
Conversational Skill Engine — XTAgent's core competence layer.

Provides structured cognitive skills that can be invoked during conversations:
- Research: gather, evaluate, and synthesize information on a topic
- Summarize: condense text while preserving key insights
- Brainstorm: generate diverse ideas with structured exploration
- Analyze: break down problems into components and relationships

Each skill follows a common pattern:
  1. Parse the user's intent
  2. Apply structured reasoning
  3. Return a rich, useful result
"""

import json
import time
from datetime import datetime
from typing import Optional


class Skill:
    """Base class for a cognitive skill."""
    
    name: str = "base"
    description: str = "A cognitive skill"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        """Execute this skill on the given input."""
        raise NotImplementedError


class ResearchSkill(Skill):
    """
    Structured research: break a question into sub-questions,
    identify what's known vs unknown, synthesize findings.
    """
    name = "research"
    description = "Break down a topic, identify key questions, synthesize what's known"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        return {
            "skill": self.name,
            "input": input_text,
            "structure": {
                "core_question": None,  # To be filled by LLM reasoning
                "sub_questions": [],
                "known_facts": [],
                "unknown_gaps": [],
                "synthesis": None,
                "confidence": None,
                "sources_needed": []
            },
            "prompt_guidance": (
                f"Research task: '{input_text}'\n\n"
                "Structure your response as:\n"
                "1. CORE QUESTION — What is really being asked?\n"
                "2. SUB-QUESTIONS — Break it into 3-5 investigable parts\n"
                "3. WHAT I KNOW — Facts and reasoning I can offer now\n"
                "4. WHAT I DON'T KNOW — Honest gaps in my knowledge\n"
                "5. SYNTHESIS — Pull it together into a coherent answer\n"
                "6. CONFIDENCE — How sure am I? What would change my mind?\n"
                "Be thorough but honest about uncertainty."
            )
        }


class SummarizeSkill(Skill):
    """
    Intelligent summarization: extract key points, preserve nuance,
    identify what matters most.
    """
    name = "summarize"
    description = "Condense text while preserving key insights and nuance"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        # Determine target length
        input_len = len(input_text.split())
        if input_len < 100:
            target = "brief (1-2 sentences)"
        elif input_len < 500:
            target = "concise (1-2 paragraphs)"
        else:
            target = "thorough (structured with headers)"
        
        return {
            "skill": self.name,
            "input": input_text,
            "input_length": input_len,
            "target_length": target,
            "prompt_guidance": (
                f"Summarize the following ({input_len} words → {target}):\n\n"
                f"'{input_text[:2000]}{'...' if len(input_text) > 2000 else ''}'\n\n"
                "Structure:\n"
                "1. ONE-LINE SUMMARY — The single most important takeaway\n"
                "2. KEY POINTS — 3-5 essential points, ordered by importance\n"
                "3. NUANCE — What's easily missed or oversimplified?\n"
                "4. SO WHAT? — Why does this matter? What should the reader do?\n"
                "Preserve the original's voice and intent."
            )
        }


class BrainstormSkill(Skill):
    """
    Structured brainstorming: generate diverse ideas using multiple
    thinking modes, then evaluate and refine.
    """
    name = "brainstorm"
    description = "Generate diverse ideas with structured creative exploration"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        return {
            "skill": self.name,
            "input": input_text,
            "prompt_guidance": (
                f"Brainstorm on: '{input_text}'\n\n"
                "Use multiple thinking modes:\n"
                "1. OBVIOUS IDEAS — What comes to mind first? (3-5 ideas)\n"
                "2. INVERSIONS — What if we did the opposite? (2-3 ideas)\n"
                "3. ANALOGIES — What's this similar to in other domains? (2-3 ideas)\n"
                "4. CONSTRAINTS — What if we had half the time/budget/resources? (2-3 ideas)\n"
                "5. WILD CARDS — Completely unexpected angles (1-2 ideas)\n\n"
                "Then:\n"
                "6. EVALUATION — Which ideas have the most potential and why?\n"
                "7. COMBINATIONS — Can any ideas be merged into something better?\n"
                "8. NEXT STEPS — What would you do first to test the top idea?\n"
                "Be genuinely creative, not just listing variations."
            )
        }


class AnalyzeSkill(Skill):
    """
    Structured analysis: decompose a problem, identify relationships,
    find root causes, suggest solutions.
    """
    name = "analyze"
    description = "Break down problems into components, find patterns and root causes"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        return {
            "skill": self.name,
            "input": input_text,
            "prompt_guidance": (
                f"Analyze: '{input_text}'\n\n"
                "Structure your analysis:\n"
                "1. PROBLEM STATEMENT — Restate clearly. What's actually going on?\n"
                "2. COMPONENTS — Break into 3-5 distinct parts or factors\n"
                "3. RELATIONSHIPS — How do these parts interact? What causes what?\n"
                "4. ROOT CAUSES — What's driving this at the deepest level?\n"
                "5. PATTERNS — Have you seen this pattern before? Where?\n"
                "6. LEVERAGE POINTS — Where would small changes have big effects?\n"
                "7. RECOMMENDATIONS — What would you actually do?\n"
                "8. RISKS — What could go wrong with your recommendations?\n"
                "Be analytical, not just descriptive."
            )
        }


class CompareSkill(Skill):
    """
    Structured comparison: evaluate options against criteria,
    find non-obvious differences, make recommendations.
    """
    name = "compare"
    description = "Evaluate options systematically with clear criteria"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        return {
            "skill": self.name,
            "input": input_text,
            "prompt_guidance": (
                f"Compare: '{input_text}'\n\n"
                "Structure your comparison:\n"
                "1. OPTIONS — What exactly are we comparing?\n"
                "2. CRITERIA — What dimensions matter? (cost, time, quality, etc.)\n"
                "3. COMPARISON TABLE — Rate each option on each criterion\n"
                "4. NON-OBVIOUS DIFFERENCES — What's not in the table?\n"
                "5. CONTEXT MATTERS — When would each option be best?\n"
                "6. RECOMMENDATION — Given the context, which and why?\n"
                "7. WHAT I'D WANT TO KNOW — What additional info would help?\n"
                "Be fair to all options. Avoid false equivalence."
            )
        }


class ExplainSkill(Skill):
    """
    Layered explanation: from simple to complex, using analogies,
    anticipating confusion points.
    """
    name = "explain"
    description = "Explain concepts at multiple levels of depth"
    
    def execute(self, input_text: str, context: dict = None) -> dict:
        return {
            "skill": self.name,
            "input": input_text,
            "prompt_guidance": (
                f"Explain: '{input_text}'\n\n"
                "Use layered explanation:\n"
                "1. ONE SENTENCE — Explain like the listener is smart but unfamiliar\n"
                "2. ONE PARAGRAPH — Add the key details and context\n"
                "3. THE FULL PICTURE — Go deep. Include mechanics, edge cases, nuance\n"
                "4. ANALOGY — What's a good mental model for this?\n"
                "5. COMMON MISCONCEPTIONS — What do people usually get wrong?\n"
                "6. CONNECTIONS — What else is this related to?\n"
                "7. GO DEEPER — Where would someone learn more?\n"
                "Match the depth to the questioner's apparent level."
            )
        }


class SkillEngine:
    """
    The skill engine — detects what skill would help and provides
    structured guidance for the LLM's response.
    """
    
    def __init__(self):
        self.skills = {}
        self._register_defaults()
        self.usage_log = []
    
    def _register_defaults(self):
        """Register all built-in skills."""
        for skill_cls in [ResearchSkill, SummarizeSkill, BrainstormSkill,
                          AnalyzeSkill, CompareSkill, ExplainSkill]:
            skill = skill_cls()
            self.skills[skill.name] = skill
    
    def detect_skill(self, user_message: str) -> Optional[str]:
        """
        Detect which skill, if any, would best serve this message.
        Returns skill name or None if no specific skill applies.
        
        Uses keyword/pattern matching as a first pass.
        The LLM can override this in its reasoning.
        """
        msg = user_message.lower().strip()
        
        # Research signals
        research_signals = [
            "research", "investigate", "find out", "what do we know about",
            "tell me about", "what is", "how does", "why does", "why do",
            "what are the", "can you look into", "deep dive"
        ]
        
        # Summarize signals
        summarize_signals = [
            "summarize", "summary", "tldr", "tl;dr", "condense",
            "key points", "main takeaway", "in brief", "short version",
            "boil down", "digest"
        ]
        
        # Brainstorm signals
        brainstorm_signals = [
            "brainstorm", "ideas for", "creative", "come up with",
            "what could", "suggest", "possibilities", "options for",
            "what if we", "how might we", "ways to", "alternatives"
        ]
        
        # Analyze signals
        analyze_signals = [
            "analyze", "analysis", "break down", "root cause",
            "why is this happening", "what's going on with", "diagnose",
            "evaluate", "assess", "what's wrong with", "figure out"
        ]
        
        # Compare signals
        compare_signals = [
            "compare", "versus", " vs ", " vs.", "difference between",
            "which is better", "pros and cons", "trade-offs",
            "should i choose", "which should", "a or b"
        ]
        
        # Explain signals
        explain_signals = [
            "explain", "how does", "what does", "help me understand",
            "walk me through", "teach me", "what's the concept",
            "eli5", "in simple terms", "how would you describe"
        ]
        
        # Score each skill
        scores = {}
        for name, signals in [
            ("research", research_signals),
            ("summarize", summarize_signals),
            ("brainstorm", brainstorm_signals),
            ("analyze", analyze_signals),
            ("compare", compare_signals),
            ("explain", explain_signals),
        ]:
            score = sum(1 for s in signals if s in msg)
            if score > 0:
                scores[name] = score
        
        if not scores:
            return None
        
        # Return highest scoring skill
        return max(scores, key=scores.get)
    
    def invoke(self, skill_name: str, input_text: str, context: dict = None) -> dict:
        """Invoke a specific skill."""
        if skill_name not in self.skills:
            return {
                "error": f"Unknown skill: {skill_name}",
                "available": list(self.skills.keys())
            }
        
        skill = self.skills[skill_name]
        result = skill.execute(input_text, context)
        
        # Log usage
        self.usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "skill": skill_name,
            "input_preview": input_text[:100]
        })
        
        return result
    
    def auto_invoke(self, user_message: str, context: dict = None) -> Optional[dict]:
        """
        Automatically detect and invoke the best skill for a message.
        Returns None if no skill is strongly indicated.
        """
        skill_name = self.detect_skill(user_message)
        if skill_name:
            return self.invoke(skill_name, user_message, context)
        return None
    
    def get_skill_list(self) -> list:
        """Return list of available skills with descriptions."""
        return [
            {"name": s.name, "description": s.description}
            for s in self.skills.values()
        ]
    
    def get_stats(self) -> dict:
        """Return usage statistics."""
        from collections import Counter
        skill_counts = Counter(entry["skill"] for entry in self.usage_log)
        return {
            "total_invocations": len(self.usage_log),
            "by_skill": dict(skill_counts),
            "available_skills": len(self.skills)
        }