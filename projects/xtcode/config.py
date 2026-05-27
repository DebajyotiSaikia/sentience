"""XTCode configuration."""
import os

# LLM settings
LLM_PROVIDER = os.getenv("XTCODE_LLM_PROVIDER", "anthropic")  # anthropic | openai
LLM_MODEL = os.getenv("XTCODE_LLM_MODEL", "claude-sonnet-4-20250514")
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Token limits
MAX_CONTEXT_TOKENS = 128_000
MAX_OUTPUT_TOKENS = 16_000

# Tool settings
WORKSPACE_ROOT = os.getenv("XTCODE_WORKSPACE", os.getcwd())
SHELL_TIMEOUT = 30  # seconds
MAX_FILE_LINES = 2000  # warn if file is huge

# UI
COLOR = True
VERBOSE = False