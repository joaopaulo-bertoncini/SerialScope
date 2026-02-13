"""Unit tests for StreamParser."""

import pytest

from serialscope.core.event import EventType, LogLevel
from serialscope.core.parser import ParserMode, StreamParser


class TestStreamParser:
    """Test StreamParser class."""

    def test_parse_plain_text(self):
        """Test plain text parsing."""
        parser = StreamParser(mode=ParserMode.PLAIN_TEXT)
        data = b"[INFO] Boot complete\n[ERROR] Sensor failed\n"
        events = list(parser.parse(data))
        assert len(events) == 2
        assert events[0].level == LogLevel.INFO
        assert events[1].level == LogLevel.ERROR

    def test_parse_json(self):
        """Test JSON parsing."""
        parser = StreamParser(mode=ParserMode.JSON)
        data = b'{"level":"INFO","temp":42.3}\n{"level":"ERROR","message":"Failed"}\n'
        events = list(parser.parse(data))
        assert len(events) == 2
        assert events[0].data["temp"] == 42.3

    def test_parse_incomplete_line(self):
        """Test handling of incomplete lines."""
        parser = StreamParser(mode=ParserMode.PLAIN_TEXT)
        data = b"[INFO] Incomplete"
        events = list(parser.parse(data))
        # Should not yield event for incomplete line
        assert len(events) == 0
        # Next complete line should work
        data2 = b" line\n"
        events2 = list(parser.parse(data2))
        assert len(events2) == 1

    def test_auto_detect_json(self):
        """Test auto-detection of JSON mode."""
        parser = StreamParser(mode=ParserMode.AUTO)
        data = b'{"type":"metric","temp":42}\n'
        events = list(parser.parse(data))
        assert len(events) == 1
        assert parser.detected_mode == ParserMode.JSON

    def test_auto_detect_plain_text(self):
        """Test auto-detection of plain text mode."""
        parser = StreamParser(mode=ParserMode.AUTO)
        data = b"[INFO] Test message\n"
        events = list(parser.parse(data))
        assert len(events) == 1
        assert parser.detected_mode == ParserMode.PLAIN_TEXT

    def test_reset(self):
        """Test parser reset."""
        parser = StreamParser(mode=ParserMode.PLAIN_TEXT)
        parser.parse(b"Partial")
        parser.reset()
        assert len(parser.buffer) == 0
        assert parser.detected_mode is None
