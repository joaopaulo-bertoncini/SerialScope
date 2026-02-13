"""Unit tests for Event module."""

import json
from datetime import datetime

import pytest

from serialscope.core.event import Event, EventType, LogLevel


class TestEvent:
    """Test Event class."""

    def test_event_creation(self):
        """Test basic event creation."""
        event = Event(
            type=EventType.LOG,
            level=LogLevel.INFO,
            data={"message": "Test message"},
        )
        assert event.type == EventType.LOG
        assert event.level == LogLevel.INFO
        assert event.data["message"] == "Test message"
        assert isinstance(event.timestamp, datetime)

    def test_event_to_dict(self):
        """Test event serialization."""
        event = Event(
            type=EventType.METRIC,
            level=None,
            data={"temp": 42.3, "voltage": 3.28},
        )
        event_dict = event.to_dict()
        assert event_dict["type"] == "metric"
        assert event_dict["level"] is None
        assert event_dict["data"]["temp"] == 42.3
        assert "timestamp" in event_dict

    def test_event_from_dict(self):
        """Test event deserialization."""
        event_dict = {
            "type": "log",
            "timestamp": "2026-02-12T10:30:00",
            "level": "INFO",
            "data": {"message": "Test"},
            "raw": None,
            "source": None,
        }
        event = Event.from_dict(event_dict)
        assert event.type == EventType.LOG
        assert event.level == LogLevel.INFO
        assert event.data["message"] == "Test"

    def test_event_is_error(self):
        """Test error detection."""
        error_event = Event(type=EventType.LOG, level=LogLevel.ERROR)
        assert error_event.is_error()

        info_event = Event(type=EventType.LOG, level=LogLevel.INFO)
        assert not info_event.is_error()

    def test_event_is_warning(self):
        """Test warning detection."""
        warn_event = Event(type=EventType.LOG, level=LogLevel.WARN)
        assert warn_event.is_warning()

        info_event = Event(type=EventType.LOG, level=LogLevel.INFO)
        assert not info_event.is_warning()

    def test_event_level_inference(self):
        """Test automatic level inference from data."""
        event = Event(
            type=EventType.LOG,
            data={"level": "ERROR", "message": "Error occurred"},
        )
        assert event.level == LogLevel.ERROR
