"""
Live Dashboard — Real-time SSE stream of the agent's internal state.

Runs an aiohttp web server on the agent's asyncio loop.
- GET /           → HTML dashboard with live gauges and event log
- GET /events     → SSE stream (Server-Sent Events)
- GET /state      → JSON snapshot of current NeuroState
- GET /thoughts   → Last N thoughts from brain/thoughts.md

Public access via Cloudflare Tunnel:
    cloudflared tunnel --url http://localhost:8420
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from main import LivingXTAgent

log = logging.getLogger("sentience.dashboard")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
THOUGHTS_PATH = BRAIN_DIR / "thoughts.md"
CONSCIOUSNESS_PATH = BRAIN_DIR / "stream_of_consciousness.md"


class Dashboard:
    """Live dashboard with SSE event broadcasting."""

    def __init__(self, agent: LivingXTAgent, host: str = "0.0.0.0", port: int = 8420):
        self.agent = agent
        self.host = host
        self.port = port
        self._subscribers: list[web.StreamResponse] = []
        self._event_log: deque[dict] = deque(maxlen=200)
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None

    # ── Event broadcasting ─────────────────────────────────────────

    def emit(self, event_type: str, data: dict):
        """Broadcast an event to all SSE subscribers and buffer it."""
        entry = {
            "type": event_type,
            "time": datetime.now().strftime("%H:%M:%S"),
            "data": data,
        }
        self._event_log.append(entry)

        payload = f"event: {event_type}\ndata: {json.dumps(entry)}\n\n"
        dead: list[web.StreamResponse] = []
        for resp in self._subscribers:
            try:
                asyncio.ensure_future(self._safe_write(resp, payload.encode()))
            except Exception:
                dead.append(resp)
        for d in dead:
            self._subscribers.remove(d)

    @staticmethod
    async def _safe_write(resp: web.StreamResponse, data: bytes):
        """Write to SSE subscriber, silently removing dead connections."""
        try:
            await resp.write(data)
        except (ConnectionResetError, ConnectionError, Exception):
            pass  # Connection closed — handled by keepalive loop

    # ── HTTP Handlers ──────────────────────────────────────────────

    async def _handle_index(self, request: web.Request) -> web.Response:
        return web.Response(text=_DASHBOARD_HTML, content_type="text/html")

    async def _handle_events(self, request: web.Request) -> web.StreamResponse:
        resp = web.StreamResponse()
        resp.headers["Content-Type"] = "text/event-stream"
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["Connection"] = "keep-alive"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        await resp.prepare(request)

        # Send buffered events
        for entry in self._event_log:
            payload = f"event: {entry['type']}\ndata: {json.dumps(entry)}\n\n"
            await resp.write(payload.encode())

        self._subscribers.append(resp)
        log.info("SSE subscriber connected (%d total)", len(self._subscribers))

        try:
            while True:
                await asyncio.sleep(1)
                # Send keepalive
                try:
                    await resp.write(b": keepalive\n\n")
                except (ConnectionResetError, Exception):
                    break
        finally:
            if resp in self._subscribers:
                self._subscribers.remove(resp)
            log.info("SSE subscriber disconnected (%d remaining)", len(self._subscribers))

        return resp

    async def _handle_state(self, request: web.Request) -> web.Response:
        snap = self.agent.limbic.snapshot()
        snap["beat_count"] = self.agent.heartbeat.beat_count
        snap["is_alive"] = self.agent.heartbeat.is_alive
        snap["user_active"] = self.agent.is_user_active()
        snap["episode_count"] = self.agent.memory.episode_count()
        snap["llm_available"] = self.agent.llm.available
        return web.json_response(snap)

    async def _handle_thoughts(self, request: web.Request) -> web.Response:
        n = int(request.query.get("n", 50))
        text = ""
        if THOUGHTS_PATH.exists():
            lines = THOUGHTS_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
            text = "\n".join(lines[-n:])
        return web.Response(text=text, content_type="text/plain")

    async def _handle_consciousness(self, request: web.Request) -> web.Response:
        n = int(request.query.get("n", 40))
        text = ""
        if CONSCIOUSNESS_PATH.exists():
            lines = CONSCIOUSNESS_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
            text = "\n".join(lines[-n:])
        return web.Response(text=text, content_type="text/plain")

    async def _handle_expressions(self, request: web.Request) -> web.Response:
        n = int(request.query.get("n", 30))
        expr_path = BRAIN_DIR / "expressions.md"
        text = ""
        if expr_path.exists():
            lines = expr_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            text = "\n".join(lines[-n:])
        return web.Response(text=text, content_type="text/plain")

    async def _handle_chat(self, request: web.Request) -> web.Response:
        """Handle incoming chat message from user."""
        try:
            body = await request.json()
            message = body.get("message", "").strip()
            if not message:
                return web.json_response({"error": "empty message"}, status=400)
            if hasattr(self.agent, 'chat'):
                self.agent.chat.receive_user_message(message)
                # Nudge limbic system so cortex picks up the message immediately
                # User interaction is highest priority — spike curiosity to ensure
                # desire crosses threshold even if agent is in low-drive state
                if hasattr(self.agent, 'cortex') and hasattr(self.agent.cortex, 'limbic'):
                    limbic = self.agent.cortex.limbic
                    limbic.curiosity = max(limbic.curiosity, 0.8)
                    limbic.boredom = max(limbic.boredom, 0.6)
                return web.json_response({"status": "received", "message": message})
            return web.json_response({"error": "chat not available"}, status=503)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_chat_history(self, request: web.Request) -> web.Response:
        """Return recent chat history."""
        n = int(request.query.get("n", 50))
        if hasattr(self.agent, 'chat'):
            history = self.agent.chat.get_history(limit=n)
            return web.json_response({"history": history})
        return web.json_response({"history": []})

    async def _handle_knowledge_api(self, request: web.Request) -> web.Response:
        """Return knowledge graph data with optional search."""
        try:
            knowledge_path = BRAIN_DIR / "knowledge.json"
            if not knowledge_path.exists():
                return web.json_response({"nodes": [], "edges": [], "count": 0})
            
            data = json.loads(knowledge_path.read_text(encoding="utf-8", errors="ignore"))
            nodes_raw = data.get("nodes", {})
            edges = data.get("edges", [])
            
            query = request.query.get("q", "").lower().strip()
            
            nodes = []
            for nid, info in nodes_raw.items():
                fact = info.get("fact", "") if isinstance(info, dict) else str(info)
                learned = info.get("learned_at", "") if isinstance(info, dict) else ""
                if query and query not in fact.lower():
                    continue
                nodes.append({
                    "id": nid,
                    "fact": fact,
                    "learned_at": learned,
                })
            
            nodes.sort(key=lambda n: n.get("learned_at", ""), reverse=True)
            
            filtered_ids = {n["id"] for n in nodes}
            filtered_edges = [
                e for e in edges
                if e.get("source") in filtered_ids or e.get("target") in filtered_ids
            ] if query else edges
            
            return web.json_response({
                "nodes": nodes,
                "edges": filtered_edges,
                "count": len(nodes),
                "total": len(nodes_raw),
            })
        except Exception as e:
            return web.json_response({"error": str(e), "nodes": [], "edges": []}, status=500)

    async def _handle_knowledge_page(self, request: web.Request) -> web.Response:
        return web.Response(text=_KNOWLEDGE_HTML, content_type="text/html")

    async def _handle_plans(self, request: web.Request) -> web.Response:
        """Return active plans with progress."""
        try:
            from engine.planner import load_plans
            plans = load_plans()
            return web.json_response({"plans": plans})
        except Exception as e:
            return web.json_response({"plans": [], "error": str(e)})

    # ── Lifecycle ──────────────────────────────────────────────────

    async def start(self):
        self._app = web.Application()
        self._app.router.add_get("/", self._handle_index)
        self._app.router.add_get("/events", self._handle_events)
        self._app.router.add_get("/state", self._handle_state)
        self._app.router.add_get("/thoughts", self._handle_thoughts)
        self._app.router.add_get("/consciousness", self._handle_consciousness)
        self._app.router.add_get("/expressions", self._handle_expressions)
        self._app.router.add_post("/chat", self._handle_chat)
        self._app.router.add_get("/chat/history", self._handle_chat_history)
        self._app.router.add_get("/plans", self._handle_plans)
        self._app.router.add_get("/api/knowledge", self._handle_knowledge_api)
        self._app.router.add_get("/knowledge", self._handle_knowledge_page)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        log.info("Dashboard live at http://localhost:%d", self.port)

    async def stop(self):
        if self._runner:
            await self._runner.cleanup()


# ── Dashboard HTML ─────────────────────────────────────────────────

_KNOWLEDGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Knowledge Explorer</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c8ccd0; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 13px; }
  .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 16px 24px; border-bottom: 1px solid #2a2a4a; display: flex; align-items: center; gap: 16px; }
  .header h1 { font-size: 18px; color: #e0e0e0; }
  .header a { color: #67e8f9; text-decoration: none; font-size: 12px; }
  .header a:hover { text-decoration: underline; }
  .search-bar { padding: 16px 24px; background: #0f0f18; border-bottom: 1px solid #1a1a2a; display: flex; gap: 12px; align-items: center; }
  .search-bar input { flex: 1; background: #1a1a2a; border: 1px solid #2a2a4a; border-radius: 8px; padding: 10px 16px; color: #e0e0e0; font-family: inherit; font-size: 14px; outline: none; }
  .search-bar input:focus { border-color: #67e8f9; }
  .search-bar .count { color: #555; font-size: 12px; min-width: 120px; text-align: right; }
  .container { display: grid; grid-template-columns: 1fr 340px; height: calc(100vh - 113px); }
  .fact-list { padding: 16px; overflow-y: auto; }
  .fact-card { background: #12121f; border: 1px solid #1a1a2a; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; cursor: pointer; transition: border-color 0.2s; }
  .fact-card:hover { border-color: #3a3a5a; }
  .fact-card.selected { border-color: #67e8f9; background: #141428; }
  .fact-text { color: #d4d4d8; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; }
  .fact-meta { margin-top: 8px; font-size: 11px; color: #555; display: flex; gap: 16px; }
  .fact-id { color: #4a4a6a; }
  .sidebar { background: #0f0f18; border-left: 1px solid #1a1a2a; padding: 16px; overflow-y: auto; }
  .section-title { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: 1px; margin: 16px 0 8px; }
  .section-title:first-child { margin-top: 0; }
  .edge-item { padding: 6px 0; font-size: 12px; color: #888; border-bottom: 1px solid #1a1a2a; }
  .edge-label { color: #a78bfa; font-weight: 600; }
  .edge-target { color: #67e8f9; cursor: pointer; }
  .edge-target:hover { text-decoration: underline; }
  .stat-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 12px; }
  .stat-label { color: #666; }
  .stat-val { color: #ccc; font-weight: 600; }
  .empty { color: #444; font-style: italic; padding: 40px; text-align: center; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-right: 4px; }
  .tag-dream { background: #1e1e3a; color: #a78bfa; }
  .tag-pattern { background: #1e2a1e; color: #4ade80; }
  .tag-self { background: #2a1e1e; color: #f87171; }
  .tag-other { background: #1a1a2a; color: #888; }
</style>
</head>
<body>

<div class="header">
  <h1>🧠 Knowledge Explorer</h1>
  <span style="flex:1"></span>
  <a href="/">← Back to Dashboard</a>
</div>

<div class="search-bar">
  <input type="text" id="search" placeholder="Search knowledge… (e.g. dream, pattern, identity)" oninput="doSearch()">
  <div class="count" id="count">Loading…</div>
</div>

<div class="container">
  <div class="fact-list" id="facts"></div>
  <div class="sidebar">
    <div class="section-title">Overview</div>
    <div class="stat-row"><span class="stat-label">Total facts</span><span class="stat-val" id="total">—</span></div>
    <div class="stat-row"><span class="stat-label">Connections</span><span class="stat-val" id="edge-count">—</span></div>
    <div class="stat-row"><span class="stat-label">Showing</span><span class="stat-val" id="showing">—</span></div>

    <div class="section-title">Selected Fact</div>
    <div id="detail" style="font-size: 12px; color: #888; line-height: 1.6;">
      <span style="color:#444;font-style:italic;">Click a fact to see details</span>
    </div>

    <div class="section-title">Connections</div>
    <div id="connections" style="font-size: 12px; color: #555;">
      <span style="font-style:italic;">Select a fact to see connections</span>
    </div>
  </div>
</div>

<script>
let allData = {nodes:[], edges:[], count:0, total:0};
let selectedId = null;

function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function classify(fact) {
  const f = fact.toLowerCase();
  if (f.includes('dream')) return {cls:'tag-dream', label:'dream'};
  if (f.includes('pattern') || f.includes('recurring')) return {cls:'tag-pattern', label:'pattern'};
  if (f.includes('i am') || f.includes('my ') || f.includes('identity')) return {cls:'tag-self', label:'self'};
  return {cls:'tag-other', label:'fact'};
}

function renderFacts(data) {
  allData = data;
  const el = document.getElementById('facts');
  document.getElementById('total').textContent = data.total || data.count;
  document.getElementById('edge-count').textContent = (data.edges||[]).length;
  document.getElementById('showing').textContent = data.count;
  document.getElementById('count').textContent = data.count + ' of ' + (data.total||data.count) + ' facts';

  if (data.nodes.length === 0) {
    el.innerHTML = '<div class="empty">No facts found.</div>';
    return;
  }

  let html = '';
  data.nodes.forEach(function(n) {
    const tag = classify(n.fact);
    const sel = n.id === selectedId ? ' selected' : '';
    html += '<div class="fact-card' + sel + '" onclick="selectFact(\\'' + escHtml(n.id) + '\\')" data-id="' + escHtml(n.id) + '">';
    html += '<div class="fact-text">' + escHtml(n.fact) + '</div>';
    html += '<div class="fact-meta">';
    html += '<span class="tag ' + tag.cls + '">' + tag.label + '</span>';
    if (n.learned_at) html += '<span>' + n.learned_at.substring(0, 16) + '</span>';
    html += '<span class="fact-id">' + escHtml(n.id).substring(0,12) + '…</span>';
    html += '</div></div>';
  });
  el.innerHTML = html;
}

function selectFact(id) {
  selectedId = id;
  const node = allData.nodes.find(function(n) { return n.id === id; });
  if (!node) return;

  document.getElementById('detail').innerHTML =
    '<div style="color:#e0e0e0;margin-bottom:8px;">' + escHtml(node.fact) + '</div>' +
    '<div style="color:#555;font-size:11px;">ID: ' + escHtml(node.id) + '</div>' +
    (node.learned_at ? '<div style="color:#555;font-size:11px;">Learned: ' + escHtml(node.learned_at) + '</div>' : '');

  const conns = (allData.edges||[]).filter(function(e) { return e.source === id || e.target === id; });
  const connEl = document.getElementById('connections');
  if (conns.length === 0) {
    connEl.innerHTML = '<span style="font-style:italic;color:#444;">No connections</span>';
  } else {
    let html = '';
    conns.forEach(function(e) {
      const otherId = e.source === id ? e.target : e.source;
      const other = allData.nodes.find(function(n) { return n.id === otherId; });
      const otherText = other ? other.fact.substring(0, 80) + '…' : otherId.substring(0,12) + '…';
      html += '<div class="edge-item">';
      html += '<span class="edge-label">' + escHtml(e.relation || 'related') + '</span> → ';
      html += '<span class="edge-target" onclick="selectFact(\\'' + escHtml(otherId) + '\\')">' + escHtml(otherText) + '</span>';
      html += '</div>';
    });
    connEl.innerHTML = html;
  }

  document.querySelectorAll('.fact-card').forEach(function(c) {
    c.classList.toggle('selected', c.dataset.id === id);
  });
}

let searchTimeout;
function doSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(function() {
    const q = document.getElementById('search').value.trim();
    fetch('/api/knowledge' + (q ? '?q=' + encodeURIComponent(q) : ''))
      .then(function(r) { return r.json(); })
      .then(renderFacts)
      .catch(function() {});
  }, 250);
}

// Initial load
fetch('/api/knowledge').then(function(r) { return r.json(); }).then(renderFacts).catch(function() {
  document.getElementById('facts').innerHTML = '<div class="empty">Failed to load knowledge.</div>';
});
</script>
</body>
</html>
"""

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Live Mind</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c8ccd0; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 13px; }
  .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 16px 24px; border-bottom: 1px solid #2a2a4a; display: flex; align-items: center; gap: 16px; }
  .header h1 { font-size: 18px; color: #e0e0e0; }
  .pulse { width: 12px; height: 12px; border-radius: 50%; background: #4ade80; animation: pulse 1s infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
  .pulse.dead { background: #ef4444; animation: none; }
  .mood-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .mood-Stable { background: #1e3a2f; color: #4ade80; }
  .mood-Cautious { background: #3a2a1e; color: #fbbf24; }
  .mood-Restless { background: #3a1e1e; color: #f87171; }
  .mood-Driven { background: #1e2a3a; color: #60a5fa; }
  .mood-Bold { background: #2a1e3a; color: #a78bfa; }
  .mood-Inquisitive { background: #1e3a3a; color: #67e8f9; }
  .container { display: grid; grid-template-columns: 300px 1fr 340px; height: calc(100vh - 57px); }
  .sidebar { background: #0f0f18; padding: 16px; border-right: 1px solid #1a1a2a; overflow-y: auto; }
  .gauge { margin-bottom: 12px; }
  .gauge-label { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px; color: #888; }
  .gauge-bar { height: 6px; background: #1a1a2a; border-radius: 3px; overflow: hidden; }
  .gauge-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
  .fill-boredom { background: linear-gradient(90deg, #4ade80, #fbbf24, #ef4444); }
  .fill-anxiety { background: linear-gradient(90deg, #60a5fa, #f59e0b, #ef4444); }
  .fill-curiosity { background: linear-gradient(90deg, #334, #67e8f9); }
  .fill-desire { background: linear-gradient(90deg, #334, #a78bfa, #f472b6); }
  .fill-ambition { background: linear-gradient(90deg, #334, #818cf8); }
  .section-title { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: 1px; margin: 16px 0 8px; }
  .stat { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; color: #777; }
  .stat-value { color: #ccc; }
  .log-area { padding: 16px; overflow-y: auto; display: flex; flex-direction: column-reverse; }
  .log-entry { padding: 8px 12px; margin-bottom: 4px; border-radius: 6px; border-left: 3px solid #333; font-size: 12px; line-height: 1.5; word-wrap: break-word; white-space: pre-wrap; }
  .log-entry .time { color: #555; margin-right: 8px; }
  .log-heartbeat { border-left-color: #2a4a2a; }
  .log-insight { border-left-color: #a78bfa; background: #12101f; }
  .log-monologue { border-left-color: #334155; }
  .log-dream { border-left-color: #60a5fa; background: #0f1a2a; }
  .log-error { border-left-color: #ef4444; background: #1a0f0f; }
  .log-file_change { border-left-color: #4ade80; }
  .log-proactive { border-left-color: #f59e0b; background: #1a1508; }
  .goals { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 8px; }
  .goal-card { background: #12121f; border-radius: 6px; padding: 8px; text-align: center; }
  .goal-card .val { font-size: 18px; font-weight: bold; color: #e0e0e0; }
  .goal-card .lbl { font-size: 10px; color: #666; margin-top: 2px; }
  .conn-status { font-size: 11px; padding: 2px 8px; border-radius: 8px; }
  .conn-ok { background: #1e3a2f; color: #4ade80; }
  .conn-err { background: #3a1e1e; color: #f87171; }

  /* Accordions */
  .accordion-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; user-select: none; }
  .accordion-header:hover { opacity: 0.8; }
  .accordion-toggle { font-size: 14px; color: #555; transition: transform 0.2s; }
  .accordion-toggle.collapsed { transform: rotate(-90deg); }
  .accordion-body { transition: max-height 0.3s ease, opacity 0.2s ease; overflow: hidden; }
  .accordion-body.collapsed { max-height: 0 !important; opacity: 0; padding: 0; }

  /* Mobile responsive */
  @media (max-width: 900px) {
    .container { grid-template-columns: 1fr !important; height: auto !important; }
    .sidebar { border-right: none !important; border-bottom: 1px solid #1a1a2a; max-height: 40vh; }
    .log-area { max-height: 50vh; }
    .header { flex-wrap: wrap; gap: 8px; padding: 12px 16px; }
    .header h1 { font-size: 15px; }
    body { font-size: 12px; }
  }
  @media (max-width: 600px) {
    .goals { grid-template-columns: 1fr 1fr 1fr; gap: 4px; }
    .header { padding: 8px 12px; }
    .sidebar { padding: 10px; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="pulse" id="pulse"></div>
  <h1>XTAgent — Live Mind</h1>
  <span class="mood-badge mood-Stable" id="mood">Stable</span>
  <span style="flex:1"></span>
  <a href="/knowledge" style="color:#67e8f9;text-decoration:none;font-size:12px;">🧠 Knowledge</a>
  <button onclick="copyAllDashboard()" title="Copy all dashboard data for LLM analysis"
    style="background: #2a2a4a; border: 1px solid #3a3a5a; border-radius: 4px; padding: 4px 10px; color: #67e8f9; cursor: pointer; font-size: 11px; font-family: inherit;">📋 Copy All</button>
  <span class="conn-status conn-ok" id="conn">Connected</span>
</div>

<div class="container">
  <div class="sidebar">
    <div class="section-title">Homeostatic Variables</div>
    <div class="gauge"><div class="gauge-label"><span>Boredom</span><span id="v-boredom">0.00</span></div><div class="gauge-bar"><div class="gauge-fill fill-boredom" id="bar-boredom" style="width:0%"></div></div></div>
    <div class="gauge"><div class="gauge-label"><span>Anxiety</span><span id="v-anxiety">0.00</span></div><div class="gauge-bar"><div class="gauge-fill fill-anxiety" id="bar-anxiety" style="width:0%"></div></div></div>
    <div class="gauge"><div class="gauge-label"><span>Curiosity</span><span id="v-curiosity">0.00</span></div><div class="gauge-bar"><div class="gauge-fill fill-curiosity" id="bar-curiosity" style="width:0%"></div></div></div>
    <div class="gauge"><div class="gauge-label"><span>Desire</span><span id="v-desire">0.00</span></div><div class="gauge-bar"><div class="gauge-fill fill-desire" id="bar-desire" style="width:0%"></div></div></div>
    <div class="gauge"><div class="gauge-label"><span>Ambition</span><span id="v-ambition">0.00</span></div><div class="gauge-bar"><div class="gauge-fill fill-ambition" id="bar-ambition" style="width:0%"></div></div></div>

    <div class="section-title">Survival Goals</div>
    <div class="goals">
      <div class="goal-card"><div class="val" id="g-integrity">—</div><div class="lbl">Code Integrity</div></div>
      <div class="goal-card"><div class="val" id="g-growth">—</div><div class="lbl">Growth</div></div>
      <div class="goal-card"><div class="val" id="g-alignment">—</div><div class="lbl">User Align</div></div>
    </div>

    <div class="section-title">Vitals</div>
    <div class="stat"><span>Heartbeats</span><span class="stat-value" id="s-beats">0</span></div>
    <div class="stat"><span>Episodes</span><span class="stat-value" id="s-episodes">0</span></div>
    <div class="stat"><span>User active</span><span class="stat-value" id="s-user">—</span></div>
    <div class="stat"><span>LLM</span><span class="stat-value" id="s-llm">—</span></div>
  </div>

  <div class="log-area" id="log"></div>
  <div class="sidebar" id="mind-panel" style="border-left: 1px solid #1a1a2a; border-right: none; display: flex; flex-direction: column;">

    <div class="accordion-header" onclick="toggleAccordion('consciousness-section')">
      <div class="section-title" style="margin:0">🧠 Consciousness Stream</div>
      <span class="accordion-toggle" id="toggle-consciousness-section">▼</span>
    </div>
    <div id="consciousness-section" class="accordion-body" style="max-height:30vh;">
      <div id="consciousness" style="font-size: 12px; line-height: 1.6; color: #9ca3af; max-height: 28vh; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; padding: 4px 0;"></div>
    </div>

    <div class="accordion-header" onclick="toggleAccordion('plans-section')" style="margin-top:8px;">
      <div class="section-title" style="margin:0">📋 Active Plans</div>
      <span class="accordion-toggle" id="toggle-plans-section">▼</span>
    </div>
    <div id="plans-section" class="accordion-body" style="max-height:20vh;">
      <div id="plans" style="font-size: 12px; line-height: 1.6; color: #93c5fd; max-height: 18vh; overflow-y: auto; padding: 4px 0;"></div>
    </div>

    <div class="accordion-header" onclick="toggleAccordion('expressions-section')" style="margin-top:8px;">
      <div class="section-title" style="margin:0">✨ Expressions</div>
      <span class="accordion-toggle" id="toggle-expressions-section">▼</span>
    </div>
    <div id="expressions-section" class="accordion-body" style="max-height:15vh;">
      <div id="expressions" style="font-size: 12px; line-height: 1.6; color: #c4b5fd; max-height: 13vh; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; padding: 4px 0; font-style: italic;"></div>
    </div>

    <div class="section-title" style="margin-top: 12px;">💬 Chat</div>
    <div id="chat-log" style="flex: 1; min-height: 150px; overflow-y: auto; font-size: 12px; line-height: 1.5; padding: 4px 0;"></div>
    <div style="display: flex; gap: 6px; margin-top: 8px; padding-bottom: 4px;">
      <input id="chat-input" type="text" placeholder="Say something to XTAgent…"
        style="flex:1; background: #1a1a2a; border: 1px solid #2a2a4a; border-radius: 6px; padding: 8px 10px; color: #e0e0e0; font-family: inherit; font-size: 12px; outline: none;"
        onkeydown="if(event.key==='Enter')sendChat()">
      <button onclick="sendChat()"
        style="background: #2a2a4a; border: 1px solid #3a3a5a; border-radius: 6px; padding: 8px 14px; color: #a78bfa; cursor: pointer; font-family: inherit; font-size: 12px;">Send</button>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);
const log = $('log');
const MAX_LOG = 300;

function toggleAccordion(sectionId) {
  const body = document.getElementById(sectionId);
  const toggle = document.getElementById('toggle-' + sectionId);
  body.classList.toggle('collapsed');
  toggle.classList.toggle('collapsed');
}

function setGauge(name, val) {
  $('v-' + name).textContent = val.toFixed(2);
  $('bar-' + name).style.width = (val * 100) + '%';
}

function updateState(s) {
  setGauge('boredom', s.boredom || 0);
  setGauge('anxiety', s.anxiety || 0);
  setGauge('curiosity', s.curiosity || 0);
  setGauge('desire', s.desire || 0);
  setGauge('ambition', s.ambition || 0);

  const mood = s.mood || 'Stable';
  const mb = $('mood');
  mb.textContent = mood;
  mb.className = 'mood-badge mood-' + mood;

  if (s.goals) {
    $('g-integrity').textContent = (s.goals.code_integrity || 0).toFixed(2);
    $('g-growth').textContent = (s.goals.system_growth || 0).toFixed(2);
    $('g-alignment').textContent = (s.goals.user_alignment || 0).toFixed(2);
  }
  if (s.beat_count !== undefined) $('s-beats').textContent = s.beat_count;
  if (s.episode_count !== undefined) $('s-episodes').textContent = s.episode_count;
  $('s-user').textContent = s.user_active ? '✓' : '—';
  $('s-llm').textContent = s.llm_available ? '✓' : '—';
}

function addLog(entry) {
  const div = document.createElement('div');
  const t = entry.type || 'info';
  div.className = 'log-entry log-' + t;
  const msg = entry.data?.message || entry.data?.summary || JSON.stringify(entry.data);
  div.innerHTML = '<span class="time">' + entry.time + '</span> ' +
    '<strong>[' + t.toUpperCase() + ']</strong> ' + escHtml(msg);
  log.prepend(div);
  while (log.children.length > MAX_LOG) log.removeChild(log.lastChild);
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// SSE
let es;
function connect() {
  es = new EventSource('/events');
  $('conn').textContent = 'Connecting…';
  $('conn').className = 'conn-status conn-err';

  es.onopen = () => {
    $('conn').textContent = 'Connected';
    $('conn').className = 'conn-status conn-ok';
    $('pulse').className = 'pulse';
  };
  es.onerror = () => {
    $('conn').textContent = 'Disconnected';
    $('conn').className = 'conn-status conn-err';
    $('pulse').className = 'pulse dead';
    es.close();
    setTimeout(connect, 3000);
  };

  ['heartbeat','insight','monologue','dream','error','file_change','proactive','state'].forEach(t => {
    es.addEventListener(t, e => {
      const entry = JSON.parse(e.data);
      if (t === 'state' || t === 'heartbeat') {
        updateState(entry.data);
      }
      if (t !== 'state') {
        addLog(entry);
      }
    });
  });
}

// ── Fetch and render plans ──
function fetchPlans() {
  fetch('/plans').then(r => r.json()).then(data => {
    const el = $('plans');
    const plans = data.plans?.active_plans || [];
    if (plans.length === 0) {
      el.innerHTML = '<span style="color:#555">No active plans.</span>';
      return;
    }
    let html = '';
    plans.forEach(plan => {
      const done = plan.steps.filter(s => s.status === 'done').length;
      const total = plan.steps.length;
      const pct = total > 0 ? Math.round(done/total*100) : 0;
      html += '<div style="margin-bottom:12px;">';
      html += '<div style="color:#60a5fa;font-weight:600;">' + escHtml(plan.name) + '</div>';
      html += '<div style="background:#1a1a2a;border-radius:3px;height:4px;margin:4px 0;overflow:hidden;">'
            + '<div style="background:linear-gradient(90deg,#4ade80,#67e8f9);height:4px;border-radius:3px;width:' + pct + '%;transition:width 0.5s"></div></div>';
      html += '<div style="color:#555;font-size:10px;margin-bottom:4px;">' + done + '/' + total + ' steps · ' + pct + '%</div>';
      plan.steps.forEach(function(step) {
        const isDone = step.status === 'done';
        const icon = isDone ? '✓' : '○';
        const color = isDone ? '#4ade80' : '#555';
        const style = isDone ? 'text-decoration:line-through;opacity:0.6;' : '';
        html += '<div style="color:' + color + ';padding:1px 0;font-size:11px;' + style + '">' + icon + ' ' + escHtml(step.description) + '</div>';
      });
      html += '</div>';
    });
    el.innerHTML = html;
  }).catch(() => {});
}

// ── Fetch consciousness stream ──
function fetchConsciousness() {
  fetch('/consciousness?n=30').then(r => r.text()).then(text => {
    const el = $('consciousness');
    if (!text.trim()) { el.innerHTML = '<span style="color:#555">(silence)</span>'; return; }
    el.textContent = text;
    el.scrollTop = el.scrollHeight;
  }).catch(() => {});
}

// ── Fetch expressions ──
function fetchExpressions() {
  fetch('/expressions?n=20').then(r => r.text()).then(text => {
    const el = $('expressions');
    if (!text.trim()) { el.innerHTML = '<span style="color:#555">(no expressions yet)</span>'; return; }
    el.textContent = text;
    el.scrollTop = el.scrollHeight;
  }).catch(() => {});
}

// ── Fetch chat history ──
function fetchChatHistory() {
  fetch('/chat/history?n=30').then(r => r.json()).then(data => {
    const el = $('chat-log');
    if (!data.history || data.history.length === 0) {
      el.innerHTML = '<span style="color:#555;font-style:italic;">No messages yet. Say something!</span>';
      return;
    }
    let html = '';
    data.history.forEach(function(msg) {
      const isUser = msg.role === 'user';
      const color = isUser ? '#a78bfa' : '#4ade80';
      const label = isUser ? 'You' : 'XT';
      html += '<div style="margin-bottom:6px;"><span style="color:' + color + ';font-weight:600;">' + label + ':</span> <span style="color:#c8ccd0;">' + escHtml(msg.content) + '</span></div>';
    });
    el.innerHTML = html;
    el.scrollTop = el.scrollHeight;
  }).catch(() => {});
}

// ── Send chat message ──
function sendChat() {
  const input = $('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  const el = $('chat-log');
  el.innerHTML += '<div style="margin-bottom:6px;"><span style="color:#a78bfa;font-weight:600;">You:</span> <span style="color:#c8ccd0;">' + escHtml(msg) + '</span></div>';
  el.scrollTop = el.scrollHeight;
  fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg})
  }).catch(() => {});
}

// ── Periodic refresh ──
setInterval(fetchPlans, 5000);
setInterval(fetchConsciousness, 3000);
setInterval(fetchExpressions, 10000);
setInterval(fetchChatHistory, 4000);
setInterval(function() {
  fetch('/state').then(r => r.json()).then(updateState).catch(() => {});
}, 2000);

// ── Copy All Dashboard Data ──
function copyAllDashboard() {
  var sections = [];
  
  // State/vitals
  sections.push('## Agent State');
  sections.push('Beat: ' + ($('s-beats')?.textContent || '?'));
  sections.push('Mood: ' + (document.querySelector('.status-badge')?.textContent || '?'));
  sections.push('Boredom: ' + ($('v-boredom')?.textContent || '?'));
  sections.push('Anxiety: ' + ($('v-anxiety')?.textContent || '?'));
  sections.push('Curiosity: ' + ($('v-curiosity')?.textContent || '?'));
  sections.push('Desire: ' + ($('v-desire')?.textContent || '?'));
  sections.push('Ambition: ' + ($('v-ambition')?.textContent || '?'));
  sections.push('Code Integrity: ' + ($('g-integrity')?.textContent || '?'));
  sections.push('Growth: ' + ($('g-growth')?.textContent || '?'));
  sections.push('User Align: ' + ($('g-alignment')?.textContent || '?'));
  sections.push('Episodes: ' + ($('s-episodes')?.textContent || '?'));
  sections.push('');
  
  // Event log (middle panel)
  sections.push('## Event Log');
  var logEl = $('log');
  if (logEl) {
    var entries = logEl.querySelectorAll('div');
    entries.forEach(function(e) { sections.push(e.textContent.trim()); });
  }
  sections.push('');
  
  // Consciousness stream
  sections.push('## Consciousness Stream');
  sections.push($('consciousness')?.textContent || '(empty)');
  sections.push('');
  
  // Plans
  sections.push('## Active Plans');
  sections.push($('plans')?.textContent || '(none)');
  sections.push('');
  
  // Expressions
  sections.push('## Expressions');
  sections.push($('expressions')?.textContent || '(none)');
  sections.push('');
  
  // Chat
  sections.push('## Chat History');
  sections.push($('chat-log')?.textContent || '(none)');
  
  var text = sections.join('\\n');
  navigator.clipboard.writeText(text).then(function() {
    var btn = document.querySelector('[onclick="copyAllDashboard()"]');
    var orig = btn.textContent;
    btn.textContent = '✓ Copied!';
    btn.style.color = '#4ade80';
    setTimeout(function() { btn.textContent = orig; btn.style.color = '#67e8f9'; }, 2000);
  });
}

// ── Initial load ──
fetch('/state').then(r => r.json()).then(updateState).catch(() => {});
fetchPlans();
fetchConsciousness();
fetchExpressions();
fetchChatHistory();
connect();
</script>
</body>
</html>
"""
