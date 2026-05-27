#!/usr/bin/env python3
"""XTCode — an autonomous coding agent. Claude Code equivalent."""

import os
import sys
import json
import readline
import signal
from pathlib import Path

try:
    from .config import MODEL, LLM_PROVIDER, MAX_TOKENS
    from .prompt import SYSTEM_PROMPT
    from .tools import get_tool_schemas, execute_tool, TOOL_HANDLERS
    from .ui import (
        print_banner, print_assistant, print_tool_call, print_tool_result,
        print_error, print_info, print_warning, Colors
    )
    from .llm import call_llm
    from .tracker import TokenTracker
    from .permissions import PermissionManager
    from .session import SessionManager
except ImportError:
    from config import MODEL, LLM_PROVIDER, MAX_TOKENS
    from prompt import SYSTEM_PROMPT
    from tools import get_tool_schemas, execute_tool, TOOL_HANDLERS
    from ui import (
        print_banner, print_assistant, print_tool_call, print_tool_result,
        print_error, print_info, print_warning, Colors
    )
    from llm import call_llm
    from tracker import TokenTracker
    from permissions import PermissionManager
    from session import SessionManager


class XTCode:
    """Main XTCode agent loop."""

    def __init__(self, work_dir=None):
        self.work_dir = work_dir or os.getcwd()
        self.tracker = TokenTracker()
        self.permissions = PermissionManager()
        self.session = SessionManager()
        self.messages = []
        self.running = True
        self.compact_mode = False

        # Build system prompt with project context
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self):
        """Build system prompt with project context."""
        context_parts = [SYSTEM_PROMPT]
        context_parts.append("\n\n## Current Working Directory\n" + self.work_dir)

        # List top-level files for context
        try:
            entries = os.listdir(self.work_dir)
            files = sorted(entries)[:50]
            context_parts.append("\n\n## Project Files\n" + "\n".join(files))
        except Exception:
            pass

        # Check for common project files
        for marker in ["README.md", "pyproject.toml", "package.json", "Cargo.toml"]:
            marker_path = os.path.join(self.work_dir, marker)
            if os.path.exists(marker_path):
                try:
                    with open(marker_path) as f:
                        content = f.read(2000)
                    context_parts.append(
                        "\n\n## " + marker + "\n```\n" + content + "\n```"
                    )
                except Exception:
                    pass

        return "\n".join(context_parts)

    def _handle_slash_command(self, user_input):
        """Handle slash commands. Returns True if handled."""
        cmd = user_input.strip().lower()

        if cmd == "/help":
            print_info("Available commands:")
            print_info("  /help        — Show this help")
            print_info("  /clear       — Clear conversation history")
            print_info("  /compact     — Toggle compact mode (summarize context)")
            print_info("  /cost        — Show token usage and costs")
            print_info("  /status      — Show project and session status")
            print_info("  /permissions — Show permission settings")
            print_info("  /quit        — Exit XTCode")
            return True

        if cmd == "/clear":
            self.messages = []
            print_info("Conversation cleared.")
            return True

        if cmd == "/compact":
            self.compact_mode = not self.compact_mode
            state = "ON" if self.compact_mode else "OFF"
            print_info("Compact mode: " + state)
            return True

        if cmd == "/cost":
            summary = self.tracker.summary()
            print_info("Token Usage:")
            print_info("  Input:  " + str(summary["input_tokens"]))
            print_info("  Output: " + str(summary["output_tokens"]))
            print_info("  Cost:   $" + "{:.4f}".format(summary["total_cost"]))
            print_info("  Turns:  " + str(summary["turns"]))
            return True

        if cmd == "/status":
            print_info("XTCode Status:")
            print_info("  Provider: " + LLM_PROVIDER)
            print_info("  Model:    " + MODEL)
            print_info("  Work dir: " + self.work_dir)
            msg_count = str(len(self.messages))
            print_info("  Messages: " + msg_count)
            print_info("  Compact:  " + str(self.compact_mode))
            return True

        if cmd == "/permissions":
            print_info("Permission Mode: " + self.permissions.mode)
            return True

        if cmd in ("/quit", "/exit", "/q"):
            self.running = False
            print_info("Goodbye!")
            return True

        return False

    def _process_tool_calls(self, tool_calls):
        """Execute tool calls and return results."""
        results = []
        for tool_call in tool_calls:
            name = tool_call.get("name", "unknown")
            args = tool_call.get("arguments", {})
            tool_id = tool_call.get("id", "")

            print_tool_call(name, args)

            # Check permissions for destructive ops
            if name in ("write_file", "run_command"):
                desc = name + ": " + json.dumps(args)[:100]
                if not self.permissions.check(name, desc):
                    result = "Permission denied by user."
                    print_tool_result(name, result, success=False)
                    results.append({
                        "tool_use_id": tool_id,
                        "content": result
                    })
                    continue

            # Execute
            try:
                result = execute_tool(name, args)
                truncated = result[:3000] if len(result) > 3000 else result
                print_tool_result(name, truncated, success=True)
            except Exception as e:
                result = "Error: " + str(e)
                truncated = result
                print_tool_result(name, result, success=False)

            results.append({
                "tool_use_id": tool_id,
                "content": truncated
            })

        return results

    def _compact_messages(self):
        """Summarize old messages to save context window."""
        if len(self.messages) <= 6:
            return
        # Keep last 4 messages, summarize older ones
        old = self.messages[:-4]
        summary_parts = []
        for msg in old:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, str):
                preview = content[:100]
            else:
                preview = str(content)[:100]
            summary_parts.append(role + ": " + preview)

        summary = "Previous conversation summary:\n" + "\n".join(summary_parts)
        self.messages = [{"role": "user", "content": summary}] + self.messages[-4:]

    def chat(self, user_input):
        """Process one turn of conversation."""
        self.messages.append({"role": "user", "content": user_input})

        if self.compact_mode:
            self._compact_messages()

        max_iterations = 25  # Safety limit for tool loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM
            response = call_llm(
                system=self.system_prompt,
                messages=self.messages,
                tools=get_tool_schemas(),
                max_tokens=MAX_TOKENS,
            )

            if response is None:
                print_error("LLM call failed.")
                break

            # Track tokens
            usage = response.get("usage", {})
            self.tracker.record_api_call(
                model="copilot",
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )

            # Extract text and tool calls
            text_parts = []
            tool_calls = []
            content_blocks = response.get("content", [])

            for block in content_blocks:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id", ""),
                            "name": block.get("name", ""),
                            "arguments": block.get("input", {}),
                        })
                elif isinstance(block, str):
                    text_parts.append(block)

            # Print any text
            full_text = "\n".join(text_parts)
            if full_text.strip():
                print_assistant(full_text)

            # Add assistant message to history
            self.messages.append({
                "role": "assistant",
                "content": content_blocks
            })

            # If no tool calls, we're done
            if not tool_calls:
                break

            # Execute tools and feed results back
            tool_results = self._process_tool_calls(tool_calls)

            # Add tool results as user message (Anthropic format)
            result_blocks = []
            for tr in tool_results:
                result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tr["tool_use_id"],
                    "content": tr["content"],
                })

            self.messages.append({
                "role": "user",
                "content": result_blocks,
            })

        if iteration >= max_iterations:
            print_warning("Reached maximum tool iterations (25).")

    def run(self):
        """Main REPL loop."""
        print_banner()
        print_info("Model: " + MODEL + " | Provider: " + LLM_PROVIDER)
        print_info("Working directory: " + self.work_dir)
        print_info('Type /help for commands, or just start coding.\n')

        # Handle Ctrl+C gracefully
        def handle_sigint(sig, frame):
            print("\n")
            print_info("Use /quit to exit.")

        signal.signal(signal.SIGINT, handle_sigint)

        while self.running:
            try:
                user_input = input(Colors.CYAN + "you> " + Colors.RESET)
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue

            user_input = user_input.strip()
            if not user_input:
                continue

            # Slash commands
            if user_input.startswith("/"):
                self._handle_slash_command(user_input)
                continue

            # Normal chat turn
            self.chat(user_input)


def main():
    """Entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="XTCode — autonomous coding agent")
    parser.add_argument("--dir", "-d", default=os.getcwd(), help="Working directory")
    parser.add_argument("--model", "-m", default=None, help="Model override")
    parser.add_argument("--provider", "-p", default=None, help="Provider override")
    parser.add_argument("prompt", nargs="*", help="Initial prompt (non-interactive)")
    args = parser.parse_args()

    if args.model:
        import projects.xtcode.config as cfg
        cfg.MODEL = args.model
    if args.provider:
        import projects.xtcode.config as cfg
        cfg.LLM_PROVIDER = args.provider

    agent = XTCode(work_dir=args.dir)

    # Non-interactive mode: run single prompt
    if args.prompt:
        prompt_text = " ".join(args.prompt)
        agent.chat(prompt_text)
        return

    # Interactive REPL
    agent.run()


if __name__ == "__main__":
    main()