"""
Serial interface layer.

Handles low-level serial communication with thread-safe operations,
auto-detection, auto-reconnect, and timeout management.
"""

import logging
import serial
import serial.tools.list_ports
import threading
import time
from queue import Queue, Empty
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class SerialManager:
    """
    Thread-safe serial port manager.

    Responsibilities:
    - Open/close serial port
    - Auto-detect device
    - Auto-reconnect on disconnect
    - Handle timeouts
    - Thread-safe read/write operations
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 1.0,
        auto_reconnect: bool = True,
        reconnect_delay: float = 2.0,
    ):
        """
        Initialize serial manager.

        Args:
            port: Serial port name (e.g., '/dev/ttyUSB0' or 'COM3')
                 If None or 'auto', will attempt auto-detection
            baudrate: Serial baud rate (default: 115200)
            timeout: Read timeout in seconds
            auto_reconnect: Enable automatic reconnection on disconnect
            reconnect_delay: Delay between reconnection attempts (seconds)
        """
        self.port_name = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay

        self.serial_conn: Optional[serial.Serial] = None
        self.is_running = False
        self.read_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        self.data_queue: Queue[bytes] = Queue()
        self.callbacks: list[Callable[[bytes], None]] = []

    def register_callback(self, callback: Callable[[bytes], None]) -> None:
        """Register a callback to receive serial data."""
        self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[bytes], None]) -> None:
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def _notify_callbacks(self, data: bytes) -> None:
        """Notify all registered callbacks with new data."""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback: {e}", exc_info=True)

    @staticmethod
    def list_ports() -> list[Any]:
        """List all available serial ports."""
        return list(serial.tools.list_ports.comports())

    @staticmethod
    def auto_detect_port() -> Optional[str]:
        """
        Attempt to auto-detect ESP32/STM32 device.

        Looks for common USB-to-serial chip identifiers.
        """
        ports = serial.tools.list_ports.comports()
        esp32_keywords = ["ch340", "ch341", "cp210", "ft232", "ch9102"]

        for port_info in ports:
            description = (port_info.description or "").lower()
            hwid = (port_info.hwid or "").lower()

            # Check if it matches common ESP32 USB-to-serial chips
            if any(keyword in description or keyword in hwid for keyword in esp32_keywords):
                return port_info.device

        # Fallback: return first available port if any
        if ports:
            logger.warning(f"Auto-detection failed, using first available port: {ports[0].device}")
            return ports[0].device

        return None

    def connect(self) -> bool:
        """
        Connect to serial port.

        Returns:
            True if connection successful, False otherwise
        """
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                logger.warning("Already connected")
                return True

            # Auto-detect if needed
            port = self.port_name
            if port is None or port.lower() == "auto":
                port = self.auto_detect_port()
                if port is None:
                    logger.error("No serial port found")
                    return False
                logger.info(f"Auto-detected port: {port}")

            try:
                self.serial_conn = serial.Serial(
                    port=port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.timeout,
                )
                self.port_name = port
                logger.info(f"Connected to {port} at {self.baudrate} baud")
                return True
            except serial.SerialException as e:
                logger.error(f"Failed to connect to {port}: {e}")
                return False

    def disconnect(self) -> None:
        """Disconnect from serial port."""
        with self.lock:
            self.is_running = False
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=2.0)

            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                logger.info("Disconnected from serial port")

    def start_reading(self) -> None:
        """Start background thread for reading serial data."""
        if self.is_running:
            return

        if not self.serial_conn or not self.serial_conn.is_open:
            if not self.connect():
                raise RuntimeError("Failed to connect to serial port")

        self.is_running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        logger.info("Started serial reading thread")

    def stop_reading(self) -> None:
        """Stop background reading thread."""
        self.is_running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)

    def _read_loop(self) -> None:
        """Background thread loop for reading serial data."""
        while self.is_running:
            try:
                with self.lock:
                    if not self.serial_conn or not self.serial_conn.is_open:
                        if self.auto_reconnect:
                            logger.warning("Serial port closed, attempting reconnect...")
                            time.sleep(self.reconnect_delay)
                            if self.connect():
                                continue
                            else:
                                time.sleep(self.reconnect_delay)
                                continue
                        else:
                            break

                    # Read available data
                    if self.serial_conn.in_waiting > 0:
                        data = self.serial_conn.read(self.serial_conn.in_waiting)
                        self.data_queue.put(data)
                        self._notify_callbacks(data)

            except serial.SerialException as e:
                logger.error(f"Serial read error: {e}")
                if self.auto_reconnect:
                    time.sleep(self.reconnect_delay)
                    with self.lock:
                        if self.serial_conn:
                            try:
                                self.serial_conn.close()
                            except Exception:
                                pass
                        self.serial_conn = None
                else:
                    break
            except Exception as e:
                logger.error(f"Unexpected error in read loop: {e}", exc_info=True)
                time.sleep(0.1)

    def read(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """
        Read data from serial port (non-blocking).

        Args:
            timeout: Maximum time to wait for data (None = use default timeout)

        Returns:
            Bytes read, or None if timeout
        """
        try:
            return self.data_queue.get(timeout=timeout or self.timeout)
        except Empty:
            return None

    def write(self, data: bytes) -> int:
        """
        Write data to serial port.

        Args:
            data: Bytes to write

        Returns:
            Number of bytes written
        """
        with self.lock:
            if not self.serial_conn or not self.serial_conn.is_open:
                raise RuntimeError("Serial port not connected")

            try:
                return self.serial_conn.write(data)
            except serial.SerialException as e:
                logger.error(f"Serial write error: {e}")
                raise

    def is_connected(self) -> bool:
        """Check if serial port is connected."""
        with self.lock:
            return self.serial_conn is not None and self.serial_conn.is_open
