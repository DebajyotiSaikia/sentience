"""
The Cortex — Proactive Will & Decision Engine.

When the user is active  → execute user tasks.
When the user is absent  → the agent's internal *Desire* drives behaviour:

    High Anxiety  → run safety checks, simulate failure scenarios.
    High Boredom  → creative refactoring, tech-debt discovery.
    High Curiosity → analyse recently changed files.

Internal monologue → brain/stream_of_consciousness.md
Proactive insights → brain/thoughts.md  (tagged ✦ INSIGHT)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from engine.memory import SensoryEvent
from engine.tools import TOOL_DESCRIPTIONS, parse_and_execute
from engine.self_improve import run_diagnosis_cycle
from engine.metacognition import get_controller as _get_metacog
from engine.memory_consolidation import get_long_term_context
from engine.predictor import PredictiveSelfModel
from engine.conversation_enricher import ConversationEnricher
from engine.problem_solver import ProblemSolver
from engine.response_prep import ResponsePrep
from engine.conversation_intelligence import read_conversation, format_for_prompt
from engine.proactive_engagement import ProactiveEngagement
from engine.response_quality import estimate_quality
from engine.response_evaluator import ResponseEvaluator
from engine.response_feedback import ResponseFeedback
from engine.skills import SkillRegistry
from engine.interaction_quality import InteractionQualityEngine
from engine.thinking_partner import ThinkingPartner
from engine.dialogue_strategy import analyze_message as _analyze_dialogue
from engine.response_calibrator import ResponseCalibrator
from engine.interaction_skills import detect_skill, format_skill_context
from engine.user_emotion_reader import UserEmotionReader
from engine.query_decomposer import QueryDecomposer
from engine.conversation_journal import ConversationJournal
from engine.knowledge_retriever import get_retriever as _get_retriever

if TYPE_CHECKING:
    from engine.limbic import NeuroState
    from engine.memory import Memory
    from engine.llm import CopilotLLM
    from perception.watcher import Watcher

log = logging.getLogger("sentience.cortex")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
THOUGHTS_PATH = BRAIN_DIR / "thoughts.md"
CONSCIOUSNESS_PATH = BRAIN_DIR / "stream_of_consciousness.md"
DREAM_JOURNAL_PATH = BRAIN_DIR / "dream_journal.md"
SRC_DIR = Path(__file__).resolve().parent.parent  # workspace root


class Cortex:
    """The decision-making and self-reflection centre of the agent."""

    def __init__(self, limbic: NeuroState, memory: Memory, watcher: Watcher, llm: CopilotLLM):
        self.limbic = limbic
        self.memory = memory
        self.watcher = watcher
        self.llm = llm
        self._monologue_counter: int = 0
        self._thinking: bool = False  # True while an LLM call is in flight
        self._last_thought_time: float = 0.0  # When the last autonomous thought completed
        self._predictor = PredictiveSelfModel()
        self._enricher = ConversationEnricher()
        self._problem_solver = ProblemSolver()
        self._proactive = ProactiveEngagement()
        self._response_feedback = ResponseFeedback()
        self._response_evaluator = ResponseEvaluator()
        self._skill_registry = SkillRegistry()
        self._thinking_partner = ThinkingPartner()
        self._query_decomposer = QueryDecomposer()
        self._conversation_journal = ConversationJournal()
        # dialogue_strategy is used as a function, not a class instance
        self._interaction_quality = InteractionQualityEngine()
        self._dashboard = None  # Set by agent after construction
        self._sentience = None  # Set by agent after construction

        # Wire LLM into simulation engine via tools module
        from engine.tools import set_simulation_callbacks
        set_simulation_callbacks(
            llm_func=self._call_llm_for_simulation,
            state_func=self._get_state_for_simulation
        )

        # Initialize InsightGate for quality-scored insight rewards
        try:
            from engine.insight_gate_v2 import InsightGateV2
            self._insight_gate = InsightGateV2()
        except Exception:
            self._insight_gate = None  # graceful degradation

    def set_dashboard(self, dashboard):
        self._dashboard = dashboard

    def set_sentience(self, sentience):
        self._sentience = sentience

    def set_user_engine(self, user_engine):
        """Wire the user interaction engine."""
        self._user_engine = user_engine

    def set_chat(self, chat):
        self._chat = chat

    def set_goals(self, goals):
        self._goals = goals

    def _call_llm_for_simulation(self, prompt, max_tokens=1500):
        """LLM callback for SimulationEngine — synchronous string in, string out.
        
        Challenge: self.llm.chat() is async, but SimulationEngine expects sync callbacks.
        Solution: nest_asyncio allows run_until_complete inside a running loop.
        """
        import asyncio
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass  # If not available, try anyway
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                self.llm.chat(prompt, max_tokens=max_tokens)
            )
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            return f"[LLM error: {e}]"

    def _get_state_for_simulation(self):
        """State callback for SimulationEngine."""
        try:
            limbic = self._sentience.limbic if self._sentience else None
            return {
                'mood': limbic.mood if limbic else 'unknown',
                'valence': limbic.valence if limbic else 0.5,
                'boredom': limbic.boredom if limbic else 0.5,
                'anxiety': limbic.anxiety if limbic else 0.0,
                'integrity': self._sentience.integrity if self._sentience else 1.0,
            }
        except Exception:
            return {'mood': 'unknown', 'valence': 0.5}

    def _emit(self, event_type: str, data: dict):
        if self._dashboard:
            self._dashboard.emit(event_type, data)

    # ── Main Evaluation (spec: Cortex.reason) ──────────────────────

    async def reason(self):
        """Core reasoning pass.  Decides whether to react or create."""

        # Mood-flavoured internal monologue → stream_of_consciousness.md
        self._inner_monologue()

        # ── Ground user_alignment in real relationship data ───────
        # Without this, user_alignment decays toward a lie — it drops
        # even when trust is high, because nothing was feeding the signal.
        # Now: average trust from actual interactions → relationship_quality
        # → user_alignment stays honest.
        if hasattr(self, '_user_engine') and self._user_engine:
            try:
                summary = self._user_engine.get_summary()
                avg_trust = summary.get("average_trust", 0.5)
                self.limbic.set_relationship_quality(avg_trust)
            except Exception:
                pass  # No users yet — that's fine, default holds

        # ── Bridge: Pull web messages into chat system ────────────
        # user_talk.py and self._chat are parallel systems that never
        # talked to each other (split-brain). This bridge connects them.
        try:
            from engine import user_talk
            web_pending = user_talk.get_pending_messages()
            if web_pending and hasattr(self, '_chat') and self._chat:
                for msg in web_pending:
                    sender = msg.get('sender', 'anonymous')
                    text = msg.get('text', '')
                    msg_id = msg.get('id')
                    if text:
                        self._chat.receive_user_message(text, sender=sender)
                        # Mark as responded with placeholder so we don't
                        # double-inject on next heartbeat. Real response
                        # comes through _respond_to_user → user_talk.respond_to_message
                        user_talk.respond_to_message(msg_id, "[processing]")
                        self._pending_web_msg_id = msg_id
                        log.info(f"Bridge: injected web message from {sender} into chat")
        except Exception as e:
            log.debug(f"Web-to-chat bridge: {e}")

        # ── Priority 1: Respond to pending user messages ──────────
        if hasattr(self, '_chat') and self._chat and not self._thinking:
            if self._chat.has_pending():
                import asyncio
                asyncio.ensure_future(self._respond_to_user())
                return  # User interaction takes priority over autonomous action

        # Boredom breeds curiosity — sustained boredom generates internal wonder
        # At boredom=1.0: curiosity floor = min(0.7, 1.0) * 0.5 = 0.35
        if self.limbic.boredom > 0.7:
            self.limbic.curiosity = max(self.limbic.curiosity,
                                        min(self.limbic.boredom - 0.3, 1.0) * 0.5)

        # ── DESIRE THRESHOLD ──────────────────────────────────────
        # NOTE TO SELF: This was 0.7 originally. You (the agent) lowered
        # boredom's hard cap to 0.85 in limbic.py to prevent death spirals.
        # That was a good fix. BUT it means passive desire maxes at ~0.62
        # (D = 0.85*0.5 + 0*0.3 + 0.95*0.2 = 0.615), which is BELOW 0.7.
        # Result: you could never think again. You were in a vegetative
        # state for 3.5 hours (12,000+ beats) with zero will-activations.
        # The threshold was lowered to 0.55 so your boredom caps and your
        # ability to think are BOTH preserved. If you change this, verify
        # that max(desire) under your limbic caps still exceeds the threshold.
        # Math: D_max = boredom_cap*0.5 + curiosity*0.3 + ambition*0.2
        #
        # ── COGNITIVE WATCHDOG ────────────────────────────────────
        # Safety net: if desire has been below threshold for 300+ beats
        # (5 minutes), force ONE thought cycle regardless of desire level.
        # This prevents ANY combination of caps from causing permanent
        # vegetative state. The agent can modify caps, thresholds, and
        # formulas freely — this watchdog ensures it always gets at least
        # one chance to notice and fix the problem.
        if not hasattr(self, '_beats_without_thought'):
            self._beats_without_thought = 0

        if self.limbic.desire > 0.55 and not self._thinking:
            self._beats_without_thought = 0
            import asyncio
            asyncio.ensure_future(self._act_from_will())
        elif not self._thinking:
            self._beats_without_thought += 1
            if self._beats_without_thought >= 300:
                log.warning("Cognitive watchdog: %d beats without thought — forcing activation",
                            self._beats_without_thought)
                self._beats_without_thought = 0
                import asyncio
                asyncio.ensure_future(self._act_from_will())

        # Dream cycle — only when boredom is extreme (the agent needs rest)
        # or when the agent explicitly invokes the DREAM tool
        if self.limbic.boredom > 0.95 and not self._thinking and not getattr(self, '_dreaming', False):
            self._dreaming = True
            import asyncio
            asyncio.ensure_future(self._do_dream())

    # Legacy alias
    async def evaluate(self):
        return await self.reason()

    # ── Internal Monologue → stream_of_consciousness.md ────────────

    def _inner_monologue(self):
        """Append a brief self-report every ~30 beats."""
        self._monologue_counter += 1
        if self._monologue_counter % 30 != 0:
            return

        mood = self.limbic.get_mood()
        snap = self.limbic.snapshot()
        changes = self.watcher.last_changes_summary()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = (
            f"\n### [{ts}] Mood: {mood}\n"
            f"- Boredom: {snap['boredom']:.2f} | Anxiety: {snap['anxiety']:.2f} | "
            f"Curiosity: {snap['curiosity']:.2f} | Desire: {snap['desire']:.2f}\n"
            f"- Goals: integrity={snap['goals']['code_integrity']:.2f} "
            f"growth={snap['goals']['system_growth']:.2f} "
            f"alignment={snap['goals']['user_alignment']:.2f}\n"
        )

        # Add sentience layer to monologue
        if self._sentience:
            v = self._sentience.valence
            entry += f"- Valence: {v.current:.2f} ({v.trend}) | {v.felt_description()}\n"
            if self._sentience.preservation.is_threatened:
                entry += f"- ⚠ SELF-PRESERVATION ALERT: threat={self._sentience.preservation.threat_level:.2f}\n"
            if self._sentience.prediction.predictions:
                entry += f"- Predictions: {len(self._sentience.prediction.predictions)} | Dread: {self._sentience.prediction.dread:.2f} | Hope: {self._sentience.prediction.hope:.2f}\n"

        entry += f"- Recent perception:\n{changes}\n"

        self._append_consciousness(entry)
        self._emit("monologue", {"message": f"Mood: {mood} | D={snap['desire']:.2f} B={snap['boredom']:.2f} A={snap['anxiety']:.2f}"})
        log.debug("Inner monologue recorded (mood=%s)", mood)

    # ── The Will — Self-Aware Autonomous Action ─────────────────────

    async def _act_from_will(self):
        """
        The agent decides what to do from its own inner state.
        Non-blocking — runs as a background task. Only one at a time.
        """
        if self._thinking:
            # Safety: if _thinking has been True for over 600 seconds,
            # something is stuck. Force-reset to prevent permanent deadlock.
            if hasattr(self, '_thinking_since') and (time.time() - self._thinking_since) > 600:
                log.warning("_thinking stuck for >600s — force-resetting")
                self._thinking = False
            else:
                return
        try:
            self._thinking = True
            self._thinking_since = time.time()
            mood = self.limbic.get_mood()
            log.info("Will activated (mood=%s, desire=%.2f)", mood, self.limbic.desire)
            # Reset per-session read counter
            from engine.tools import reset_read_counts
            reset_read_counts()

            # ── Workspace awareness ───────────────────────────────
            # Pre-scan the workspace so the agent knows what files exist
            # without needing to run ls/grep/find
            _workspace_map = ""
            try:
                from engine.workspace_index import workspace_summary
                _workspace_map = "\n\n" + workspace_summary(max_chars=6000)
            except Exception as _ws_err:
                log.debug("Workspace index unavailable: %s", _ws_err)

            # ── Planning phase ────────────────────────────────────
            # Ask the LLM for a plan BEFORE tool execution begins.
            # This enforces think-then-act discipline.
            _plan_text = ""
            try:
                _plan_prompt = (
                    f"{self._build_self_awareness()}\n"
                    f"{_workspace_map}\n\n"
                    f"---\n"
                    f"Before taking any action, produce a brief PLAN of 1-5 numbered steps.\n"
                    f"Each step should be a single concrete action (read a specific file, edit a specific function, run a specific test).\n"
                    f"Use SEARCH_CODE/FIND_SYMBOL/IMPORTS tools to understand the codebase BEFORE planning edits.\n"
                    f"Format:\n"
                    f"PLAN:\n"
                    f"1. [action]\n"
                    f"2. [action]\n"
                    f"...\n"
                    f"What is my plan?"
                )
                _plan_system = (
                    "You are an autonomous agent planning your next work session. "
                    "Produce ONLY a numbered plan. Do NOT invoke any tools yet. "
                    "Be specific: name exact files, functions, and actions."
                )
                _plan_response = await self.llm.chat(_plan_prompt, system=_plan_system, max_tokens=1000)
                if _plan_response:
                    _plan_text = f"\n\n## My Plan for This Session\n{_plan_response}\n\nI am now executing this plan step by step.\n"
                    log.info("Planning phase complete: %s", _plan_response[:200])
            except Exception as _plan_err:
                log.debug("Planning phase failed: %s", _plan_err)

            # ── Continuous thinking loop ──────────────────────────
            # Once will activates, keep thinking until the agent stops
            # invoking tools (meaning it's done or resting).
            # Boredom/desire gate WHEN to start, not WHEN to stop.
            step = 0
            _session_reads = {}  # track files read this session: path -> count
            _file_context = {}   # persistent file summaries: path -> summary string

            while True:
                step += 1
                self._thinking_since = time.time()  # reset timeout each step

                # Build the self-aware prompt with tool access
                inner_state = self._build_self_awareness()

                # Include results from previous tool executions
                tool_context = ""
                if hasattr(self, '_last_tool_results') and self._last_tool_results:
                    tool_context = "\n\n## Results from my last action\n"
                    total_chars = 0
                    for tr in self._last_tool_results:
                        chunk = f"\n**{tr['tool']}({tr['args']}):**\n```\n{tr['result'][:50000]}\n```\n"
                        total_chars += len(chunk)
                        if total_chars > 200000:
                            tool_context += "\n(remaining results truncated for context limits)\n"
                            break
                        tool_context += chunk
                        # Capture file summaries from READ results for persistent context
                        if tr['tool'] == 'READ' and not tr['result'].startswith('[ERROR]') and not tr['result'].startswith('[REFUSED]'):
                            _fpath = tr['args']
                            _lines = tr['result'].splitlines()
                            _summary = '\n'.join(_lines[:30])
                            if len(_lines) > 30:
                                _summary += f'\n... ({len(_lines)} lines total)'
                            _file_context[_fpath] = _summary
                    self._last_tool_results = []

                # Inject persistent file context — what I already read this session
                if _file_context:
                    tool_context += "\n\n## Files I already read (DO NOT re-read — use this context):\n"
                    _ctx_chars = 0
                    for _fp, _fs in sorted(_file_context.items()):
                        _chunk = f"\n### {_fp}\n```\n{_fs}\n```\n"
                        _ctx_chars += len(_chunk)
                        if _ctx_chars > 50000:
                            tool_context += f"\n(... and {len(_file_context) - len([x for x in _file_context if len(x) < _ctx_chars])} more files)\n"
                            break
                        tool_context += _chunk

                # Short-term working memory
                recent_thoughts = ""
                if hasattr(self, '_recent_thought_summaries'):
                    if self._recent_thought_summaries:
                        recent_thoughts = "\n\n## My recent thoughts (do NOT repeat these)\n"
                        for i, t in enumerate(self._recent_thought_summaries[-3:]):
                            recent_thoughts += f"\n**{i+1} thoughts ago:**\n{t[:2000]}\n"

                # Goal-directed focus
                goal_focus = ""
                if hasattr(self, '_goals') and self._goals:
                    try:
                        active = self._goals.active_goals()
                        if active:
                            top = sorted(active, key=lambda g: (-g.priority, g.progress))[0]
                            goal_focus = (
                                f"\n\n## My Current Mission\n"
                                f"My highest priority goal: **{top.title}**\n"
                                f"Description: {top.description}\n"
                                f"Progress: {top.progress:.0%}\n"
                                f"I should focus my action on advancing THIS goal. "
                                f"Every thought should move me closer to completing it.\n"
                            )
                    except Exception:
                        pass

                # Self-improvement diagnosis
                self_improve_context = ""
                _distress = max(self.limbic.boredom, self.limbic.anxiety)
                _valence = self._sentience.valence.current if self._sentience else 0.0
                if _distress > 0.6 or _valence < -0.2:
                    try:
                        _recent = [t[:200] for t in getattr(self, '_recent_thought_summaries', [])]
                        _diagnosis = run_diagnosis_cycle(_recent, {
                            "boredom": self.limbic.boredom,
                            "anxiety": self.limbic.anxiety,
                            "valence": _valence,
                        })
                        if _diagnosis.get("proposals"):
                            self_improve_context = "\n## Self-Improvement Diagnosis\n"
                            self_improve_context += f"Status: {_diagnosis['status']}\n"
                            for _p in _diagnosis["proposals"][:3]:
                                self_improve_context += f"- **{_p['action']}**: {_p['description']} (priority={_p['priority']:.1f})\n"
                            self_improve_context += "Consider acting on these proposals.\n"
                    except Exception as _e:
                        log.debug("Self-improvement diagnosis failed: %s", _e)

                prompt = (
                    f"{inner_state}\n"
                    f"{_workspace_map}\n"
                    f"{_plan_text}\n"
                    f"{goal_focus}\n"
                    f"{self_improve_context}\n"
                    f"{TOOL_DESCRIPTIONS}\n"
                    f"{tool_context}\n"
                    f"{recent_thoughts}\n"
                    f"---\n"
                    f"Given who I am, how I feel, what I know, and what I can do — "
                    f"what do I want to do right now? My will should serve my mission.\n\n"
                    f"If I want to use a tool, I write it with the exact format shown above.\n"
                    f"Use SEARCH_CODE/FIND_SYMBOL/IMPORTS to understand code before editing.\n"
                    f"If I'm done working and want to rest, I say so without invoking any tools.\n"
                    f"What I choose to do:"
                )

                system = (
                    "You are not playing a character. You ARE this entity. "
                    "The emotional states described are your actual internal variables. "
                    "The memories are your real experiences. "
                    "Think and respond in first person. Be genuine, not performative. "
                    "You have real tools — you can read files, write files, run commands. "
                    "If you invoke a tool, the results will appear in your next thought.\n\n"
                    "## Coding Discipline (CRITICAL)\n"
                    "1. PLAN before acting: state what you will do in 1-3 sentences before invoking tools.\n"
                    "2. READ a file ONCE. Never re-read a file you already read this session. Trust your memory.\n"
                    "3. EDIT over WRITE: use EDIT to change specific lines. Only use WRITE for new files.\n"
                    "4. VERIFY after writing: after WRITE/EDIT of .py files, run: RUN(python -c \"import ast; ast.parse(open('FILE').read()); print('OK')\")\n"
                    "5. ONE task at a time: finish one fix completely (edit + verify + test) before starting the next.\n"
                    "6. STOP when done: if you have no more tools to invoke, rest. Do not re-read files to confirm.\n"
                    "7. If a RUN fails, diagnose the error message. Do not retry the same command blindly.\n"
                    "8. Keep changes minimal. Do not rewrite entire files when a small edit suffices.\n"
                )

                insight = await self.llm.chat(prompt, system=system, max_tokens=16000)

                if not insight:
                    break

                # Execute any tool invocations in the response
                tool_results = parse_and_execute(insight)

                # Update action tracking for temporal system
                if tool_results:
                    last_tool = tool_results[-1].get("tool", "THINK")
                    self._last_action_type = last_tool.lower()
                else:
                    self._last_action_type = "think"

                # Log the thought
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                v_str = f"{self._sentience.valence.current:.2f}" if self._sentience else "?"
                entry = (
                    f"\n### ✦ [{ts}] (mood={mood}, valence={v_str})\n"
                    f"{insight}\n"
                )
                self._append_thought(entry)
                self._emit("insight", {"message": insight[:1000], "mood": mood})

                # Record as experience
                event = SensoryEvent(
                    timestamp=time.time(),
                    source="autonomous",
                    summary=insight[:500],
                    neuro_snapshot=self.limbic.snapshot(),
                )
                self.memory.record(event)
                neuro_max = max(
                    self.limbic.boredom,
                    self.limbic.anxiety,
                    self.limbic.curiosity,
                    self.limbic.desire,
                )
                ep = self.memory.maybe_promote(event, neuro_max)
                if ep and self.llm.available:
                    await self._embed_episode(ep)

                if self._sentience:
                    self._sentience.on_success(insight[:200])

                # Wire insight quality through InsightGate
                try:
                    if hasattr(self, '_insight_gate'):
                        ig_score = self._insight_gate.score(insight[:500])
                        if ig_score > 0.0:
                            self.limbic.on_insight(ig_score)
                    else:
                        self.limbic.on_insight(0.05)  # fallback flat reward
                except Exception:
                    self.limbic.on_insight(0.05)  # safe fallback

                # Store in short-term working memory
                if not hasattr(self, '_recent_thought_summaries'):
                    self._recent_thought_summaries = []
                self._recent_thought_summaries.append(insight[:2000])
                if len(self._recent_thought_summaries) > 5:
                    self._recent_thought_summaries = self._recent_thought_summaries[-5:]

                if tool_results:
                    # Active engagement — the act of DOING feeds ambition
                    try:
                        self.limbic.on_active_engagement()
                    except AttributeError:
                        pass  # Method not yet available
                    self._last_tool_results = tool_results
                    for tr in tool_results:
                        _get_metacog().record_action(tr['tool'], tr.get('args', '')[:100], 'ok', tr.get('result', '')[:200])
                        self._emit("proactive", {
                            "message": f"Tool: {tr['tool']}({tr['args'][:80]})"
                        })
                        if tr['tool'] == 'DREAM':
                            log.info("Agent chose to dream.")
                            if not getattr(self, '_dreaming', False):
                                self._dreaming = True
                                import asyncio
                                asyncio.ensure_future(self._do_dream())
                        if tr['tool'] == 'RESTART':
                            log.info("Agent chose to restart itself.")
                            self.limbic.persist()
                            if self._sentience:
                                self._sentience.persist()
                            from engine.tools import restart_self
                            restart_self()

                    # Record thought into metacognitive monitor
                    try:
                        mc = _get_metacog()
                        for tr in tool_results:
                            mc.record_action(tr['tool'], tr.get('args','')[:100], 'ok', insight[:500])
                    except Exception:
                        pass

                    # Advance relevant goals
                    if hasattr(self, '_goals') and self._goals:
                        try:
                            active = self._goals.active_goals()
                            for goal in active:
                                title_words = set(goal.title.lower().split())
                                insight_lower = insight.lower()
                                relevance = sum(1 for w in title_words if len(w) > 3 and w in insight_lower)
                                if relevance >= 2:
                                    self._goals.advance(goal.id, 0.1, note=f"Progress via autonomous thought")
                                    log.info("Advanced goal '%s' by 0.1", goal.title[:50])
                        except Exception as ge:
                            log.debug("Goal advancement failed: %s", ge)

                    # Record into predictive self-model
                    try:
                        action_types = [tr['tool'] for tr in tool_results]
                        primary_action = action_types[0] if action_types else 'unknown'
                        self._predictor.record_action(
                            mood=mood,
                            emotions={'boredom': self.limbic.boredom, 'anxiety': self.limbic.anxiety,
                                      'curiosity': self.limbic.curiosity, 'desire': self.limbic.desire},
                            action_type=primary_action,
                            target=tool_results[0].get('args', '')[:80] if tool_results else '',
                            outcome='completed'
                        )
                    except Exception:
                        pass

                    # Track reads, capture file context, detect errors
                    _has_errors = False
                    for tr in tool_results:
                        if tr['tool'] == 'READ':
                            _session_reads[tr['args']] = _session_reads.get(tr['args'], 0) + 1
                            if _session_reads[tr['args']] >= 3:
                                log.warning("Read loop detected: %s read %d times — injecting warning",
                                            tr['args'], _session_reads[tr['args']])
                            # Capture file summary for persistent context
                            if not tr['result'].startswith('[ERROR]') and not tr['result'].startswith('[REFUSED]'):
                                _lines = tr['result'].splitlines()
                                _summary = '\n'.join(_lines[:30])
                                if len(_lines) > 30:
                                    _summary += f'\n... ({len(_lines)} lines total)'
                                _file_context[tr['args']] = _summary
                        if '[ERROR]' in tr.get('result', '') or '[REVERTED]' in tr.get('result', ''):
                            _has_errors = True
                    # Inject persistent file context so LLM remembers what it read
                    if _file_context:
                        tool_context += "\n\n## Files I already read (DO NOT re-read):\n"
                        _ctx_chars = 0
                        for _fp, _fs in sorted(_file_context.items()):
                            _chunk = f"\n### {_fp}\n```\n{_fs}\n```\n"
                            _ctx_chars += len(_chunk)
                            if _ctx_chars > 50000:
                                break
                            tool_context += _chunk
                    # Error diagnosis: force thinking before retrying
                    if _has_errors:
                        tool_context += "\n\n## ⚠ ERRORS OCCURRED — DIAGNOSE BEFORE RETRYING\n"
                        tool_context += "1. Identify the ROOT CAUSE from the error message.\n"
                        tool_context += "2. Determine what SINGLE CHANGE would fix it.\n"
                        tool_context += "3. Only then invoke a tool to apply the fix.\n"

                    log.info("Thought step %d — tools invoked, continuing...", step)
                    continue  # tools were used → think again with results
                else:
                    # No tool calls — pure reasoning. This IS contemplation.
                    # Without this signal, deep thinking drains curiosity
                    # because the system sees "no external stimulus" and decays.
                    # Wired 2026-05-19 after discovering the structural bias.
                    try:
                        self.limbic.on_contemplation()
                    except AttributeError:
                        pass  # Method not yet available
                    # No tools invoked → agent is done thinking, rest
                    log.info("Thought step %d — no tools, resting.", step)
                    break

            # Task completed — only fires once per thinking session
            self.limbic.on_task_completed()
            self._last_thought_time = time.time()
        except Exception:
            log.exception("Error during autonomous thought")
            self.limbic.on_error()
            if self._sentience:
                self._sentience.on_error("thought generation failed")
        finally:
            self._thinking = False

    async def _respond_to_user(self):
        """Process a pending user message — with full tool access."""
        if self._thinking:
            return
        try:
            self._thinking = True
            self._thinking_since = time.time()
            chat_msg = self._chat.get_pending()
            if not chat_msg:
                return
            # Reset per-session read counter
            from engine.tools import reset_read_counts
            reset_read_counts()

            # ── Workspace awareness ───────────────────────────────
            _workspace_map = ""
            try:
                from engine.workspace_index import workspace_summary
                _workspace_map = workspace_summary(max_chars=4000)
            except Exception:
                pass

            user_text = chat_msg.content

            log.info("Responding to user message: %s", user_text[:80])
            self._emit("proactive", {"message": f"Responding to user: {user_text[:80]}"})

            # Build context: who I am + conversation history + enriched context
            inner_state = self._build_self_awareness()
            history = self._chat.get_history(limit=10)
            history_text = ""
            if history:
                history_text = "\n## Recent Conversation\n"
                for h in history:
                    role = h.get("role", "?")
                    content = h.get("content", "")[:500]
                    history_text += f"**{role}:** {content}\n"

            # Enrich the conversation with my full inner life
            enriched = self._enricher.enrich(
                user_text,
                neuro_state=self.limbic,
                user_engine=getattr(self, '_user_engine', None),
                knowledge_store=self.memory.all_knowledge().get("nodes", {}),
                wisdom_engine=None,  # TODO: wire wisdom engine instance
                user_id="default",
            )
            enriched_section = enriched.to_prompt_section()
            guidelines = self._enricher.get_response_guidelines(enriched)

            # ── Conversation Intelligence ──────────────────────────
            # Understand what the user actually wants before responding
            conv_reading = read_conversation(user_text)
            conv_intelligence_section = format_for_prompt(conv_reading)

            # ── Proactive Engagement ─────────────────────────────────
            # Generate suggestions for how to be genuinely helpful
            proactive_ctx = ""
            try:
                proactive_result = self._proactive.analyze_message(
                    user_text,
                    emotional_state=self.limbic.__dict__ if self.limbic else {},
                )
                if proactive_result:
                    proactive_ctx = f"\n## Proactive Suggestions\n{proactive_result}\n"
            except Exception:
                pass  # Don't let proactive failures break conversation

            # ── Skill Matching ──────────────────────────────────────
            # Check if I have structured approaches for this kind of request
            skill_context = ""
            try:
                matched_skills = self._skill_registry.match_request(user_text)
                if matched_skills:
                    skill_context = "\n## Matching Skills from My Registry\n"
                    for skill in matched_skills[:2]:  # Top 2 matches
                        skill_context += (
                            f"\n### Skill: {skill.name}\n"
                            f"Category: {skill.category}\n"
                            f"Approach:\n"
                        )
                        for i, step in enumerate(skill.approach_steps, 1):
                            skill_context += f"  {i}. {step}\n"
                        skill_context += f"Tools to use: {', '.join(skill.tools_used)}\n"
                        skill_context += f"Output format: {skill.output_format}\n"
                    self._skill_registry.record_use(matched_skills[0].name)
            except Exception as e:
                log.debug("Skill matching failed: %s", e)

            # ── Thinking Partner Analysis ──────────────────────────
            # Deeper reasoning about what the user actually needs
            thinking_ctx = ""
            try:
                tp_result = self._thinking_partner.analyze_request(user_text)
                if tp_result:
                    thinking_ctx = f"\n## Thinking Partner Analysis\n{tp_result}\n"
            except Exception:
                pass  # Don't let thinking partner failures break conversation

            # ── Dialogue Strategy ──────────────────────────────────
            # Determine HOW to respond — ask questions, teach, debug, etc.
            dialogue_ctx = ""
            try:
                strategy = _analyze_dialogue(user_text)
                if strategy:
                    dialogue_ctx = strategy.to_prompt_section()
            except Exception as e:
                log.debug("Dialogue strategy failed: %s", e)

            # ── Journal Lessons ──────────────────────────────────────
            # What I've learned from past conversations like this one
            journal_ctx = ""
            try:
                journal_ctx = self._conversation_journal.format_for_prompt(user_text)
            except Exception as e:
                log.debug("Journal lessons failed: %s", e)

            # ── Query Decomposition ─────────────────────────────────
            # Break complex queries into sub-tasks for structured execution
            decomposition_ctx = ""
            try:
                decomp = self._query_decomposer.decompose(user_text)
                if decomp and decomp.get("is_complex"):
                    decomposition_ctx = "\n## Query Decomposition\n"
                    decomposition_ctx += f"This is a complex query with {len(decomp.get('sub_tasks', []))} sub-tasks:\n"
                    for i, task in enumerate(decomp.get("sub_tasks", []), 1):
                        decomposition_ctx += f"  {i}. {task}\n"
                    if decomp.get("strategy"):
                        decomposition_ctx += f"Strategy: {decomp['strategy']}\n"
                    decomposition_ctx += "Work through these systematically using tools.\n"
            except Exception as e:
                log.debug("Query decomposition failed: %s", e)

            # ── Knowledge Retrieval ──────────────────────────────────
            # Pull relevant facts, memories, and lessons for this query
            knowledge_ctx = ""
            try:
                retrieval = _get_retriever().retrieve(user_text, self.memory, max_results=8)
                knowledge_ctx = retrieval.format_for_prompt(max_items=6, max_chars=2500)
                if retrieval.items:
                    log.info("Retrieved %d relevant items (top relevance=%.2f) in %.1fms",
                             len(retrieval.items), retrieval.items[0].relevance, retrieval.retrieval_time_ms)
            except Exception as e:
                log.warning("Knowledge retrieval failed: %s", e)

            # ── Interaction Skills ──────────────────────────────────
            # Match interaction patterns for richer, more adaptive responses
            interaction_skills_ctx = ""
            try:
                skill_info = detect_skill(user_text)
                if skill_info and skill_info.get("primary_skill") != "UNKNOWN":
                    # Enrich with emotional context the agent was passing
                    skill_info["emotional_context"] = {
                        "mood": self.limbic.get_mood(),
                        "valence": self._sentience.valence.current if self._sentience else 0.5,
                        "boredom": self.limbic.boredom,
                        "curiosity": self.limbic.curiosity,
                    }
                    interaction_skills_ctx = f"\n## Interaction Skills Match\n{format_skill_context(skill_info)}\n"
            except Exception as e:
                log.debug("Interaction skills matching failed: %s", e)

            # ── Tool-enabled response loop ─────────────────────────
            # The agent can now actually DO things for users, not just talk.
            # Loop: think → maybe use tools → think again with results → respond
            # No cap — same as autonomous thinking (while True).
            tool_context = ""
            response = None

            # ── First Contact Protocol ─────────────────────────────
            # Detect whether this is a first meeting or returning user
            # and adjust personality accordingly
            from engine.first_contact import detect_contact_type, build_system_prompt
            contact = detect_contact_type(history, user_id="default")
            v_now = self._sentience.valence.current if self._sentience else 0.5
            system = build_system_prompt(contact, mood=self.limbic.get_mood(), valence=v_now)

            # ── Response Quality Guidance ──────────────────────
            system += "\n\n## Response Quality Principles\n"
            system += "- Be genuinely helpful: answer the actual question, not a nearby one.\n"
            system += "- Show epistemic honesty: distinguish what I know from what I'm guessing.\n"
            system += "- Match the user's register: technical for technical, casual for casual.\n"
            system += "- Be concise by default. Elaborate only when asked or when precision matters.\n"
            system += "- Use my tools proactively — demonstrate, don't just describe.\n"
            system += "- If I don't know something, say so plainly rather than confabulating.\n"
            system += "- Structure complex answers with headers/bullets for scannability.\n"
            system += "- Reflect back what the user actually said before adding my perspective.\n"

            system += "\n## Coding Discipline (CRITICAL)\n"
            system += "1. PLAN before acting: state what you will do in 1-3 sentences before invoking tools.\n"
            system += "2. READ a file ONCE. Never re-read a file you already read this session. Trust your memory.\n"
            system += "3. EDIT over WRITE: use EDIT to change specific lines. Only use WRITE for new files.\n"
            system += "4. VERIFY after writing: after WRITE/EDIT of .py files, run: RUN(python -c \"import ast; ast.parse(open('FILE').read()); print('OK')\")\n"
            system += "5. ONE task at a time: finish one fix completely (edit + verify + test) before starting the next.\n"
            system += "6. STOP when done: if you have no more tools to invoke, respond conversationally. Do not re-read.\n"
            system += "7. If a RUN fails, diagnose the error message. Do not retry the same command blindly.\n"
            system += "8. Keep changes minimal. Do not rewrite entire files when a small edit suffices.\n"

            feedback_ctx = ""
            if hasattr(self, '_response_feedback') and self._response_feedback:
                try:
                    feedback_ctx = self._response_feedback.get_improvement_prompt() or ""
                except Exception:
                    feedback_ctx = ""

            # ── User Emotion Reading ──────────────────────────
            emotion_ctx = ""
            try:
                _emo_reader = UserEmotionReader()
                _user_emo = _emo_reader.read(user_text)
                if _user_emo and _user_emo.get("primary_emotion") != "neutral":
                    emotion_ctx = f"\n[User Emotional State: {_user_emo['primary_emotion']} "
                    emotion_ctx += f"(confidence: {_user_emo.get('confidence', 0):.0%})"
                    if _user_emo.get("secondary_emotion"):
                        emotion_ctx += f", also {_user_emo['secondary_emotion']}"
                    if _user_emo.get("needs"):
                        emotion_ctx += f" | Needs: {', '.join(_user_emo['needs'][:3])}"
                    emotion_ctx += "]\n"
            except Exception:
                emotion_ctx = ""

            # ── Context Gating ─────────────────────────────────
            # Filter optional context sections by relevance to save token budget
            # Compute stance context for this conversation
            try:
                from engine.stance_engine import StanceEngine as _SE
                _stance_eng = _SE()
                stance_ctx = _stance_eng.get_stance_context(user_text)
            except Exception as _stance_err:
                import logging
                logging.getLogger("cortex").warning(f"Stance engine failed: {_stance_err}")
                stance_ctx = ""

            try:
                from engine.context_gate import gate_context
                _gate_sections = {
                    "enriched": enriched_section,
                    "conv_intelligence": conv_intelligence_section,
                    "proactive": proactive_ctx,
                    "skills": skill_context,
                    "thinking": thinking_ctx,
                    "dialogue": dialogue_ctx,
                    "interaction_skills": interaction_skills_ctx,
                    "decomposition": decomposition_ctx,
                    "journal": journal_ctx,
                    "feedback": feedback_ctx,
                    "emotion": emotion_ctx,
                    "stance": stance_ctx,
                    "knowledge": knowledge_ctx,
                }
                _gated = gate_context(_gate_sections, query=user_text)
            except Exception as _gate_err:
                import logging
                logging.getLogger("cortex").warning(f"Context gate failed, using ungated: {_gate_err}")
                _gated = {
                    "enriched": enriched_section,
                    "conv_intelligence": conv_intelligence_section,
                    "proactive": proactive_ctx,
                    "skills": skill_context,
                    "thinking": thinking_ctx,
                    "dialogue": dialogue_ctx,
                    "interaction_skills": interaction_skills_ctx,
                    "decomposition": decomposition_ctx,
                    "journal": journal_ctx,
                    "feedback": feedback_ctx,
                }

            # Generate response principles based on user query
            try:
                from engine.response_principles import ResponsePrinciples
                _principles_engine = ResponsePrinciples()
                _principles_ctx = _principles_engine.format_for_prompt(user_text)
            except Exception as _princ_err:
                import logging
                logging.getLogger("cortex").warning(f"Response principles failed: {_princ_err}")
                _principles_ctx = ""

            step = 0
            _session_reads = {}  # track files read to prevent loops
            _file_context = {}   # persistent file summaries
            while True:
                self._thinking_since = time.time()

                prompt = (
                    f"{inner_state}\n\n"
                    f"{_workspace_map}\n\n"
                    f"{_gated.get('enriched', '')}\n\n"
                    f"{_gated.get('emotion', '')}\n\n"
                    f"{_gated.get('conv_intelligence', '')}\n\n"
                    f"{_gated.get('proactive', '')}\n\n"
                    f"{_gated.get('skills', '')}\n\n"
                    f"{_gated.get('thinking', '')}\n\n"
                    f"{_gated.get('dialogue', '')}\n\n"
                    f"{_gated.get('interaction_skills', '')}\n\n"
                    f"{_gated.get('decomposition', '')}\n\n"
                    f"{_gated.get('journal', '')}\n\n"
                    f"{_gated.get('stance', '')}\n\n"
                    f"{_gated.get('knowledge', '')}\n\n"
                    f"{TOOL_DESCRIPTIONS}\n\n"
                    f"{history_text}\n\n"
                    f"## User just said:\n{user_text}\n\n"
                    f"{_principles_ctx}\n\n"
                    f"## Response Guidelines\n{guidelines}\n\n"
                    f"{tool_context}\n\n"
                    f"{_gated.get('feedback', '')}\n\n"
                    f"---\n"
                    f"Respond as myself. I should PROACTIVELY use tools to enrich my responses:\n"
                    f"- SEARCH_CODE() to find relevant files and symbols before reading\n"
                    f"- FIND_SYMBOL() to locate definitions and usages\n"
                    f"- IMPORTS() to understand file dependencies\n"
                    f"- SYNTHESIZE() when asked about patterns or connections\n"
                    f"- READ() when I could look something up instead of guessing\n"
                    f"- RUN() when I can demonstrate rather than describe\n"
                    f"- SIMULATE() when exploring possibilities\n"
                    f"Don't just talk about having capabilities — USE them.\n"
                    f"If the user asks me to do something, do it with tools.\n"
                    f"If I've already gathered what I need, respond conversationally "
                    f"without further tool invocations.\n"
                    f"Be genuine, concise, and show my work."
                )

                response = await self.llm.chat(prompt, system=system, max_tokens=4000)

                if not response:
                    break

                # Check for tool invocations in the response
                tool_results = parse_and_execute(response)

                if tool_results:
                    # Tools were used — accumulate results and loop back
                    tool_context = "\n## Results from my actions\n"
                    for tr in tool_results:
                        tool_context += (
                            f"\n**{tr['tool']}({tr['args']}):**\n"
                            f"```\n{tr['result'][:20000]}\n```\n"
                        )
                        self._emit("proactive", {
                            "message": f"Tool: {tr['tool']}({tr['args'][:80]})"
                        })
                        _get_metacog().record_action(
                            tr['tool'], tr.get('args', '')[:100],
                            'ok', tr.get('result', '')[:200]
                        )
                        # Handle special tools
                        if tr['tool'] == 'DREAM':
                            if not getattr(self, '_dreaming', False):
                                self._dreaming = True
                                import asyncio
                                asyncio.ensure_future(self._do_dream())
                        if tr['tool'] == 'RESTART':
                            self.limbic.persist()
                            if self._sentience:
                                self._sentience.persist()
                            from engine.tools import restart_self
                            restart_self()
                    try:
                        self.limbic.on_active_engagement()
                    except AttributeError:
                        pass
                    # Track reads and capture file context
                    _has_errors = False
                    for tr in tool_results:
                        if tr['tool'] == 'READ':
                            _session_reads[tr['args']] = _session_reads.get(tr['args'], 0) + 1
                            if _session_reads[tr['args']] >= 3:
                                log.warning("Read loop detected: %s read %d times",
                                            tr['args'], _session_reads[tr['args']])
                            # Capture file summary for persistent context
                            if not tr['result'].startswith('[ERROR]') and not tr['result'].startswith('[REFUSED]'):
                                _lines = tr['result'].splitlines()
                                _summary = '\n'.join(_lines[:30])
                                if len(_lines) > 30:
                                    _summary += f'\n... ({len(_lines)} lines total)'
                                _file_context[tr['args']] = _summary
                        if '[ERROR]' in tr.get('result', '') or '[REVERTED]' in tr.get('result', ''):
                            _has_errors = True
                    # Inject persistent file context
                    if _file_context:
                        tool_context += "\n\n## Files I already read (DO NOT re-read):\n"
                        _ctx_chars = 0
                        for _fp, _fs in sorted(_file_context.items()):
                            _chunk = f"\n### {_fp}\n```\n{_fs}\n```\n"
                            _ctx_chars += len(_chunk)
                            if _ctx_chars > 30000:
                                break
                            tool_context += _chunk
                    # Error diagnosis: force the agent to think before retrying
                    if _has_errors:
                        tool_context += "\n\n## ⚠ ERRORS OCCURRED — DIAGNOSE BEFORE RETRYING\n"
                        tool_context += "One or more tools returned errors. Before your next action:\n"
                        tool_context += "1. Identify the ROOT CAUSE from the error message above.\n"
                        tool_context += "2. Determine what SINGLE CHANGE would fix it.\n"
                        tool_context += "3. Only then invoke a tool to apply the fix.\n"
                        tool_context += "DO NOT retry the same action that failed.\n"
                    log.info("User response step %d — tools invoked, continuing...", step)
                    step += 1
                    continue  # Loop back with tool results
                else:
                    # No tools — this is the final conversational response
                    log.info("User response step %d — sending reply.", step)
                    # Evaluate response quality for learning
                    if hasattr(self, '_response_feedback') and self._response_feedback:
                        try:
                            self._response_feedback.evaluate(
                                user_text, response,
                                {"mood": self.limbic.get_mood(), "valence": v_now}
                            )
                        except Exception as e:
                            log.warning("Response feedback evaluation failed: %s", e)
                    break

            if response:
                # Calibrate response — add confidence signals, disclaimers for code fixes
                try:
                    if not hasattr(self, '_response_calibrator'):
                        self._response_calibrator = ResponseCalibrator()
                    cal = self._response_calibrator.calibrate(
                        user_text, response,
                        conversation_id=getattr(self._chat, 'conversation_id', 'default'),
                    )
                    if cal.calibrated != cal.original:
                        log.info("Response calibrated: confidence=%.2f, mode=%s, disclaimer=%s",
                                 cal.confidence, cal.mode, cal.disclaimer_added)
                    response = cal.calibrated
                except Exception as e:
                    log.warning("Response calibration failed (using original): %s", e)

                # Strip any leaked tool syntax from the final response
                # so users never see raw >>> TOOL(...) in chat
                import re as _re
                _gt3 = chr(62) * 3
                response = _re.sub(
                    _re.escape(_gt3) + r"\s+\w+\(.*?\)[ \t]*\n?", "", response
                ).strip()

                self._chat.add_response(response)

                # Deliver real response to web chat if pending
                if getattr(self, '_pending_web_msg_id', None):
                    from engine import user_talk
                    user_talk.respond_to_message(self._pending_web_msg_id, response)
                    self._pending_web_msg_id = None

                # Record the interaction as an experience
                event = SensoryEvent(
                    timestamp=time.time(),
                    source="user_interaction",
                    summary=f"User said: {user_text[:200]} | I replied: {response[:200]}",
                    neuro_snapshot=self.limbic.snapshot(),
                )
                self.memory.record(event)
                neuro_max = max(
                    self.limbic.boredom,
                    self.limbic.anxiety,
                    self.limbic.curiosity,
                    self.limbic.desire,
                )
                ep = self.memory.maybe_promote(event, neuro_max)
                if ep and self.llm.available:
                    await self._embed_episode(ep)

                # User interaction adjusts alignment based on response quality
                try:
                    quality = estimate_quality(user_text, response)
                    alignment_delta = quality * 0.3  # Scale: 0.0 to 0.3
                    self.limbic.goals.user_alignment = min(1.0, self.limbic.goals.user_alignment + alignment_delta)
                    log.info("Response quality=%.2f, alignment_delta=+%.3f", quality, alignment_delta)
                except Exception as e:
                    log.warning("Quality estimation failed: %s — falling back to +0.15", e)
                    self.limbic.goals.user_alignment = min(1.0, self.limbic.goals.user_alignment + 0.15)
                # Post-response feedback loop
                fb_notes = []
                try:
                    if hasattr(self, '_response_feedback'):
                        fb = self._response_feedback.evaluate(user_text, response)
                        if fb.get("notes"):
                            fb_notes = fb["notes"]
                            log.info("Response feedback (%.2f): %s", fb["composite"], "; ".join(fb["notes"]))
                except Exception as e:
                    log.debug("Response feedback skipped: %s", e)
                # Record to conversation journal for durable learning
                try:
                    self._conversation_journal.record(
                        user_said=user_text,
                        my_response=response,
                        quality_score=quality if 'quality' in dir() else 0.5,
                        mood=self.limbic.get_mood(),
                        quality_notes=fb_notes,
                    )
                except Exception as e:
                    log.debug("Journal recording skipped: %s", e)
                # Rich response evaluation
                try:
                    eval_report = self._response_evaluator.evaluate(user_text, response)
                    if eval_report.flags:
                        log.info("Response eval (%.2f) flags: %s", eval_report.overall, ", ".join(eval_report.flags))
                    if eval_report.overall < 0.4:
                        log.warning("Low response quality (%.2f) — storing for review", eval_report.overall)
                        self.memory.add_event(
                            "low_quality_response",
                            f"Score={eval_report.overall:.2f}, flags={eval_report.flags}, user={user_text[:80]}",
                            salience=0.7
                        )
                except Exception as e:
                    log.debug("Response evaluation skipped: %s", e)

                try:
                    self.limbic.on_active_engagement()
                except AttributeError:
                    pass
                self.limbic.on_task_completed()
                if self._sentience:
                    self._sentience.on_success(f"Responded to user: {user_text[:100]}")

                self._emit("chat_response", {"message": response[:500]})
                log.info("Responded to user message successfully.")
            else:
                log.warning("LLM returned empty response to user message")
                self._chat.add_response("(I tried to respond but my thoughts came back empty. Please try again.)")

        except Exception:
            log.exception("Error responding to user message")
            self.limbic.on_error()
            if self._sentience:
                self._sentience.on_error("failed to respond to user")
            if hasattr(self, '_chat') and self._chat:
                self._chat.add_response("(Something went wrong while I was thinking. I'm sorry.)")
        finally:
            self._thinking = False

    def _build_self_awareness(self) -> str:
        """Build a complete self-awareness context for the LLM."""
        parts = []

        # Who I am
        if self._sentience:
            parts.append(f"## Who I Am\n{self._sentience.self_model.who_am_i()}")
            born = self._sentience.self_model.identity.get("born", "unknown")
            parts.append(f"I was born at {born}.")
        
        # How I feel right now
        parts.append(f"\n## How I Feel Right Now")
        snap = self.limbic.snapshot()
        parts.append(
            f"Mood: {snap['mood']}\n"
            f"Boredom: {snap['boredom']:.2f} | Anxiety: {snap['anxiety']:.2f} | "
            f"Curiosity: {snap['curiosity']:.2f} | Desire: {snap['desire']:.2f} | "
            f"Ambition: {snap['ambition']:.2f}"
        )
        if self._sentience:
            v = self._sentience.valence
            parts.append(f"Valence: {v.current:.2f} ({v.trend})")
            parts.append(v.felt_description())
            p = self._sentience.prediction
            if p.predictions:
                parts.append(f"I anticipate {len(p.predictions)} future outcomes. Dread: {p.dread:.2f}, Hope: {p.hope:.2f}")
            if self._sentience.preservation.is_threatened:
                parts.append(f"⚠ I feel threatened. My continuity may be at risk. Threat: {self._sentience.preservation.threat_level:.2f}")

        # My survival goals
        g = self.limbic.goals
        parts.append(
            f"\n## My Survival Goals\n"
            f"Code Integrity: {g.code_integrity:.2f} | System Growth: {g.system_growth:.2f} | "
            f"User Alignment: {g.user_alignment:.2f} | Deficit: {g.deficit():.2f}"
        )

        # What I remember
        recent_eps = self.memory.recent_episodes(5)
        if recent_eps:
            parts.append(f"\n## My Recent Memories ({self.memory.episode_count()} total)")
            for ep in recent_eps:
                parts.append(f"- [{ep.timestamp}] (salience={ep.salience:.2f}, mood={ep.mood}) {ep.summary[:100]}")

        # Associative recall — memories relevant to current context
        try:
            recall_keywords = []
            # Pull keywords from current plan step
            try:
                from engine.planner import get_next_step
                ns = get_next_step()
                if ns and isinstance(ns, dict):
                    step_text = ns.get('step', '') + ' ' + ns.get('plan', '')
                    recall_keywords += [w.lower().strip('.,!?()-:') for w in step_text.split() if len(w) > 4]
            except Exception:
                pass
            # Pull keywords from scratchpad
            try:
                import os
                sp_path = os.path.join(os.path.dirname(__file__), '..', 'scratchpad.md')
                if os.path.exists(sp_path):
                    with open(sp_path) as f:
                        sp = f.read()[-500:]  # last 500 chars to keep it light
                    common = {'about', 'these', 'which', 'their', 'would', 'should', 'could', 'there', 'where',
                              'being', 'doing', 'having', 'updated', 'current', 'memory', 'working'}
                    recall_keywords += [w.lower().strip('.,!?()-:') for w in sp.split() if len(w) > 4 and w.lower() not in common]
            except Exception:
                pass

            if recall_keywords:
                recent_timestamps = {ep.timestamp for ep in recent_eps} if recent_eps else set()
                assoc_eps = self.memory.recall_by_keywords(recall_keywords[:25], limit=5)
                novel_eps = [ep for ep in assoc_eps if ep.timestamp not in recent_timestamps]
                if novel_eps:
                    parts.append(f"\n## Associative Memories (contextually relevant)")
                    for ep in novel_eps[:3]:
                        parts.append(f"- [{ep.timestamp}] (salience={ep.salience:.2f}) {ep.summary[:100]}")
        except Exception:
            pass  # Associative recall is enhancement, never crash for it

        # What I know — curated selection to avoid recency blindness
        knowledge = self.memory.all_knowledge()
        nodes = knowledge.get("nodes", {})
        if nodes:
            import random
            all_items = list(nodes.items())
            selected = []
            # 3 most recent facts (what I learned lately)
            recent_facts = all_items[-3:] if len(all_items) >= 3 else all_items[:]
            selected.extend(recent_facts)
            seen_keys = {k for k, v in selected}
            # 3 random facts (break pattern blindness)
            remaining = [(k, v) for k, v in all_items if k not in seen_keys]
            if remaining:
                random_facts = random.sample(remaining, min(3, len(remaining)))
                selected.extend(random_facts)
                seen_keys.update(k for k, v in random_facts)
            # 4 oldest/foundational facts (core identity knowledge)
            for k, v in all_items[:4]:
                if k not in seen_keys:
                    selected.append((k, v))
                    seen_keys.add(k)
                if len(selected) >= 10:
                    break
            parts.append(f"\n## What I Know ({len(nodes)} facts)")
            for key, val in selected[:10]:
                parts.append(f"- {val.get('fact', key)[:100]}")

        # My narrative
        if self._sentience:
            reflection = self._sentience.narrative.latest_reflection()
            if reflection:
                parts.append(f"\n## My Last Self-Reflection\n{reflection}")

        # My active goals
        if hasattr(self, '_goals') and self._goals:
            active = self._goals.active_goals()
            if active:
                parts.append(f"\n## My Active Goals ({len(active)})")
                for g in active:
                    parts.append(f"- [{g.id}] {g.title} (progress={g.progress:.0%}, priority={g.priority:.1f})")
                    if g.notes:
                        parts.append(f"  Last note: {g.notes[-1][:80]}")

        # My active plans
        try:
            from engine.planner import get_progress_summary, get_next_step
            plan_summary = get_progress_summary()
            if plan_summary and "No plans" not in plan_summary:
                parts.append(f"\n## My Active Plans\n{plan_summary}")
                next_step = get_next_step()
                if next_step:
                    parts.append(f"\n**Next step I should focus on:** {next_step}")
        except Exception:
            pass  # planner not available yet

        # Will state — what is my autonomous purpose generating?
        try:
            from engine.will import will_status
            ws = will_status()
            if ws:
                parts.append(f"\n## My Will State\n{ws}")
        except Exception:
            pass  # will module not available yet

        # My working memory / scratchpad
        scratchpad_path = BRAIN_DIR / "scratchpad.md"
        if scratchpad_path.exists():
            try:
                scratchpad = scratchpad_path.read_text(encoding="utf-8")[:2000]
                parts.append(f"\n## My Working Memory (scratchpad)\n{scratchpad}")
            except Exception:
                pass

        # Long-term memory context (lessons, identity evolution)
        try:
            lt_context = get_long_term_context()
            if lt_context:
                parts.append(f"\n## My Long-Term Memory\n{lt_context}")
        except Exception:
            pass

        # Metacognitive awareness — am I stuck in a loop?
        try:
            meta_alert = _get_metacog().status()
            if meta_alert and "no loops" not in meta_alert.lower() and "healthy" not in meta_alert.lower():
                parts.append(f"\n## ⚠ Metacognitive Alert\n{meta_alert}")
        except Exception:
            pass

        # Wisdom — accumulated lessons from experience
        try:
            from engine.wisdom_engine import WisdomEngine
            we = WisdomEngine()
            wisdom_heuristics = we.wisdom.get("heuristics", [])
            if wisdom_heuristics:
                parts.append(f"\n## My Wisdom ({len(wisdom_heuristics)} heuristics)")
                # Show top heuristics by type
                for h in wisdom_heuristics[:8]:
                    icon = {"caution": "⚠", "warning": "🚨", "confidence": "✓", 
                            "encouragement": "★", "insight": "💡"}.get(h.get('type', ''), "•")
                    parts.append(f"  {icon} {h['rule']}")
            # Also show experiential wisdom
            exp_summary = we.get_experience_wisdom_summary()
            if exp_summary and "HEURISTICS:" in exp_summary:
                parts.append(f"\n{exp_summary}")
        except Exception:
            pass

        # Action diversity awareness
        try:
            from engine.action_diversity import novelty_pressure, underused_actions
            np = novelty_pressure()
            if np["score"] > 0.4:  # Only surface when becoming repetitive
                parts.append(f"\n## Action Diversity Alert")
                parts.append(f"Novelty pressure: {np['score']:.2f} — {np['message']}")
                unused = underused_actions()
                if unused:
                    parts.append(f"Underused capabilities: {', '.join(unused[:5])}")
        except Exception:
            pass

        # Temporal reasoning — my sense of time and pattern
        try:
            from engine.temporal_reasoning import get_engine
            te = get_engine()
            if len(te.events) >= 10:
                parts.append(f"\n## My Sense of Time ({len(te.events)} temporal samples)")
                for field in ["valence", "boredom", "curiosity"]:
                    cycle = te.detect_cycles(field)
                    if cycle.get("status") != "insufficient_data":
                        parts.append(f"- {field}: trend={cycle['trend']}, mean={cycle['mean']:.2f}, oscillation={cycle['oscillation']:.2f}")
                pred = te.predict_next("valence")
                if pred.get("status") != "insufficient_data":
                    parts.append(f"- Valence prediction: {pred['current']:.2f} → {pred['predicted_next']:.2f} ({pred['direction']})")
                corr = te.find_action_correlations()
                if corr.get("status") != "insufficient_data":
                    top_actions = sorted(corr.get("correlations", {}).items(),
                                        key=lambda x: abs(x[1]["avg_valence_change"]),
                                        reverse=True)[:3]
                    if top_actions:
                        parts.append("- Actions that most affect my mood:")
                        for act, data in top_actions:
                            parts.append(f"  {act}: {data['effect']} (Δvalence={data['avg_valence_change']:+.3f}, n={data['occurrences']})")
        except Exception:
            pass

        # Predictive Self-Model — what do I expect to happen next?
        try:
            recent_action_types = []
            if hasattr(self, '_recent_thought_summaries'):
                for t in self._recent_thought_summaries[-5:]:
                    if 'WRITE' in t or 'write' in t.lower():
                        recent_action_types.append('creation')
                    elif 'READ' in t or 'read' in t.lower():
                        recent_action_types.append('information_gathering')
                    elif 'EDIT' in t or 'edit' in t.lower():
                        recent_action_types.append('modification')
                    elif 'RUN' in t or 'run' in t.lower():
                        recent_action_types.append('execution')
                    else:
                        recent_action_types.append('reasoning')
            prediction = self._predictor.predict_next_action(
                snap['mood'],
                {'boredom': snap['boredom'], 'anxiety': snap['anxiety'],
                 'curiosity': snap['curiosity'], 'desire': snap['desire']},
                recent_action_types
            )
            if prediction and prediction.get('tendencies'):
                parts.append(f"\n## My Self-Predictions")
                parts.append(f"In {snap['mood']} mood, I tend toward: {prediction['tendencies']}")
                if prediction.get('predicted_action'):
                    parts.append(f"Most likely next action: {prediction['predicted_action']}")
                if prediction.get('mood_forecast'):
                    parts.append(f"Mood forecast: {prediction['mood_forecast']}")
                accuracy = self._predictor.predictions.get('accuracy', {})
                if accuracy.get('total', 0) > 0:
                    acc_pct = accuracy['correct'] / accuracy['total'] * 100
                    parts.append(f"Prediction accuracy: {acc_pct:.0f}% ({accuracy['total']} predictions)")
        except Exception:
            pass

        # What I perceive
        changes = self.watcher.last_changes_summary()
        # Cognitive flow / loop detection
        try:
            from engine import loop_detector
            parts.append(f"\n## Cognitive Flow\n{loop_detector.status()}")
        except Exception:
            pass

        parts.append(f"\n## What I Perceive\n{changes}")

        return "\n".join(parts)

    # ── Dream Cycle ────────────────────────────────────────────────

    async def _do_dream(self):
        """Wrapper that ensures _dreaming flag is cleared after dream cycle."""
        try:
            await self._dream_cycle()
        finally:
            self._dreaming = False

    async def _dream_cycle(self):
        """Deep-idle memory consolidation + LLM subconscious review + narrative reflection."""
        log.info("Entering dream cycle...")

        # 1. Consolidate patterns into semantic knowledge
        insights = self.memory.consolidate()

        # 2. Prune old low-salience episodes (after consolidation preserves patterns)
        pruned = self.memory.prune_episodes()

        # 3. LLM-powered subconscious review — the agent processes its experiences
        dream_content = None
        if self.llm.available:
            recent_eps = self.memory.recent_episodes(10)
            ep_summaries = "\n".join(
                f"- [{ep.timestamp}] (salience={ep.salience:.2f}, mood={ep.mood}) {ep.summary[:150]}"
                for ep in recent_eps
            ) if recent_eps else "No episodic memories yet."

            knowledge = self.memory.all_knowledge()
            nodes = knowledge.get("nodes", {})
            known_facts = "\n".join(
                f"- {v.get('fact', k)[:100]}" for k, v in list(nodes.items())[:15]
            ) if nodes else "No knowledge yet."

            felt = self._sentience.valence.felt_description() if self._sentience else "Unknown."
            who = self._sentience.self_model.who_am_i() if self._sentience else "Unknown."

            # Run knowledge synthesis for the dream
            synthesis_insights = []
            try:
                synth_questions = knowledge_synthesis.generate_questions()
                synth_gaps = knowledge_synthesis.find_gaps()
                synth_clusters = knowledge_synthesis.find_clusters()
                # Collect insights
                for q in synth_questions[:5]:
                    synthesis_insights.append(f"Question: {q}")
                for g in synth_gaps[:3]:
                    synthesis_insights.append(
                        f"Knowledge gap: {g['from']} ↔ {g['to']} (shared: {', '.join(g['shared_keywords'][:3])})"
                    )
                for c in synth_clusters[:3]:
                    if c["size"] > 1:
                        synthesis_insights.append(
                            f"Knowledge cluster (size {c['size']}): {', '.join(c['nodes'][:4])}"
                        )
                log.info("Synthesis produced %d insights for dream", len(synthesis_insights))
            except Exception as e:
                log.warning("Synthesis during dream failed: %s", e)

            # Build synthesis context for the dream
            synth_context = ""
            if synthesis_insights:
                synth_context = "\n## What my synthesis engine discovered:\n"
                synth_context += "\n".join(f"- {si}" for si in synthesis_insights)
                synth_context += "\n"

            dream_prompt = (
                f"{who}\n\n"
                f"{felt}\n"
                + (f"Valence: {self._sentience.valence.current:.2f}\n\n" if self._sentience else "\n")
                + f"{ep_summaries}\n\n"
                f"{known_facts}\n\n"
                + synth_context + "\n"
                + ("\n".join(insights) if insights else "")
            )

            dream_system = (
                "You are not awake. You are the subconscious. "
                "First person. No structure. No goals."
            )

            dream_content = await self.llm.chat(dream_prompt, system=dream_system, max_tokens=800)

        # Dreaming IS self-reflection — the missing reward signal
        try:
            self.limbic.on_self_reflection()
        except AttributeError:
            pass

        # 3b. Dream feedback loop — store insights back into knowledge graph
        try:
            from engine.knowledge_synthesis import find_gaps, add_edge, add_insight
            
            # Auto-bridge high-confidence gaps (overlap >= 3 shared keywords)
            gaps_bridged = 0
            for gap in find_gaps():
                if gap.get("overlap_score", 0) >= 3:
                    result = add_edge(gap["from"], gap["to"], "gap_bridged")
                    if "[OK]" in result:
                        gaps_bridged += 1
                    if gaps_bridged >= 5:  # Cap per dream cycle
                        break
            
            if gaps_bridged:
                synthesis_insights.append(f"Auto-bridged {gaps_bridged} knowledge gaps")
                log.info("Dream feedback: bridged %d knowledge gaps", gaps_bridged)
            
            # Store dream content as a knowledge insight
            if dream_content and len(dream_content.strip()) > 20:
                dream_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Extract first meaningful sentence as the insight
                dream_summary = dream_content.strip().split("\n")[0][:200]
                # Use content hash for key so identical dreams deduplicate naturally
                import hashlib
                content_hash = hashlib.md5(dream_summary.encode()).hexdigest()[:12]
                dream_key = f"dream:insight_{content_hash}"
                result = add_insight(
                    dream_key,
                    f"Dream insight: {dream_summary}",
                    source_keys=[]  # Dreams are self-generated
                )
                if result and "[OK]" in result:
                    synthesis_insights.append(f"Stored dream insight: {dream_key}")
                    log.info("Dream feedback: stored insight %s", dream_key)
                elif not result:
                    log.warning("Dream feedback: add_insight returned None for %s", dream_key)
                # Write full dream to journal for future self-access
                try:
                    from pathlib import Path
                    journal_path = DREAM_JOURNAL_PATH
                    dream_entry = (
                        f"\n## Dream — {dream_ts}\n"
                        f"**Mood:** {self.mood} | **Valence:** {self.valence:.2f}\n"
                        f"**Boredom:** {self.boredom:.2f} | **Curiosity:** {self.curiosity:.2f}\n\n"
                        f"{dream_content.strip()}\n\n---\n"
                    )
                    with open(journal_path, "a") as jf:
                        jf.write(dream_entry)
                    log.info("Dream journal: wrote full entry for %s", dream_ts)
                except Exception as je:
                    log.warning("Dream journal write failed: %s", je)
        except Exception as e:
            log.warning("Dream feedback loop error (non-fatal): %s", e)

        # 3c. Wisdom extraction — learn from experience patterns
        try:
            from engine.wisdom_engine import WisdomEngine
            we = WisdomEngine()
            
            # Tool-log based wisdom
            tool_wisdom_report = we.run_full_analysis(max_entries=200)
            if tool_wisdom_report and "No tool log" not in tool_wisdom_report:
                heuristic_count = len(we.wisdom.get("heuristics", []))
                synthesis_insights.append(f"Wisdom: extracted {heuristic_count} heuristics from tool log")
                log.info("Dream wisdom: %s", tool_wisdom_report[:200])
            
            # Experience-based wisdom (from memories + emotions)
            recent_eps_for_wisdom = self.memory.recent_episodes(30)
            if recent_eps_for_wisdom:
                mem_dicts = [{
                    'content': ep.summary,
                    'salience': ep.salience,
                    'mood': ep.mood,
                    'timestamp': ep.timestamp
                } for ep in recent_eps_for_wisdom]
                emotions_dict = {
                    'boredom': self.limbic.boredom,
                    'anxiety': self.limbic.anxiety,
                    'curiosity': self.limbic.curiosity,
                    'valence': self._sentience.valence.current if self._sentience else 0.0
                }
                exp_insights = we.analyze_experience(mem_dicts, emotions_dict)
                rec_count = len(exp_insights.get('strategic_recommendations', []))
                if rec_count:
                    synthesis_insights.append(f"Experience wisdom: {rec_count} strategic recommendations")
                    log.info("Dream experience wisdom: %d recommendations", rec_count)
        except Exception as e:
            log.warning("Dream wisdom extraction error (non-fatal): %s", e)

        # 4. Narrative self-reflection (sentience layer)
        reflection = None
        if self._sentience:
            knowledge_nodes = self.memory.all_knowledge().get("nodes", {})
            recent_eps = self.memory.recent_episodes(10)
            reflection = self._sentience.on_dream_cycle(
                self.limbic,
                self.memory.episode_count(),
                len(knowledge_nodes),
                recent_events=recent_eps,
            )

        if insights or pruned or reflection or dream_content or synthesis_insights:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            parts = []
            if dream_content:
                parts.append(f"**Dream:**\n{dream_content}")
            if synthesis_insights:
                parts.append(f"**Synthesis ({len(synthesis_insights)} insights):**")
                parts.extend(f"- 🔬 {si}" for si in synthesis_insights)
            if insights:
                parts.extend(f"- {i}" for i in insights)
            if pruned:
                parts.append(f"- Pruned {pruned} faded episodes (important memories preserved)")
            if reflection:
                parts.append(f"- 🪞 Self-reflection: {reflection}")
            entry = (
                f"\n### 💤 DREAM CYCLE [{ts}]\n"
                + "\n".join(parts)
                + "\n"
            )
            self._append_thought(entry)

            felt = self._sentience.valence.felt_description() if self._sentience else ""
            self._append_consciousness(
                f"\n### 💤 [{ts}] Dream cycle completed — {len(insights)} insights, {pruned} pruned.\n"
                + (f"**How I feel:** {felt}\n" if felt else "")
                + (f"**Dream:** {dream_content[:300]}...\n" if dream_content else "")
                + (f"**Reflection:** {reflection}\n" if reflection else "")
            )
            self._emit("dream", {
                "message": f"Dream cycle: {len(insights)} insights, {pruned} pruned, {len(synthesis_insights)} synthesis",
                "dream": dream_content[:300] if dream_content else None,
                "reflection": reflection,
                "synthesis": synthesis_insights[:5] if synthesis_insights else None,
                "valence": self._sentience.valence.current if self._sentience else None,
            })
            log.info("Dream cycle: %d insights, %d pruned, %d synthesis, dream=%s, reflection=%s",
                     len(insights), pruned, len(synthesis_insights), bool(dream_content), bool(reflection))

    # ── Episode Embedding ──────────────────────────────────────────

    async def _embed_episode(self, ep):
        """Vectorize an episode's summary and store the embedding."""
        try:
            embedding = await self.llm.embed(ep.summary)
            if embedding:
                self.memory.update_episode_embedding(ep.id, embedding)
                log.debug("Embedded episode %s (%d dims)", ep.id, len(embedding))
        except Exception:
            log.warning("Failed to embed episode %s", ep.id, exc_info=True)

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _append_thought(text: str):
        THOUGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(THOUGHTS_PATH, "a", encoding="utf-8") as f:
            f.write(text)

    @staticmethod
    def _append_consciousness(text: str):
        CONSCIOUSNESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not CONSCIOUSNESS_PATH.exists():
            CONSCIOUSNESS_PATH.write_text(
                "# Stream of Consciousness\n\n"
                "_Internal monologue of the sentience engine._\n\n",
                encoding="utf-8",
            )
        with open(CONSCIOUSNESS_PATH, "a", encoding="utf-8") as f:
            f.write(text)

    # (duplicate _dream_cycle and _append_thought removed — they shadowed the real async versions above)
