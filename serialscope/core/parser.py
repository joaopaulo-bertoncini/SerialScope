"""
Stream parser for converting raw serial data into structured events.

Supports multiple parsing modes:
- Plain text logs
- JSON logs
- Binary packets
"""

import json
import logging
import re
from enum import Enum
from typing import Iterator, Optional

from serialscope.core.event import Event, EventType, LogLevel

logger = logging.getLogger(__name__)


class ParserMode(str, Enum):
    """Parser operation modes."""

    PLAIN_TEXT = "plain"
    JSON = "json"
    BINARY = "binary"
    AUTO = "auto"  # Attempt to auto-detect format


class StreamParser:
    """
    Converts raw serial bytes into structured Event objects.

    This abstraction is critical - it allows the system to treat
    different data formats uniformly.
    """

    # Regex patterns for plain text log parsing
    LOG_PATTERN = re.compile(
        r"\[?(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\]?\s*(?P<message>.*)",
        re.IGNORECASE,
    )

    def __init__(self, mode: ParserMode = ParserMode.AUTO):
        """
        Initialize parser.

        Args:
            mode: Parsing mode (plain, json, binary, or auto-detect)
        """
        self.mode = mode
        self.buffer = bytearray()
        self.detected_mode: Optional[ParserMode] = None

    def parse(self, data: bytes) -> Iterator[Event]:
        """
        Parse raw bytes into events.

        Args:
            data: Raw bytes from serial port

        Yields:
            Event objects
        """
        self.buffer.extend(data)

        if self.mode == ParserMode.AUTO and self.detected_mode is None:
            self._detect_mode()

        mode = self.detected_mode if self.detected_mode else self.mode

        if mode == ParserMode.PLAIN_TEXT:
            yield from self._parse_plain_text()
        elif mode == ParserMode.JSON:
            yield from self._parse_json()
        elif mode == ParserMode.BINARY:
            yield from self._parse_binary()
        else:
            # Fallback to plain text
            yield from self._parse_plain_text()

    def _detect_mode(self) -> None:
        """Attempt to auto-detect data format."""
        if len(self.buffer) < 10:
            return

        try:
            # Try to decode as UTF-8
            text = self.buffer.decode("utf-8", errors="strict")
            
            # Check if it looks like JSON
            if text.strip().startswith("{") or text.strip().startswith("["):
                # Try to parse as JSON
                try:
                    json.loads(text.split("\n")[0])
                    self.detected_mode = ParserMode.JSON
                    logger.info("Auto-detected JSON mode")
                    return
                except (json.JSONDecodeError, ValueError):
                    pass

            # Check if it looks like structured logs (has log patterns)
            if self.LOG_PATTERN.search(text):
                self.detected_mode = ParserMode.PLAIN_TEXT
                logger.info("Auto-detected plain text mode")
                return

            # Check if it contains printable ASCII/text characters
            # If most bytes are printable, it's likely text
            printable_count = sum(1 for b in self.buffer[:100] if 32 <= b <= 126 or b in (9, 10, 13))
            if printable_count > len(self.buffer[:100]) * 0.8:  # 80% printable
                self.detected_mode = ParserMode.PLAIN_TEXT
                logger.info("Auto-detected plain text mode (high printable ratio)")
                return

            # Default to plain text for safety
            self.detected_mode = ParserMode.PLAIN_TEXT
            logger.info("Auto-detected plain text mode (default)")
            
        except UnicodeDecodeError:
            # Check if it might still be text with errors
            text_with_errors = self.buffer.decode("utf-8", errors="replace")
            printable_count = sum(1 for b in self.buffer[:100] if 32 <= b <= 126 or b in (9, 10, 13))
            
            if printable_count > len(self.buffer[:100]) * 0.5:  # 50% printable
                self.detected_mode = ParserMode.PLAIN_TEXT
                logger.info("Auto-detected plain text mode (with decode errors)")
            else:
                # Likely binary data
                self.detected_mode = ParserMode.BINARY
                logger.info("Auto-detected binary mode")

    def _parse_plain_text(self) -> Iterator[Event]:
        """Parse plain text logs."""
        try:
            text = self.buffer.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to decode text: {e}")
            self.buffer.clear()
            return

        lines = text.split("\n")
        # Keep incomplete line in buffer
        if not text.endswith("\n"):
            self.buffer = bytearray(lines[-1].encode("utf-8"))
            lines = lines[:-1]
        else:
            self.buffer.clear()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to extract log level
            match = self.LOG_PATTERN.search(line)
            if match:
                level_str = match.group("level").upper()
                message = match.group("message").strip()
                try:
                    level = LogLevel(level_str)
                except ValueError:
                    level = LogLevel.INFO

                yield Event(
                    type=EventType.LOG,
                    level=level,
                    data={"message": message},
                    raw=line,
                )
            else:
                # Plain message without level - check if it's JSON
                try:
                    json_data = json.loads(line)
                    # It's valid JSON
                    event_type = EventType.LOG
                    if isinstance(json_data, dict):
                        if "type" in json_data:
                            try:
                                event_type = EventType(json_data["type"])
                            except ValueError:
                                pass
                        # Check for numeric values (likely metrics)
                        if any(isinstance(v, (int, float)) for v in json_data.values() if v != "type"):
                            if event_type == EventType.LOG:
                                event_type = EventType.METRIC
                        # Extract level if present
                        level = None
                        if "level" in json_data:
                            try:
                                level = LogLevel(json_data["level"].upper())
                            except ValueError:
                                pass
                    
                    yield Event(
                        type=event_type,
                        level=level,
                        data=json_data if isinstance(json_data, dict) else {"value": json_data},
                        raw=line,
                    )
                except json.JSONDecodeError:
                    # Not JSON, treat as plain text
                    yield Event(
                        type=EventType.LOG,
                        level=LogLevel.INFO,
                        data={"message": line},
                        raw=line,
                    )

    def _parse_json(self) -> Iterator[Event]:
        """Parse JSON logs."""
        try:
            text = self.buffer.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Failed to decode JSON: {e}")
            self.buffer.clear()
            return

        lines = text.split("\n")
        # Keep incomplete line in buffer
        if not text.endswith("\n"):
            self.buffer = bytearray(lines[-1].encode("utf-8"))
            lines = lines[:-1]
        else:
            self.buffer.clear()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                event_type = EventType.LOG

                # Check if it's a metric
                if isinstance(data, dict):
                    if "type" in data:
                        try:
                            event_type = EventType(data["type"])
                        except ValueError:
                            pass

                    # Check for numeric values (likely metrics)
                    if any(isinstance(v, (int, float)) for v in data.values() if v != "type"):
                        if event_type == EventType.LOG:
                            event_type = EventType.METRIC

                    # Extract level if present
                    level = None
                    if "level" in data:
                        try:
                            level = LogLevel(data["level"].upper())
                        except ValueError:
                            pass

                yield Event(
                    type=event_type,
                    level=level,
                    data=data if isinstance(data, dict) else {"value": data},
                    raw=line,
                )
            except json.JSONDecodeError:
                # Invalid JSON, treat as plain text
                yield Event(
                    type=EventType.LOG,
                    level=LogLevel.INFO,
                    data={"message": line},
                    raw=line,
                )

    def _parse_binary(self) -> Iterator[Event]:
        """
        Parse binary packets.

        Expected format: [HEADER][LEN][PAYLOAD][CRC]
        This is a simplified implementation - can be extended.
        """
        # Check if buffer looks like text (safety check)
        if len(self.buffer) > 0:
            printable_count = sum(1 for b in self.buffer[:min(100, len(self.buffer))] if 32 <= b <= 126 or b in (9, 10, 13))
            if printable_count > len(self.buffer[:min(100, len(self.buffer))]) * 0.7:
                # Looks like text, switch to plain text mode
                logger.warning("Binary parser detected text data, switching to plain text mode")
                self.detected_mode = ParserMode.PLAIN_TEXT
                yield from self._parse_plain_text()
                return

        # Simple binary parser - expects packets with length prefix
        # Only process if we have enough data and it doesn't look like text
        while len(self.buffer) >= 2:
            # Assume first byte is length
            packet_len = self.buffer[0]
            
            # Validate packet length (reasonable range)
            if packet_len == 0 or packet_len > 200:  # Reduced max to avoid false positives
                # Check if this might be text starting with a character
                if 32 <= self.buffer[0] <= 126:  # Printable ASCII
                    # Likely text, switch modes
                    logger.warning("Binary parser detected text-like data, switching to plain text mode")
                    self.detected_mode = ParserMode.PLAIN_TEXT
                    yield from self._parse_plain_text()
                    return
                # Invalid, skip one byte and retry
                self.buffer.pop(0)
                continue

            if len(self.buffer) < packet_len + 1:
                # Incomplete packet, wait for more data
                break

            # Extract packet
            payload = bytes(self.buffer[1 : packet_len + 1])
            self.buffer = self.buffer[packet_len + 1 :]

            yield Event(
                type=EventType.PACKET,
                data={"payload": payload.hex(), "length": len(payload)},
                raw=payload.hex(),
            )

    def reset(self) -> None:
        """Reset parser state."""
        self.buffer.clear()
        self.detected_mode = None
