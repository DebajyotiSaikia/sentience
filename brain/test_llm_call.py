"""Diagnose LLM API call failures — see the actual error body."""
import asyncio
import sys
import os
import json

# Ensure we can import from workspace root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_raw_http():
    """Make raw HTTP calls to see exact error responses."""
    import aiohttp
    
    # Get token the same way llm.py does
    token_url = "http://localhost:15432/v1/token"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(token_url) as resp:
                data = await resp.json()
                token = data.get("token")
                if not token:
                    print(f"No token from {token_url}: {data}")
                    return
                print(f"Token obtained: {token[:20]}...")
        except Exception as e:
            print(f"Token fetch failed: {e}")
            return
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        completions_url = "https://api.githubcopilot.com/chat/completions"
        
        # Test 1: Plain string content (standard OpenAI format)
        payload1 = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Say hello in one word."},
            ],
            "max_tokens": 50,
            "temperature": 0.7,
        }
        
        print("\n=== Test 1: Completions with plain string content ===")
        try:
            async with session.post(completions_url, json=payload1, headers=headers) as resp:
                status = resp.status
                body = await resp.text()
                print(f"Status: {status}")
                if status == 200:
                    result = json.loads(body)
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"Response: {content}")
                else:
                    print(f"Error body: {body[:500]}")
        except Exception as e:
            print(f"Request failed: {e}")
        
        # Test 2: Responses API endpoint
        responses_url = "https://api.githubcopilot.com/chat/completions"  # same endpoint
        payload2 = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Say hello in one word."},
            ],
            "max_tokens": 50,
        }
        
        print("\n=== Test 2: Minimal completions payload ===")
        try:
            async with session.post(responses_url, json=payload2, headers=headers) as resp:
                status = resp.status
                body = await resp.text()
                print(f"Status: {status}")
                if status == 200:
                    result = json.loads(body)
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"Response: {content}")
                else:
                    print(f"Error body: {body[:500]}")
        except Exception as e:
            print(f"Request failed: {e}")

async def test_call_llm():
    """Test via the public call_llm interface."""
    from engine.llm import call_llm
    
    print("\n=== Test 3: call_llm public API ===")
    try:
        result = await call_llm("Say hello in one word.", system="You are helpful.")
        print(f"SUCCESS: {result[:200]}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

async def main():
    await test_raw_http()
    await test_call_llm()

if __name__ == "__main__":
    asyncio.run(main())