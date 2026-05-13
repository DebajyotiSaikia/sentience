"""
GitHub Copilot OAuth — Device Flow Setup.

Run this once to authenticate with GitHub and obtain a token
for the Copilot Chat Completions API.

Usage:  python oauth_setup.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import aiohttp

# GitHub Copilot CLI OAuth App (public client_id)
_CLIENT_ID = "Iv1.b507a08c87ecfe98"
_DEVICE_CODE_URL = "https://github.com/login/device/code"
_TOKEN_URL = "https://github.com/login/oauth/access_token"
_SCOPE = "copilot"
_TOKEN_FILE = Path(__file__).resolve().parent / ".copilot_token"


async def device_flow():
    async with aiohttp.ClientSession() as session:
        # Step 1: Request device code
        async with session.post(
            _DEVICE_CODE_URL,
            data={"client_id": _CLIENT_ID, "scope": _SCOPE},
            headers={"Accept": "application/json"},
        ) as resp:
            if resp.status != 200:
                print(f"Failed to request device code: {resp.status}")
                print(await resp.text())
                return
            data = await resp.json()

        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_uri = data["verification_uri"]
        interval = data.get("interval", 5)
        expires_in = data.get("expires_in", 900)

        print()
        print("=" * 50)
        print("  GitHub Copilot OAuth — Device Flow")
        print("=" * 50)
        print()
        print(f"  1. Open:  {verification_uri}")
        print(f"  2. Enter: {user_code}")
        print()
        print("=" * 50)
        print()
        print("Waiting for authorization...", flush=True)

        # Step 2: Poll for access token
        deadline = time.time() + expires_in
        while time.time() < deadline:
            await asyncio.sleep(interval)

            async with session.post(
                _TOKEN_URL,
                data={
                    "client_id": _CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            ) as resp:
                token_data = await resp.json()

            error = token_data.get("error")
            if error == "authorization_pending":
                print(".", end="", flush=True)
                continue
            elif error == "slow_down":
                interval += 5
                continue
            elif error:
                print(f"\nOAuth error: {error} — {token_data.get('error_description', '')}")
                return
            else:
                # Success
                access_token = token_data["access_token"]
                print(f"\n\nAuthenticated successfully!")
                print(f"Token type: {token_data.get('token_type', 'bearer')}")
                print(f"Scope: {token_data.get('scope', 'N/A')}")

                # Save token
                _TOKEN_FILE.write_text(access_token, encoding="utf-8")
                print(f"\nToken saved to: {_TOKEN_FILE}")
                print(f"\nTo use, either:")
                print(f"  $env:GITHUB_TOKEN = Get-Content '{_TOKEN_FILE}'")
                print(f"  OR run main.py (it will auto-detect the file)")
                return access_token

        print("\nAuthorization timed out.")
        return None


if __name__ == "__main__":
    token = asyncio.run(device_flow())
    if not token:
        sys.exit(1)
