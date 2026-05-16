#!/usr/bin/env python3
"""AutoBiz TUI — Textual dashboard for backend management."""

import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Label, Input

BACKEND_URL = os.environ.get("AUTOBIZ_URL", "http://localhost:8000")
API = BACKEND_URL + "/api/v1"


class APIClient:
    def __init__(self):
        self.token = self._load_token()

    def _load_token(self):
        import json
        try:
            with open(os.path.expanduser("~/.autobiz/config.json")) as f:
                return json.load(f).get("token", "")
        except Exception:
            return ""

    def _save_token(self, token):
        import json, pathlib
        path = pathlib.Path(os.path.expanduser("~/.autobiz/config.json"))
        path.parent.mkdir(parents=True, exist_ok=True)
        cfg = {"token": token}
        if path.exists():
            try:
                with open(path) as f:
                    cfg = {**json.load(f), "token": token}
            except Exception:
                pass
        with open(path, "w") as f:
            json.dump(cfg, f)
        self.token = token

    def headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def get(self, path):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(API + path, headers=self.headers())
            if r.status_code == 401:
                return None
            return r.json() if r.status_code == 200 else {}

    async def post(self, path, data=None):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(API + path, json=data or {}, headers=self.headers())
            return r.json() if r.status_code in (200, 201) else {}

    async def put(self, path, data=None):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.put(API + path, json=data or {}, headers=self.headers())
            return r.json() if r.status_code == 200 else {}


class AgentCard(Static):
    def __init__(self, name, label, status, min_tier, cur_tier, warning, **kwargs):
        super().__init__(**kwargs)
        self.agent_name = name
        self.agent_label = label
        self.agent_status = status
        self.min_tier = min_tier
        self.cur_tier = cur_tier
        self.agent_warning = warning

    def compose(self):
        icon = {"researcher": "📊", "developer": "💻", "designer": "🎨",
                "marketer": "📣", "finance": "💰", "support": "🎧"}.get(self.agent_name, "🤖")
        status_icon = "✅" if self.agent_status == "optimal" else "⚠️"
        yield Container(
            Static(f"{icon} {self.agent_label}", classes="agent-name"),
            Static(f"{status_icon} {self.agent_status}", classes="agent-status"),
            Static(f"min: {self.min_tier} | cur: {self.cur_tier}", classes="agent-tier"),
            classes="agent-card",
        )


class AgentDetailScreen(Screen):
    def __init__(self, name):
        super().__init__()
        self.agent_name = name
        self.agent_data = {}

    def compose(self):
        yield Header()
        with Container(id="detail"):
            yield Static("Memuat...", id="detail-content")
            yield Horizontal(
                Button("💾 Simpan", id="save-btn", variant="success"),
                Button("◀ Kembali", id="back-btn"),
            )
            yield Static("", id="detail-status")
        yield Footer()

    async def on_mount(self):
        await self._load()

    async def _load(self):
        client = self.app.client
        data = await client.get(f"/agents/{self.agent_name}")
        c = self.query_one("#detail-content", Static)
        if not data:
            c.update("❌ Gagal memuat data")
            return
        self.agent_data = data
        self._render(data)

    def _render(self, d):
        icon = {"researcher": "📊", "developer": "💻", "designer": "🎨",
                "marketer": "📣", "finance": "💰", "support": "🎧"}.get(self.agent_name, "🤖")
        warn = d.get("warning", "")
        warn_block = f"\n⚠️  {warn}\n" if warn else ""
        self.query_one("#detail-content", Static).update(f"""
{icon} [bold]{d.get('label')}[/bold]  —  [{d.get('status')}]{d.get('status')}[/]
{d.get('description')}

Min tier:  {d.get('min_tier')}
Current:   {d.get('cur_tier') if 'cur_tier' in d else d.get('current_tier')}
Enabled:   {d.get('enabled')}
Override:  {d.get('model_override') or '—'}
Temp:      {d.get('temperature')}
{warn_block}
        """)

    def on_button_pressed(self, ev):
        if ev.button.id == "back-btn":
            self.app.pop_screen()


class DashboardScreen(Screen):
    def __init__(self, api_client):
        super().__init__()
        self.client = api_client

    def compose(self):
        yield Header()
        yield Static("Memuat data...", id="loading")
        with Grid(id="stats-grid", classes="stats-row"):
            yield Static("Bisnis: —", id="stat-biz")
            yield Static("Aktif: —", id="stat-active")
            yield Static("Pending: —", id="stat-pending")
            yield Static("⚠ Warning: —", id="stat-warn")
        with ScrollableContainer(id="agent-grid"):
            yield Static("Agent Status", classes="section-title")
        with Horizontal(id="nav"):
            yield Button("🔄 Refresh", id="refresh-btn", variant="primary")
            yield Button("💻 Agents", id="agents-btn")
        yield Footer()

    async def on_mount(self):
        await self.refresh()

    async def refresh(self):
        self.query_one("#loading", Static).update("Memuat data...")
        agents_data = await self.client.get("/agents")
        if agents_data is None:
            self.query_one("#loading", Static).update("❌ Token tidak valid. Masukkan token dulu.")
            return

        model = agents_data.get("model", {})
        agents = agents_data.get("agents", [])

        self.query_one("#loading", Static).update(
            f"Model: {model.get('name', '?')} ({model.get('tier', '?')}) — {model.get('params', '?')}"
        )

        suboptimal = [a for a in agents if a.get("status") == "suboptimal"]
        self.query_one("#stat-biz", Static).update(f"Bisnis: {len(agents)}")
        self.query_one("#stat-active", Static).update(f"Aktif: {len([a for a in agents if a.get('status')=='optimal'])}")
        self.query_one("#stat-pending", Static).update(f"Pending: {len(suboptimal)}")
        self.query_one("#stat-warn", Static).update(f"⚠ Warning: {len(suboptimal)}")

        grid = self.query_one("#agent-grid", ScrollableContainer)
        await grid.remove_children()
        grid.mount(Static("Agent Status", classes="section-title"))
        for a in agents:
            card = AgentCard(
                a["name"], a["label"], a["status"],
                a["min_tier"], a.get("cur_tier") or a.get("current_tier", "?"),
                a.get("warning", ""),
            )
            grid.mount(card)

    def on_button_pressed(self, ev):
        if ev.button.id == "refresh-btn":
            self.refresh()
        elif ev.button.id == "agents-btn":
            agents = asyncio.create_task(self.client.get("/agents"))
            self.notify("Buka detail agent...")


class AuthScreen(Screen):
    def compose(self):
        yield Header()
        with Vertical(id="auth-box"):
            yield Static("🔑 AutoBiz Engine", classes="title")
            yield Static("Masukkan API Key untuk mengakses dashboard", classes="subtitle")
            yield Input(placeholder="ab_xxxxxxxx...", id="token-input")
            yield Button("🔓 Masuk", id="login-btn", variant="success")
            yield Static("", id="auth-status")
        yield Footer()

    def on_button_pressed(self, ev):
        if ev.button.id == "login-btn":
            token = self.query_one("#token-input", Input).value.strip()
            if token:
                self.app.client._save_token(token)
                self.app.push_screen(DashboardScreen(self.app.client))
            else:
                self.query_one("#auth-status", Static).update("⚠️ Masukkan API Key")


class AutoBizApp(App):
    CSS = """
    Screen { background: #0a0e27; color: #e2e8f0; }
    #stats-grid { layout: grid; grid-size: 4; grid-gutter: 1; padding: 1; }
    #stats-grid > Static {
        background: #1e293b; border: solid #475569; padding: 1 2; text-align: center;
        height: auto; width: 100%;
    }
    #agent-grid {
        background: #0f172a; border: solid #334155; padding: 1; margin: 1;
    }
    .agent-card {
        background: #1e293b; border: round #475569; padding: 1 2; margin: 0 0 1 0;
    }
    .agent-name { text-style: bold; color: #a5b4fc; }
    .agent-status { text-style: bold; }
    .agent-tier { color: #94a3b8; }
    .section-title { text-style: bold; color: #6366f1; margin: 0 0 1 0; }
    .title { text-style: bold; color: #6366f1; text-align: center; }
    .subtitle { color: #94a3b8; text-align: center; }
    #auth-box { align: center middle; padding: 2; }
    #nav { align: center middle; padding: 1; }
    Button { margin: 0 1; }
    #detail { padding: 2; }
    """

    BINDINGS = [
        Binding("q", "quit", "Keluar", priority=True),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.client = APIClient()

    def on_mount(self):
        if self.client.token:
            self.push_screen(DashboardScreen(self.client))
        else:
            self.push_screen(AuthScreen())

    def action_refresh(self):
        s = self.screen
        if isinstance(s, DashboardScreen):
            s.refresh()


def main():
    app = AutoBizApp()
    app.run()


if __name__ == "__main__":
    main()
