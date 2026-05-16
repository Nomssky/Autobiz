#!/usr/bin/env python3
"""AutoBiz TUI — Dark mode dashboard inspired by opencode / Claude Code."""

import asyncio
import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static, Input, Button, Header, Footer

BACKEND_URL = os.environ.get("AUTOBIZ_URL", "http://localhost:8000")
API = BACKEND_URL + "/api/v1"

AGENT_ICONS = {
    "researcher": "📊", "developer": "💻", "designer": "🎨",
    "marketer": "📣", "finance": "💰", "support": "🎧",
}


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
        p = pathlib.Path(os.path.expanduser("~/.autobiz/config.json"))
        p.parent.mkdir(parents=True, exist_ok=True)
        cfg = {"token": token}
        if p.exists():
            try:
                with open(p) as f:
                    cfg = {**json.load(f), "token": token}
            except Exception:
                pass
        with open(p, "w") as f:
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

    async def put(self, path, data=None):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.put(API + path, json=data or {}, headers=self.headers())
            return r.json() if r.status_code == 200 else {}


class TopBar(Static):
    def __init__(self, text="", model=""):
        super().__init__()
        self.bar_text = text
        self.bar_model = model

    def on_mount(self):
        self.update(f"  ◈ AutoBiz  │  {self.bar_text}  │  {self.bar_model}")


class BottomBar(Static):
    def __init__(self):
        super().__init__()

    def on_mount(self):
        self.render_nav()

    def render_nav(self, current="dashboard"):
        items = [
            ("1", "Dashboard"),
            ("2", "Bisnis"),
            ("3", "Keputusan"),
            ("4", "Agents"),
            ("Q", "Keluar"),
        ]
        parts = []
        for key, label in items:
            parts.append(f"[text-bold text-brand]{key}[/] {label}")
        self.update("  " + "  │  ".join(parts))


class AuthScreen(Screen):
    def compose(self):
        yield Container(
            Vertical(
                Static("◈ AutoBiz Engine", classes="auth-title"),
                Static("Masukkan API Key untuk melanjutkan", classes="auth-subtitle"),
                Input(placeholder="ab_xxxxxxxx...", id="token-input"),
                Button("🔑 Masuk", id="login-btn", variant="primary"),
                Static("", id="auth-status"),
                classes="auth-box",
            ),
            id="auth-screen",
        )

    def on_button_pressed(self, ev):
        if ev.button.id == "login-btn":
            self._login()

    def on_input_submitted(self, _):
        self._login()

    def _login(self):
        token = self.query_one("#token-input", Input).value.strip()
        if not token:
            self.query_one("#auth-status", Static).update("⚠️  Masukkan API Key")
            return
        self.app.client._save_token(token)
        self.app.push_screen(DashboardScreen(self.app.client))


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("2", "goto('businesses')", "Bisnis"),
        Binding("3", "goto('approvals')", "Keputusan"),
        Binding("4", "goto('agents')", "Agents"),
    ]

    def __init__(self, client):
        super().__init__()
        self.client = client

    def compose(self):
        yield Container(
            TopBar("Dashboard", "memuat..."),
            Static("", id="loading"),
            Horizontal(
                Vertical(Static("—", classes="stat-num"), Static("Bisnis", classes="stat-label"), classes="stat-card"),
                Vertical(Static("—", classes="stat-num"), Static("Aktif", classes="stat-label"), classes="stat-card"),
                Vertical(Static("—", classes="stat-num"), Static("Pending", classes="stat-label"), classes="stat-card"),
                Vertical(Static("—", classes="stat-num"), Static("⚠ Agent", classes="stat-label"), classes="stat-card"),
                id="stats-grid",
            ),
            Static("Agent Status", classes="section-title"),
            ScrollableContainer(id="agent-list"),
            BottomBar(),
            id="dashboard-screen",
        )

    async def on_mount(self):
        await self._reload()

    async def _reload(self):
        data = await self.client.get("/agents")
        if data is None:
            self.query_one("#loading", Static).update("[text-error]Token tidak valid[/]")
            return

        model = data.get("model", {})
        agents = data.get("agents", [])

        self.query_one(TopBar).update(
            f"  ◈ AutoBiz  │  Dashboard  │  [text-brand]{model.get('name','?')}[/] ([text-muted]{model.get('tier','?')}[/])"
        )

        suboptimal = [a for a in agents if a.get("status") == "suboptimal"]
        cards = self.query("#stats-grid > Vertical")
        cards[0].query_one(".stat-num").update(str(len(agents)))
        cards[1].query_one(".stat-num").update(str(len([a for a in agents if a.get("status") == "optimal"])))
        cards[2].query_one(".stat-num").update(str(len(suboptimal)))
        wc = cards[3]
        wc.query_one(".stat-num").update(str(len(suboptimal)))
        if suboptimal:
            wc.classes = "stat-card warn"
            wc.query_one(".stat-label").update("⚠ Agent")
        else:
            wc.classes = "stat-card"

        self.query_one("#loading", Static).update("")

        alist = self.query_one("#agent-list", ScrollableContainer)
        await alist.remove_children()

        for a in agents:
            icon = AGENT_ICONS.get(a["name"], "🤖")
            name = a["label"]
            min_t = a["min_tier"]
            cur_t = a.get("cur_tier") or a.get("current_tier", "?")
            status = a["status"]
            dot = "●" if status == "optimal" else "○"
            dot_color = "text-success" if status == "optimal" else "text-warning"
            row = Static(
                f"  [{dot_color}]{dot}[/]  {icon}  [text-bold]{name}[/]  "
                f"[text-muted]{min_t}[/] ← [text-muted]{cur_t}[/]",
                classes="agent-row",
            )
            alist.mount(row)

    def action_goto(self, section):
        if section == "agents":
            self.notify("📋 Pilih agent → tab 4")
        elif section in ("businesses", "approvals"):
            self.notify(f"🔜 {section.title()} — coming soon")


class AgentDetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("enter", "save", "Simpan"),
    ]

    def __init__(self, name):
        super().__init__()
        self.agent_name = name
        self.data = {}

    def compose(self):
        yield Container(
            TopBar("Agent Detail", self.agent_name),
            Horizontal(
                Button("← Kembali", id="back-btn", classes="back-btn"),
                Static("", id="page-title"),
            ),
            Static("", id="detail-body"),
            Static("", id="detail-warn"),
            Container(
                Static("⚙️ Konfigurasi", classes="section-title"),
                Static("Enabled", id="cfg-enabled"),
                Static("Model Override", id="cfg-model"),
                Static("Temperature", id="cfg-temp"),
                Button("💾 Simpan", id="save-btn", variant="success"),
                Static("", id="cfg-status"),
                classes="config-box",
            ),
            BottomBar(),
        )

    async def on_mount(self):
        await self._load()

    async def _load(self):
        data = await self.app.client.get(f"/agents/{self.agent_name}")
        if not data:
            self.query_one("#detail-body", Static).update("[text-error]Gagal memuat[/]")
            return
        self.data = data
        self._render(data)

    def _render(self, d):
        icon = AGENT_ICONS.get(self.agent_name, "🤖")
        status = d.get("status", "?")
        status_dot = "●" if status == "optimal" else "○"
        status_color = "text-success" if status == "optimal" else "text-warning"
        warn = d.get("warning", "")

        body = (
            f"  {icon}  [text-bold]{d.get('label','?')}[/]\n"
            f"       [text-muted]{d.get('description','?')}[/]\n\n"
            f"  Status       [{status_color}]{status_dot} {status}[/]\n"
            f"  Min tier     [text-bold]{d.get('min_tier','?')}[/]\n"
            f"  Current      [text-muted]{d.get('cur_tier') or d.get('current_tier','?')}[/]\n"
        )
        self.query_one("#detail-body", Static).update(body)

        if warn:
            self.query_one("#detail-warn", Static).update(
                f"  [text-warning]⚠ {warn}[/]"
            )
        else:
            self.query_one("#detail-warn", Static).update("")

        self.query_one("#cfg-enabled", Static).update(
            f"  [text-muted]Enabled:[/]  {'[text-success]● Ya[/]' if d.get('enabled', True) else '[text-error]○ Tidak[/]'}"
        )
        self.query_one("#cfg-model", Static).update(
            f"  [text-muted]Override:[/] {d.get('model_override') or '[text-muted]— (default)[/]'}"
        )
        self.query_one("#cfg-temp", Static).update(
            f"  [text-muted]Temp:[/]      {d.get('temperature', 0.7)}"
        )

    def action_back(self):
        self.app.pop_screen()

    def on_button_pressed(self, ev):
        if ev.button.id == "back-btn":
            self.action_back()
        elif ev.button.id == "save-btn":
            self.notify("💾 Simpan — coming soon")

    def action_save(self):
        self.on_button_pressed(type("E", (), {"button": type("B", (), {"id": "save-btn"})})())


class AgentListScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Kembali"),
    ]
    AGENTS = ["researcher", "developer", "designer", "marketer", "finance", "support"]

    def compose(self):
        yield Container(
            TopBar("Agents", "pilih agent"),
            Static("Pilih agent untuk melihat detail:", classes="section-title"),
            ScrollableContainer(id="agent-choices"),
            BottomBar(),
        )

    async def on_mount(self):
        data = await self.app.client.get("/agents")
        agents = data.get("agents", []) if data else []
        cont = self.query_one("#agent-choices", ScrollableContainer)
        for a in agents:
            icon = AGENT_ICONS.get(a["name"], "🤖")
            st = a["status"]
            dot = "●" if st == "optimal" else "○"
            dc = "text-success" if st == "optimal" else "text-warning"
            btn = Static(
                f"  [{dc}]{dot}[/]  {icon}  [text-bold]{a['label']}[/]  "
                f"[text-muted]{a['min_tier']}[/] ← [text-muted]{a.get('cur_tier') or a.get('current_tier','?')}[/]"
                f"  [{dc}]{st}[/]",
                id=f"agent-{a['name']}",
                classes="agent-row",
            )
            btn.on_click = lambda n=a["name"]: self._open(n)
            cont.mount(btn)

    def _open(self, name):
        self.app.push_screen(AgentDetailScreen(name))


class AutoBizApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("q", "quit", "Keluar", priority=True),
        Binding("1", "go_dashboard", "Dashboard"),
        Binding("4", "go_agents", "Agents"),
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

    def action_go_dashboard(self):
        self.switch_to(DashboardScreen)

    def action_go_agents(self):
        self.push_screen(AgentListScreen())

    def action_refresh(self):
        s = self.screen
        if isinstance(s, DashboardScreen):
            asyncio.create_task(s._reload())

    def switch_to(self, cls):
        from textual.screen import Screen
        if not isinstance(self.screen, cls):
            self.push_screen(cls(self.client) if cls == DashboardScreen else cls())


def main():
    AutoBizApp().run()


if __name__ == "__main__":
    main()
