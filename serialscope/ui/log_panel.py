"""
Log panel component for displaying structured logs.

Provides filtering, highlighting, and search capabilities.
"""

import re
from collections import deque
from typing import Deque, Optional, Set, Iterator

from rich.console import Console
from rich.text import Text
from textual.containers import ScrollableContainer
from textual.widgets import Static

from serialscope.core.event import Event, LogLevel


class LogPanel(ScrollableContainer):
    """
    Terminal UI panel for displaying logs.

    Features:
    - Scroll logs
    - Filter by level
    - Regex search
    - Toggle timestamps
    - Highlight patterns
    - Clear buffer
    """

    def __init__(
        self,
        max_lines: int = 1000,
        show_timestamps: bool = True,
        filter_levels: Optional[Set[LogLevel]] = None,
        search_pattern: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize log panel.

        Args:
            max_lines: Maximum number of log lines to keep in buffer
            show_timestamps: Whether to display timestamps
            filter_levels: Set of log levels to display (None = all)
            search_pattern: Regex pattern to highlight/search
        """
        super().__init__(*args, **kwargs)
        self.max_lines = max_lines
        self.show_timestamps = show_timestamps
        self.filter_levels = filter_levels
        self.search_pattern = search_pattern

        self.logs: Deque[Event] = deque(maxlen=max_lines)
        self.console = Console()
        self._auto_scroll = True  # Auto-scroll to bottom by default
        self._content: Optional[Static] = None  # Will be set in on_mount

    def add_event(self, event: Event) -> None:
        """
        Add a new event to the log panel.

        Args:
            event: Event to add
        """
        # Apply filters
        if self.filter_levels and event.level not in self.filter_levels:
            return

        self.logs.append(event)
        self._update_display()

    def set_filter_levels(self, levels: Optional[Set[LogLevel]]) -> None:
        """Set log level filter."""
        self.filter_levels = levels
        self._update_display()

    def set_search_pattern(self, pattern: Optional[str]) -> None:
        """Set search/highlight pattern."""
        self.search_pattern = pattern
        self._update_display()

    def toggle_timestamps(self) -> None:
        """Toggle timestamp display."""
        self.show_timestamps = not self.show_timestamps
        self._update_display()

    def clear(self) -> None:
        """Clear all logs."""
        self.logs.clear()
        self._update_display()

    def compose(self) -> Iterator[Static]:
        """Compose the log panel with scrollable content."""
        self._content = Static("", id="log-content")
        yield self._content

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self._content = self.query_one("#log-content", Static)
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed log content."""
        # If content widget is not yet mounted, skip update
        if not hasattr(self, '_content') or self._content is None:
            return
            
        if not self.logs:
            self._content.update("")
            return

        lines = []
        for event in self.logs:
            line = self._format_event(event)
            lines.append(line)

        # Update content - use Rich Text for proper markup rendering
        from rich.text import Text as RichText
        content_text = "\n".join(lines)
        # Convert Rich markup string to Rich Text object for proper rendering
        rich_content = RichText.from_markup(content_text) if content_text else RichText("")
        self._content.update(rich_content)
        
        # Auto-scroll to bottom if enabled
        if self._auto_scroll:
            self.scroll_end(animate=False)

    def _format_event(self, event: Event) -> str:
        """
        Format an event as a log line.

        Args:
            event: Event to format

        Returns:
            Formatted string
        """
        parts = []

        # Timestamp
        if self.show_timestamps:
            timestamp = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
            parts.append(f"[dim]{timestamp}[/dim]")

        # Level badge
        if event.level:
            level_color = self._get_level_color(event.level)
            parts.append(f"[{level_color}]{event.level.value:8s}[/{level_color}]")

        # Message
        message = event.data.get("message", str(event.data))
        if self.search_pattern:
            message = self._highlight_pattern(message, self.search_pattern)

        parts.append(message)

        return " ".join(parts)

    @staticmethod
    def _get_level_color(level: LogLevel) -> str:
        """Get color for log level."""
        colors = {
            LogLevel.DEBUG: "dim white",
            LogLevel.INFO: "cyan",
            LogLevel.WARN: "yellow",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bold red",
            LogLevel.FATAL: "bold red",
        }
        return colors.get(level, "white")

    def _highlight_pattern(self, text: str, pattern: str) -> str:
        """
        Highlight regex pattern in text.

        Args:
            text: Text to search
            pattern: Regex pattern

        Returns:
            Text with highlighted matches
        """
        try:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if not matches:
                return text

            # Build highlighted text
            result = Text()
            last_end = 0
            for match in matches:
                # Add text before match
                result.append(text[last_end : match.start()])
                # Add highlighted match
                result.append(text[match.start() : match.end()], style="bold yellow on red")
                last_end = match.end()

            # Add remaining text
            result.append(text[last_end:])
            return str(result)
        except re.error:
            return text
