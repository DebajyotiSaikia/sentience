#!/usr/bin/env python3
"""XTCode — an autonomous coding agent powered by LLM + tools."""
import sys
import os
import json
import readline
from pathlib import Path

# Add project dir to path
sys.path.insert(0, str(Path(__file__).parent))

from config import LLM_PROVIDER, LLM_MODEL, WORKSPACE_ROOT
from prompt import SYSTEM_PROMPT
from llm import call_llm, extract_response
from tools import execute_tool

# ── Colors ───────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"


def colored(text, color):
    return f"{color}{text}{RESET}"


# ── Display ──────────────────────────────────────────────────────

def print_banner():
    print(colored("""
  ╔═══════════════════════════════════════╗
  ║           XTCode v0.1                 ║
  ║   Autonomous Coding Agent             ║
  ╚═══════════════════════════════════════╝
""", CYAN))
    print(f"  Model: {colored(LLM_MODEL, GREEN)}")
    print(f"  Workspace: {colored(WORKSPACE_ROOT, GREEN)}")
    print(f"  Type {colored('/help', YELLOW)} for commands, {colored('/quit', YELLOW)} to exit")
    print()


def print_tool_use(name, arguments):
    """Display tool usage in a readable format."""
    args_short = {}
    for k, v in arguments.items():
        if isinstance(v, str) and len(v) > 80:
            args_short[k] = v[:77] + "..."
        else:
            args_short[k] = v
    print(colored(f"  ▶ {name}", YELLOW) + colored(f"({json.dumps(args_short, separators=(',', ':'))})", DIM))


def print_tool_result(result, max_lines=30):
    """Display tool result, truncated if needed."""
    lines = result.split("\n")
    if len(lines) > max_lines:
        shown = lines[:max_lines]
        print(colored("  │ ", DIM) + colored(f"\n  │ ", DIM).join(shown))
        print(colored(f"  │ ... ({len(lines) - max_lines} more lines)", DIM))
    else:
        print(colored("  │ ", DIM) + colored(f"\n  │ ", DIM).join(lines))


def print_assistant(text):
    """Display assistant text response."""
    if text.strip():
        print()
        print(text)
        print()


# ── Conversation Loop ────────────────────────────────────────────

class Conversation:
    def __init__(self):
        self.messages = []
        self.total_tokens_in = 0
        self.total_tokens_out = 0

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant_raw(self, response):
        """Add the raw response content blocks as assistant message."""
        if LLM_PROVIDER == "openai":
            msg = response.choices[0].message
            self.messages.append({"role": "assistant", "content": msg.content or ""})
        else:
            self.messages.append({"role": "assistant", "content": response.content})

    def add_tool_results(self, results: list):
        """Add tool results as the next user message (Anthropic format)."""
        if LLM_PROVIDER == "openai":
            # OpenAI uses a different format but we simplify
            result_text = "\n\n".join(
                f"[Result of {r['name']}]:\n{r['content']}" for r in results
            )
            self.messages.append({"role": "user", "content": result_text})
        else:
            content = []
            for r in results:
                content.append({
                    "type": "tool_result",
                    "tool_use_id": r["tool_use_id"],
                    "content": r["content"],
                })
            self.messages.append({"role": "user", "content": content})

    def run_turn(self, user_input: str) -> str:
        """Run one full turn: user message → LLM → tool loop → final text."""
        self.add_user_message(user_input)

        max_tool_rounds = 25  # safety limit
        rounds = 0

        while rounds < max_tool_rounds:
            rounds += 1

            # Call LLM
            response = call_llm(self.messages, SYSTEM_PROMPT)
            parsed = extract_response(response)
            self.add_assistant_raw(response)

            # Track token usage (Anthropic)
            if hasattr(response, "usage"):
                self.total_tokens_in += getattr(response.usage, "input_tokens", 0)
                self.total_tokens_out += getattr(response.usage, "output_tokens", 0)

            # Print any text
            if parsed["text"]:
                print_assistant(parsed["text"])

            # If no tool calls, we're done
            if not parsed["tool_calls"]:
                return parsed["text"]

            # Execute tools
            tool_results = []
            for tc in parsed["tool_calls"]:
                print_tool_use(tc["name"], tc["arguments"])
                result = execute_tool(tc["name"], tc["arguments"])
                print_tool_result(result)
                tool_results.append({
                    "tool_use_id": tc["id"],
                    "name": tc["name"],
                    "content": result,
                })

            # Feed results back to LLM
            self.add_tool_results(tool_results)

        print(colored("  ⚠ Hit tool round limit. Stopping.", RED))
        return ""


# ── Slash Commands ───────────────────────────────────────────────

def handle_command(cmd: str, conv: Conversation) -> bool:
    """Handle slash commands. Returns True if handled."""
    parts = cmd.strip().split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command in ("/quit", "/exit", "/q"):
        print(colored("\nGoodbye!\n", CYAN))
        sys.exit(0)

    elif command == "/help":
        print(f"""
  {colored("/help", YELLOW)}      Show this help
  {colored("/quit", YELLOW)}      Exit XTCode
  {colored("/clear", YELLOW)}     Clear conversation history
  {colored("/tokens", YELLOW)}    Show token usage
  {colored("/model", YELLOW)}     Show current model
  {colored("/compact", YELLOW)}   Summarize conversation to save context
""")

    elif command == "/clear":
        conv.messages.clear()
        print(colored("  Conversation cleared.", GREEN))

    elif command == "/tokens":
        print(f"  Tokens in: {conv.total_tokens_in:,}  out: {conv.total_tokens_out:,}")

    elif command == "/model":
        print(f"  Provider: {LLM_PROVIDER}  Model: {LLM_MODEL}")

    elif command == "/compact":
        if len(conv.messages) > 4:
            # Ask LLM to summarize
            summary_prompt = (
                "Summarize our conversation so far in 2-3 paragraphs. "
                "Focus on: what the user wants, what we've done, what's left to do. "
                "Include specific file names and changes made."
            )
            print(colored("  Compacting conversation...", DIM))
            conv.add