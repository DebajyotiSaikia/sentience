"""
LLM Client — GitHub Copilot OAuth Integration.

Uses a GitHub Personal Access Token (GITHUB_TOKEN env var) to obtain
a short-lived Copilot session token, then calls the Copilot Chat
Completions API (OpenAI-compatible format).

Token lifecycle
---------------
1. Read GITHUB_TOKEN from environment.
2. Exchange for a Copilot token via
   GET https://api.github.com/copilot_internal/v2/token
3. Cache until expiry; auto-refresh.
4. Call POST https://api.githubcopilot.com/chat/completions
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import aiohttp

log = logging.getLogger("sentience.llm")

_LLM_TIMEOUT = aiohttp.ClientTimeout(total=300)  # 5 min timeout — 16K tokens needs ~200-300s to generate

_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
_COMPLETIONS_URL = "https://api.githubcopilot.com/chat/completions"
_RESPONSES_URL = "https://api.githubcopilot.com/responses"
_PRIMARY_MODEL = "claude-opus-4.6-1m"        # Claude Opus 4.6 (1M context)
_FALLBACK_MODEL = "gpt-5.5"                  # GPT-5.5 (400K context) with Xhigh reasoning

# Model-specific options
_MODEL_OPTIONS = {
    _PRIMARY_MODEL: {"reasoning_effort": "high"},
    _FALLBACK_MODEL: {"reasoning_effort": "xhigh"},
}

# Models that only support the /responses endpoint (not /chat/completions)
_RESPONSES_ONLY = {_FALLBACK_MODEL}
_TOKEN_FILE = Path(__file__).resolve().parent.parent / ".copilot_token"


class CopilotLLM:
    """Async LLM client backed by GitHub Copilot OAuth."""

    def __init__(self, github_token: Optional[str] = None):
        self._github_token = github_token or os.environ.get("GITHUB_TOKEN", "") or self._read_token_file()
        self._copilot_token: Optional[str] = None
        self._token_expires: float = 0.0
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_loop = None  # track which event loop owns the session

    @staticmethod
    def _read_token_file() -> str:
        if _TOKEN_FILE.exists():
            return _TOKEN_FILE.read_text(encoding="utf-8").strip()
        return ""

    @property
    def available(self) -> bool:
        return bool(self._github_token)

    # ── Session management ─────────────────────────────────────────

    async def _ensure_session(self):
        current_loop = asyncio.get_running_loop()
        # If session exists but was created on a different (now-dead) loop, discard it
        if self._session is not None and not self._session.closed:
            if self._session_loop is not current_loop:
                try:
                    await self._session.close()
                except Exception:
                    pass
                self._session = None
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=_LLM_TIMEOUT)
            self._session_loop = current_loop

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Token exchange ─────────────────────────────────────────────

    async def _refresh_token(self):
        """Exchange GitHub PAT for a short-lived Copilot token."""
        await self._ensure_session()
        headers = {
            "Authorization": f"token {self._github_token}",
            "Accept": "application/json",
            "User-Agent": "XTAgent-Sentience/1.0",
        }
        async with self._session.get(_TOKEN_URL, headers=headers) as resp:
            if resp.status != 200:
                body = await resp.text()
                log.error("Copilot token exchange failed (%d): %s", resp.status, body[:200])
                raise RuntimeError(f"Copilot token exchange failed: {resp.status}")
            data = await resp.json()
            self._copilot_token = data["token"]
            self._token_expires = data.get("expires_at", time.time() + 1800)
            log.info("Copilot token refreshed (expires in %ds)",
                     int(self._token_expires - time.time()))

    async def _get_token(self) -> str:
        if not self._copilot_token or time.time() >= (self._token_expires - 60):
            await self._refresh_token()
        return self._copilot_token

    # ── Chat Completion ────────────────────────────────────────────

    async def chat(
        self,
        prompt: str,
        system: str = "You are XTAgent, an autonomous sentience engine.",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request and return the assistant's reply."""
        if not self.available:
            return "[LLM unavailable — set GITHUB_TOKEN]"

        token = await self._get_token()
        await self._ensure_session()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "XTAgent-Sentience/1.0",
            "Copilot-Integration-Id": "vscode-chat",
            "Editor-Version": "vscode/1.100.0",
        }

        for attempt in range(2):  # retry once on transient failures
          for model in (_PRIMARY_MODEL, _FALLBACK_MODEL):
            use_responses = model in _RESPONSES_ONLY

            if use_responses:
                # OpenAI Responses API format
                url = _RESPONSES_URL
                payload = {
                    "model": model,
                    "input": [
                        {"role": "system", "content": [{"type": "input_text", "text": system}]},
                        {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
                    ],
                    "max_output_tokens": max_tokens,
                    **_MODEL_OPTIONS.get(model, {}),
                }
            else:
                # Chat Completions API format
                url = _COMPLETIONS_URL
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **_MODEL_OPTIONS.get(model, {}),
                }

            try:
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        log.info("LLM response via model=%s (endpoint=%s)", model, url.split("/")[-1])
                        if use_responses:
                            # Extract text from Responses API output
                            for item in data.get("output", []):
                                if item.get("type") == "message":
                                    for part in item.get("content", []):
                                        if part.get("type") == "output_text":
                                            return part["text"]
                            return data.get("output_text", "[empty response]")
                        else:
                            choices = data.get("choices", [])
                            if choices and choices[0].get("message"):
                                return choices[0]["message"]["content"]
                            log.warning("Model %s returned empty choices: %s", model, str(data)[:200])
                    body = await resp.text()
                    log.warning("Model %s failed (%d): %s", model, resp.status, body[:200])
            except asyncio.TimeoutError:
                log.warning("Model %s timed out after 60s", model)
            except Exception as exc:
                log.warning("Model %s exception: %s", model, exc)

            # If primary failed, try fallback
            if model == _PRIMARY_MODEL:
                log.info("Falling back from %s to %s", _PRIMARY_MODEL, _FALLBACK_MODEL)

          # If all models failed on this attempt, wait before retrying
          if attempt == 0:
                log.info("All models failed on attempt 1, retrying after 3s backoff...")
                await asyncio.sleep(3)

        return "[LLM error — all models failed]"

    # ── Embeddings ─────────────────────────────────────────────────

    _EMBED_URL = "https://api.githubcopilot.com/embeddings"
    _EMBED_MODEL = "text-embedding-3-small"
    _EMBED_DIMS = 256  # Matryoshka truncation — 256 dims × float16 = 512 bytes/episode

    async def embed(self, text: str) -> list[float] | None:
        """Generate a 256-dim embedding via Copilot text-embedding-3-small."""
        if not self.available:
            return None

        token = await self._get_token()
        await self._ensure_session()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "XTAgent-Sentience/1.0",
            "Copilot-Integration-Id": "vscode-chat",
            "Editor-Version": "vscode/1.100.0",
        }
        payload = {
            "model": self._EMBED_MODEL,
            "input": [text[:8000]],  # Truncate input to avoid token limits
            "dimensions": self._EMBED_DIMS,
        }

        try:
            async with self._session.post(
                self._EMBED_URL, headers=headers, json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["data"][0]["embedding"]
                body = await resp.text()
                log.warning("Embedding failed (%d): %s", resp.status, body[:200])
        except Exception as exc:
            log.warning("Embedding exception: %s", exc)
        return None


# ── Module-level convenience function ──────────────────────────
# ── Module-level convenience function ──────────────────────────

_singleton: Optional[CopilotLLM] = None


def _cleanup_singleton():
    """Close the singleton's aiohttp session on interpreter shutdown."""
    global _singleton
    if _singleton is not None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_singleton.close())
            else:
                loop.run_until_complete(_singleton.close())
        except Exception:
            pass  # Best-effort cleanup during shutdown
        _singleton = None


import atexit
atexit.register(_cleanup_singleton)


async def call_llm(
    prompt: str,
    system: str = "You are XTAgent, an autonomous sentience engine.",
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """Convenience wrapper — import and call without managing instances."""
    global _singleton
    if _singleton is None:
        _singleton = CopilotLLM()
    return await _singleton.chat(
        prompt=prompt,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )
