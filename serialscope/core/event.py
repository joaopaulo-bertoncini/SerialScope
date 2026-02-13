"""
Event abstraction layer.

This module defines the core Event class that unifies all serial data
into a structured format, enabling smart filtering, visualization, and replay.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EventType(str, Enum):
    """Types of events that can be processed."""

    LOG = "log"
    METRIC = "metric"
    PACKET = "packet"


class LogLevel(str, Enum):
    """Standard log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


@dataclass
class Event:
    """
    Unified event structure for all serial data.

    This abstraction is critical - it allows the system to treat
    plain text, JSON logs, and binary packets uniformly.
    """

    type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    level: Optional[LogLevel] = None
    data: Dict[str, Any] = field(default_factory=dict)
    raw: Optional[str] = None
    source: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate event structure."""
        if self.type == EventType.LOG and self.level is None:
            # Try to infer level from data
            if "level" in self.data:
                try:
                    self.level = LogLevel(self.data["level"].upper())
                except ValueError:
                    pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value if self.level else None,
            "data": self.data,
            "raw": self.raw,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            type=EventType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=LogLevel(data["level"]) if data.get("level") else None,
            data=data.get("data", {}),
            raw=data.get("raw"),
            source=data.get("source"),
        )

    def is_error(self) -> bool:
        """Check if event represents an error."""
        if self.level in (LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.FATAL):
            return True
        return False

    def is_warning(self) -> bool:
        """Check if event represents a warning."""
        return self.level in (LogLevel.WARN, LogLevel.WARNING)
