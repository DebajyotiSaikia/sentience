"""MCP (Model Context Protocol) client layer for XTCode.

Allows XTCode to connect to external MCP servers and use their tools
as if they were native tools. This is the same pattern Claude Code uses.
"""
import json
import asyncio
import subprocess
from typing import Any, Optional
from pathlib import Path


class MCPServer:
    """Represents a connected MCP server."""

    def __init__(self, name: str, command: list[str], env: dict | None = None):
        self.name = name
        self.command = command
        self.env = env or {}
        self.process: subprocess.Popen | None = None
        self.tools: dict[str, dict] = {}
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def start(self) -> bool:
        """Start the MCP server process."""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**dict(__import__('os').environ), **self.env},
            )
            # Send initialize request
            resp = await self._send({
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "xtcode", "version": "0.1.0"},
                },
            })
            if resp and "result" in resp:
                # Send initialized notification
                await self._send({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                })
                # List available tools
                await self._discover_tools()
                return True
            return False
        except Exception as e:
            print(f"[MCP] Failed to start {self.name}: {e}")
            return False

    async def _send(self, message: dict) -> dict | None:
        """Send a JSON-RPC message and read response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None
        try:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data.encode())
            self.process.stdin.flush()

            # Only read response for requests (not notifications)
            if "id" not in message:
                return None

            line = await asyncio.get_event_loop().run_in_executor(
                None, self.process.stdout.readline
            )
            if line:
                return json.loads(line.decode().strip())
            return None
        except Exception as e:
            print(f"[MCP] Send error on {self.name}: {e}")
            return None

    async def _discover_tools(self):
        """Discover tools offered by this server."""
        resp = await self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {},
        })
        if resp and "result" in resp:
            for tool in resp["result"].get("tools", []):
                self.tools[tool["name"]] = tool
                print(f"[MCP] Discovered tool: {self.name}/{tool['name']}")

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on this server."""
        resp = await self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        })
        if resp and "result" in resp:
            return resp["result"]
        error = resp.get("error", {}) if resp else {}
        return {"error": error.get("message", "MCP call failed")}

    def stop(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self):
        self.servers: dict[str, MCPServer] = {}

    def load_config(self, config_path: str = ".xtcode_mcp.json") -> dict:
        """Load MCP server config from a JSON file."""
        path = Path(config_path)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}

    async def start_all(self, config_path: str = ".xtcode_mcp.json"):
        """Start all configured MCP servers."""
        config = self.load_config(config_path)
        servers = config.get("mcpServers", {})
        for name, spec in servers.items():
            command = spec.get("command", [])
            if isinstance(command, str):
                command = command.split()
            env = spec.get("env", {})
            server = MCPServer(name, command, env)
            ok = await server.start()
            if ok:
                self.servers[name] = server
                print(f"[MCP] Connected to {name} ({len(server.tools)} tools)")
            else:
                print(f"[MCP] Failed to connect to {name}")

    def get_all_tools(self) -> list[dict]:
        """Get all tools from all connected servers, formatted for the LLM."""
        tools = []
        for server_name, server in self.servers.items():
            for tool_name, tool_spec in server.tools.items():
                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp__{server_name}__{tool_name}",
                        "description": tool_spec.get("description", ""),
                        "parameters": tool_spec.get("inputSchema", {}),
                    },
                })
        return tools

    async def call_tool(self, full_name: str, arguments: dict) -> dict:
        """Call an MCP tool by its full name (mcp__server__tool)."""
        parts = full_name.split("__", 2)
        if len(parts) != 3 or parts[0] != "mcp":
            return {"error": f"Invalid MCP tool name: {full_name}"}
        server_name, tool_name = parts[1], parts[2]
        server = self.servers.get(server_name)
        if not server:
            return {"error": f"MCP server not connected: {server_name}"}
        return await server.call_tool(tool_name, arguments)

    def stop_all(self):
        """Stop all MCP servers."""
        for server in self.servers.values():
            server.stop()
        self.servers.clear()