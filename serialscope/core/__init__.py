"""Core modules for SerialScope."""

from serialscope.core.event import Event, EventType, LogLevel
from serialscope.core.parser import StreamParser, ParserMode
from serialscope.core.serial_manager import SerialManager

__all__ = [
    "Event",
    "EventType",
    "LogLevel",
    "StreamParser",
    "ParserMode",
    "SerialManager",
]
