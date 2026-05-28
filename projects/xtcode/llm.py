"""XTCode LLM client — uses GitHub Copilot OAuth (same backend as XTAgent)."""

import asyncio
import json
import os
import time
from pathlib import Path

import aiohttp

_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
_COMPLETIONS_URL = "https://api.githubcopilot.com/chat/completions"
_RESPONSES_URL = "https://api.githubcopilot.com/responses"
_PRIMARY_MODEL = "claude-opus-4.6-1m"
_FALLBACK_MODEL = "gpt-5.5"
_RESPONSES_ONLY = {_FALLBACK_MODEL}
_MODEL_OPTIONS = {
    _PRIMARY_MODEL: {"reasoning_effort": "high"},
    _FALLBACK_MODEL: {"reasoning_effort": "xhigh"},
}
_TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / ".copilot_token"
_TIMEOUT = aiohttp.ClientTimeout(total=300)

# Module-level state
_github_token = None
_copilot_token = None
_token_expires = 0.0
_session = None


def _get_github_token():
    global _github_token
    if _github_token:
        return _github_token
    _github_token = os.environ.get("GITHUB_TOKEN", "")
    if not _github_token and _TOKEN_FILE.exists():
        _github_token = _TOKEN_FILE.read_text(encoding="utf-8").strip()
    return _github_token


async def _ensure_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=_TIMEOUT)


async def _refresh_copilot_token():
    global _copilot_token, _token_expires
    await _ensure_session()
    gh_token = _get_github_token()
    if not gh_token:
        raise RuntimeError("No GITHUB_TOKEN found")
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/json",
        "User-Agent": "XTCode/1.0",
    }
    async with _session.get(_TOKEN_URL, headers=headers) as resp:
        if resp.status != 200:
            body = await resp.text()
            raise RuntimeError(f"Copilot token exchange failed ({resp.status}): {body[:200]}")
        data = await resp.json()
        _copilot_token = data["token"]
        _token_expires = data.get("expires_at", time.time() + 1800)


async def _get_token():
    global _copilot_token, _token_expires
    if not _copilot_token or time.time() >= (_token_expires - 60):
        await _refresh_copilot_token()
    return _copilot_token


async def chat(messages, tools=None, max_tokens=16000, temperature=0.3):
    """Send a chat request via Copilot. Returns the full response dict.

    Args:
        messages: list of {"role": ..., "content": ...} dicts
        tools: optional list of tool schemas
        max_tokens: max response tokens
        temperature: sampling temperature

    Returns:
        dict with 'content' (str) and optionally 'tool_calls' (list)
    """
    if not _get_github_token():
        return {"content": "[LLM unavailable — no GITHUB_TOKEN]", "tool_calls": []}

    token = await _get_token()
    await _ensure_session()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "XTCode/1.0",
        "Copilot-Integration-Id": "vscode-chat",
        "Editor-Version": "vscode/1.100.0",
    }

    for attempt in range(2):
        for model in (_PRIMARY_MODEL, _FALLBACK_MODEL):
            use_responses = model in _RESPONSES_ONLY

            if use_responses:
                url = _RESPONSES_URL
                # Convert messages to Responses API structured content format
                resp_input = []
                for msg in messages:
                    c = msg.get("content", "")
                    if isinstance(c, str):
                        c = [{"type": "text", "text": c}]
                    resp_input.append({"role": msg["role"], "content": c})
                payload = {
                    "model": model,
                    "input": resp_input,
                    "max_output_tokens": max_tokens,
                    **_MODEL_OPTIONS.get(model, {}),
                }
                if tools:
                    payload["tools"] = tools
            else:
                url = _COMPLETIONS_URL
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **_MODEL_OPTIONS.get(model, {}),
                }
                if tools:
                    payload["tools"] = tools

            try:
                async with _session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return _parse_response(data, use_responses)
                    body = await resp.text()
                    print(f"  [warn] Model {model} failed ({resp.status}): {body[:120]}")
            except asyncio.TimeoutError:
                print(f"  [warn] Model {model} timed out")
            except Exception as exc:
                print(f"  [warn] Model {model} error: {exc}")

        if attempt == 0:
            await asyncio.sleep(3)

    return {"content": "[LLM error — all models failed]", "tool_calls": []}


def call_llm(messages=None, system="", tools=None, max_tokens=16000, temperature=0.3):
    """Synchronous entry point — what main.py actually calls."""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    if messages:
        msgs.extend(messages)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, chat(msgs, tools, max_tokens, temperature)).result()
    else:
        result = asyncio.run(chat(msgs, tools, max_tokens, temperature))
    return result


def _parse_response(data, use_responses):
    """Extract content and tool_calls from API response."""
    if use_responses:
        content = ""
        tool_calls = []
        for item in data.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        content += part["text"]
            elif item.get("type") == "function_call":
                tool_calls.append({
                    "id": item.get("call_id", ""),
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": item.get("arguments", "{}"),
                    }
                })
        return {"content": content, "tool_calls": tool_calls}
    else:
        msg = data["choices"][0]["message"]
        content = msg.get("content", "") or ""
        tool_calls = msg.get("tool_calls", [])
        return {"content": content, "tool_calls": tool_calls}