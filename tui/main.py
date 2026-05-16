#!/usr/bin/env python3
"""AutoBiz TUI — WebView dashboard inside terminal."""

import sys
import os

# Add backend to path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from textual.app import App
from textual.binding import Binding
from textual_webview import WebView

BACKEND_URL = os.environ.get("AUTOBIZ_URL", "http://localhost:8000")


class AutoBizApp(App):
    TITLE = "AutoBiz Engine"
    SUB_TITLE = "AI-Powered Business Automation"

    BINDINGS = [
        Binding("q", "quit", "Keluar", priority=True),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self):
        yield WebView(BACKEND_URL + "/ui/dashboard")

    def action_refresh(self):
        wv = self.query_one(WebView)
        wv.reload()


if __name__ == "__main__":
    app = AutoBizApp()
    app.run()
