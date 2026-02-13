"""Integration tests for serial communication (requires mock)."""

import pytest

from serialscope.core.event import LogLevel
from serialscope.core.parser import ParserMode, StreamParser
from serialscope.core.serial_manager import SerialManager


class TestSerialIntegration:
    """Integration tests for serial communication."""

    def test_serial_manager_list_ports(self):
        """Test listing available serial ports."""
        ports = SerialManager.list_ports()
        # Should return a list (may be empty if no ports available)
        assert isinstance(ports, list)

    def test_parser_with_serial_data(self):
        """Test parser with simulated serial data."""
        parser = StreamParser(mode=ParserMode.PLAIN_TEXT)

        # Simulate serial data stream
        chunks = [
            b"[INFO] Starting",
            b" system\n",
            b"[WARN] Low battery\n",
            b"[ERROR] Sensor",
            b" timeout\n",
        ]

        all_events = []
        for chunk in chunks:
            events = list(parser.parse(chunk))
            all_events.extend(events)

        # Should have 3 complete events
        assert len(all_events) == 3
        assert all_events[0].level == LogLevel.INFO
        assert all_events[1].level == LogLevel.WARN
        assert all_events[2].level == LogLevel.ERROR
