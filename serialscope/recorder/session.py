"""
Session recorder and replayer.

Allows saving and replaying debug sessions for post-analysis.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from serialscope.core.event import Event

logger = logging.getLogger(__name__)


class SessionRecorder:
    """
    Records events to a session file.

    Useful for:
    - Debugging field logs
    - Reproducing bugs
    - Sharing with teammates
    """

    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize recorder.

        Args:
            output_path: Path to save session file. If None, auto-generates name.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = f"sessions/session_{timestamp}.log"

        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = None
        self.event_count = 0

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def start(self) -> None:
        """Start recording."""
        self.file_handle = open(self.output_path, "w", encoding="utf-8")
        logger.info(f"Started recording to {self.output_path}")

    def stop(self) -> None:
        """Stop recording."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            logger.info(f"Stopped recording. Saved {self.event_count} events to {self.output_path}")

    def record(self, event: Event) -> None:
        """
        Record an event.

        Args:
            event: Event to record
        """
        if not self.file_handle:
            raise RuntimeError("Recorder not started. Call start() first.")

        event_dict = event.to_dict()
        line = json.dumps(event_dict, ensure_ascii=False)
        self.file_handle.write(line + "\n")
        self.file_handle.flush()
        self.event_count += 1


class SessionReplayer:
    """
    Replays events from a session file.

    Usage:
        serialscope --replay session.log
    """

    def __init__(self, session_path: str, speed: float = 1.0):
        """
        Initialize replayer.

        Args:
            session_path: Path to session file
            speed: Playback speed multiplier (1.0 = real-time, 2.0 = 2x speed)
        """
        self.session_path = Path(session_path)
        if not self.session_path.exists():
            raise FileNotFoundError(f"Session file not found: {session_path}")

        self.speed = speed
        self.file_handle = None
        self.last_timestamp: Optional[datetime] = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def start(self) -> None:
        """Start replay."""
        self.file_handle = open(self.session_path, "r", encoding="utf-8")
        logger.info(f"Started replaying from {self.session_path}")

    def stop(self) -> None:
        """Stop replay."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def events(self) -> Iterator[Event]:
        """
        Generate events from session file.

        Yields:
            Event objects with preserved timestamps
        """
        if not self.file_handle:
            raise RuntimeError("Replayer not started. Call start() first.")

        import time

        self.file_handle.seek(0)
        for line in self.file_handle:
            line = line.strip()
            if not line:
                continue

            try:
                event_dict = json.loads(line)
                event = Event.from_dict(event_dict)

                # Maintain timing between events
                if self.last_timestamp and self.speed > 0:
                    delta = (event.timestamp - self.last_timestamp).total_seconds()
                    sleep_time = delta / self.speed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                self.last_timestamp = event.timestamp
                yield event

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse event: {e}")
                continue
