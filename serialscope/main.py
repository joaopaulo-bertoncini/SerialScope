"""
Main CLI entry point for SerialScope.

Usage:
    serialscope --port auto --baud 115200
    serialscope --filter ERROR
    serialscope --json
    serialscope --record
    serialscope --replay session.log
    serialscope --plot temp
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

from serialscope.core.parser import ParserMode
from serialscope.core.serial_manager import SerialManager
from serialscope.recorder.session import SessionRecorder, SessionReplayer
from serialscope.ui.dashboard import Dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def setup_signal_handlers(serial_manager: SerialManager) -> None:
    """Setup signal handlers for graceful shutdown."""

    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, shutting down...")
        serial_manager.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SerialScope - Serial Telemetry & Debug Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  serialscope --port auto --baud 115200
  serialscope --port /dev/ttyUSB0 --filter ERROR
  serialscope --json --record
  serialscope --replay session_2026-02-12.log
  serialscope --plot temp voltage
        """,
    )

    # Serial connection options
    parser.add_argument(
        "--port",
        type=str,
        default="auto",
        help="Serial port (e.g., /dev/ttyUSB0, COM3, or 'auto' for auto-detection)",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Serial baud rate (default: 115200). Common values: 9600, 115200, 230400, 460800",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Serial read timeout in seconds (default: 1.0)",
    )

    # Parser options
    parser.add_argument(
        "--mode",
        type=str,
        choices=["plain", "json", "binary", "auto"],
        default="auto",
        help="Parser mode (default: auto)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Force JSON parsing mode (shortcut for --mode json)",
    )

    # Filtering options
    parser.add_argument(
        "--filter",
        type=str,
        help="Filter logs by level (e.g., ERROR, WARN, INFO)",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search/highlight pattern (regex)",
    )

    # Recording/replay options
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record session to file",
    )
    parser.add_argument(
        "--record-file",
        type=str,
        help="Path to record file (default: auto-generated)",
    )
    parser.add_argument(
        "--replay",
        type=str,
        help="Replay session from file",
    )
    parser.add_argument(
        "--replay-speed",
        type=float,
        default=1.0,
        help="Replay speed multiplier (default: 1.0)",
    )

    # UI options
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Disable TUI, output to stdout",
    )
    parser.add_argument(
        "--plot",
        nargs="+",
        help="Metrics to plot (e.g., --plot temp voltage)",
    )

    # Debug options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine parser mode
    parser_mode = ParserMode.JSON if args.json else ParserMode(args.mode)

    # Replay mode
    if args.replay:
        logger.info(f"Replaying session from {args.replay}")
        replayer = SessionReplayer(args.replay, speed=args.replay_speed)
        dashboard = Dashboard()

        with replayer:
            dashboard.on_mount()
            for event in replayer.events():
                dashboard.add_event(event)
                # Note: In a real implementation, we'd need to handle UI updates properly

        return

    # Normal operation mode
    serial_manager = SerialManager(
        port=args.port if args.port != "auto" else None,
        baudrate=args.baud,
        timeout=args.timeout,
    )

    setup_signal_handlers(serial_manager)

    # Connect to serial port
    if not serial_manager.connect():
        logger.error("Failed to connect to serial port")
        sys.exit(1)

    # Setup recorder if requested
    recorder = None
    if args.record:
        recorder = SessionRecorder(args.record_file)
        recorder.start()

    try:
        # Initialize parser
        from serialscope.core.parser import StreamParser

        parser_instance = StreamParser(mode=parser_mode)

        # Setup UI or stdout output
        if args.no_ui:
            # Simple stdout output
            serial_manager.start_reading()
            while True:
                data = serial_manager.read(timeout=1.0)
                if data:
                    for event in parser_instance.parse(data):
                        if recorder:
                            recorder.record(event)
                        print(f"[{event.level.value if event.level else 'INFO'}] {event.data}")
        else:
            # TUI mode
            dashboard = Dashboard()

            # Setup event handler
            def on_serial_data(data: bytes):
                for event in parser_instance.parse(data):
                    if recorder:
                        recorder.record(event)
                    dashboard.add_event(event)

            serial_manager.register_callback(on_serial_data)
            serial_manager.start_reading()

            # Run dashboard
            dashboard.run()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        if recorder:
            recorder.stop()
        serial_manager.disconnect()


if __name__ == "__main__":
    main()
