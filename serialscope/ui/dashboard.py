"""
Main dashboard UI using Textual.

Provides a split-pane layout with logs and metrics panels.
"""

from collections import defaultdict
from typing import Dict, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from serialscope.core.event import Event, EventType
from serialscope.ui.log_panel import LogPanel


class MetricsPanel(Static):
    """Panel for displaying real-time telemetry metrics."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics: Dict[str, float] = {}
        self.update_interval = 0.5  # Update every 500ms

    def update_metric(self, name: str, value: float) -> None:
        """Update a metric value."""
        self.metrics[name] = value
        self._update_display()

    def _update_display(self) -> None:
        """Update the metrics display."""
        if not self.metrics:
            self.update("[dim]No metrics available[/dim]")
            return

        lines = ["[bold]System Metrics[/bold]", ""]
        for name, value in sorted(self.metrics.items()):
            # Format value appropriately
            if "temp" in name.lower() or "temperature" in name.lower():
                formatted = f"{value:.1f} °C"
            elif "voltage" in name.lower():
                formatted = f"{value:.2f} V"
            elif "rssi" in name.lower():
                formatted = f"{value:.0f} dBm"
            elif "cpu" in name.lower() or "usage" in name.lower():
                formatted = f"{value:.1f} %"
            else:
                formatted = f"{value:.2f}"

            lines.append(f"{name:20s}: {formatted}")

        self.update("\n".join(lines))


class Dashboard(App):
    """
    Main dashboard application.

    Layout:
    +------------------------------------------------+
    | SerialScope                                    |
    +----------------------+-------------------------+
    | Logs                 | System Metrics         |
    |----------------------|------------------------|
    | [INFO] Boot OK       | Temp: 42.3 °C          |
    | [WARN] Low battery   | Voltage: 3.28 V        |
    |                      | WiFi RSSI: -62 dBm     |
    +----------------------+------------------------+
    | Command Input:                                |
    +------------------------------------------------+
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #log-panel {
        height: 1fr;
        border: solid $primary;
        scrollbar-gutter: stable;
    }

    #log-content {
        width: 100%;
        padding: 1;
    }

    #metrics-panel {
        width: 30%;
        border: solid $primary;
        padding: 1;
    }

    #main-container {
        layout: horizontal;
    }

    #log-container {
        width: 70%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_logs", "Clear Logs"),
        ("t", "toggle_timestamps", "Toggle Timestamps"),
        ("f", "filter_menu", "Filter"),
        ("up", "scroll_up", "Scroll Up"),
        ("down", "scroll_down", "Scroll Down"),
        ("pageup", "scroll_page_up", "Page Up"),
        ("pagedown", "scroll_page_down", "Page Down"),
        ("home", "scroll_home", "Scroll Home"),
        ("end", "scroll_end", "Scroll End"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_panel: Optional[LogPanel] = None
        self.metrics_panel: Optional[MetricsPanel] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="log-container"):
                yield LogPanel(id="log-panel", show_timestamps=True)
            yield MetricsPanel(id="metrics-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        self.log_panel = self.query_one("#log-panel", LogPanel)
        self.metrics_panel = self.query_one("#metrics-panel", MetricsPanel)
        self.title = "SerialScope"

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_clear_logs(self) -> None:
        """Clear all logs."""
        if self.log_panel:
            self.log_panel.clear()

    def action_toggle_timestamps(self) -> None:
        """Toggle timestamp display."""
        if self.log_panel:
            self.log_panel.toggle_timestamps()

    def action_filter_menu(self) -> None:
        """Open filter menu (placeholder)."""
        self.notify("Filter menu (not yet implemented)", severity="information")

    def add_event(self, event: Event) -> None:
        """
        Add an event to the dashboard.

        Args:
            event: Event to display
        """
        if self.log_panel:
            self.log_panel.add_event(event)

        # Extract metrics from event
        if event.type == EventType.METRIC and self.metrics_panel:
            for key, value in event.data.items():
                if isinstance(value, (int, float)):
                    self.metrics_panel.update_metric(key, float(value))
