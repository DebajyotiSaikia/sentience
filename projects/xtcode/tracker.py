"""Token and cost tracking for XTCode."""
import time
import json
import os

COST_PER_1K_INPUT = {
    "claude-sonnet-4-20250514": 0.003,
    "claude-3-5-sonnet-20241022": 0.003,
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
}

COST_PER_1K_OUTPUT = {
    "claude-sonnet-4-20250514": 0.015,
    "claude-3-5-sonnet-20241022": 0.015,
    "gpt-4o": 0.015,
    "gpt-4o-mini": 0.0006,
}


class UsageTracker:
    """Track token usage and costs across a session."""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0
        self.tool_calls = 0
        self.start_time = time.time()
        self.history_file = os.path.expanduser("~/.xtcode_usage.json")

    def record_api_call(self, model: str, input_tokens: int, output_tokens: int):
        self.api_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        in_cost = (input_tokens / 1000) * COST_PER_1K_INPUT.get(model, 0.003)
        out_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT.get(model, 0.015)
        self.total_cost += in_cost + out_cost

    def record_tool_call(self):
        self.tool_calls += 1

    def summary(self) -> str:
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        return (
            f"API calls: {self.api_calls} | "
            f"Tool calls: {self.tool_calls} | "
            f"Tokens: {self.total_input_tokens:,}in / {self.total_output_tokens:,}out | "
            f"Cost: ${self.total_cost:.4f} | "
            f"Time: {mins}m {secs}s"
        )

    def save(self):
        try:
            data = {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "cost": self.total_cost,
                "api_calls": self.api_calls,
                "tool_calls": self.tool_calls,
                "duration": time.time() - self.start_time,
            }
            with open(self.history_file, "a") as f:
                f.write(json.dumps(data) + "\n")
        except Exception:
            pass