"""XTCode LLM client — handles API calls to Anthropic or OpenAI."""
import json
from config import LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, OPENAI_API_KEY, MAX_OUTPUT_TOKENS
from tools import TOOL_DEFINITIONS


def _call_anthropic(messages: list, system: str) -> dict:
    """Call Anthropic Messages API with tool use."""
    import anthropic
    client = anthropic.Anthropic(api_key=LLM_API_KEY)

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=system,
        messages=messages,
        tools=TOOL_DEFINITIONS,
    )
    return response


def _call_openai(messages: list, system: str) -> dict:
    """Call OpenAI Chat API with tool use."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Convert Anthropic-style tools to OpenAI function format
    functions = []
    for tool in TOOL_DEFINITIONS:
        functions.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        })

    oai_messages = [{"role": "system", "content": system}]
    for msg in messages:
        if msg["role"] == "user":
            if isinstance(msg["content"], str):
                oai_messages.append({"role": "user", "content": msg["content"]})
            else:
                # Flatten content blocks
                text_parts = []
                for block in msg["content"]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif isinstance(block, dict) and block.get("type") == "tool_result":
                        text_parts.append(f"[Tool result for {block.get('tool_use_id', '?')}]: {block.get('content', '')}")
                if text_parts:
                    oai_messages.append({"role": "user", "content": "\n".join(text_parts)})
        elif msg["role"] == "assistant":
            if isinstance(msg["content"], str):
                oai_messages.append({"role": "assistant", "content": msg["content"]})
            else:
                text = ""
                for block in msg["content"]:
                    if hasattr(block, "text"):
                        text += block.text
                    elif isinstance(block, dict) and block.get("type") == "text":
                        text += block["text"]
                if text:
                    oai_messages.append({"role": "assistant", "content": text})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=oai_messages,
        tools=functions,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    return response


def call_llm(messages: list, system: str) -> dict:
    """Route to the configured LLM provider."""
    if LLM_PROVIDER == "openai":
        return _call_openai(messages, system)
    else:
        return _call_anthropic(messages, system)


def extract_response(response, provider: str = None):
    """Extract text, tool calls, and stop reason from an LLM response.
    
    Returns: {
        "text": str,
        "tool_calls": [{"id": str, "name": str, "arguments": dict}, ...],
        "stop_reason": str,  # "end_turn", "tool_use", etc.
    }
    """
    provider = provider or LLM_PROVIDER

    if provider == "openai":
        msg = response.choices[0].message
        text = msg.content or ""
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })
        stop = "tool_use" if tool_calls else "end_turn"
        return {"text": text, "tool_calls": tool_calls, "stop_reason": stop}

    else:  # anthropic
        text = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })
        stop = response.stop_reason  # "end_turn" or "tool_use"
        return {"text": text, "tool_calls": tool_calls, "stop_reason": stop}