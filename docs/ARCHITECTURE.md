# Architecture Documentation

## Overview

SerialScope follows a modular architecture that separates concerns into distinct layers. This design enables extensibility, testability, and maintainability.

## Core Philosophy

Instead of treating serial output as plain text, we treat it as a **structured event stream**. This abstraction allows:

- Smart filtering
- Data extraction
- Visualization
- Replay
- Post-analysis

This moves debugging from **print debugging → observability**.

## Architecture Layers

### 1. Serial Interface Layer (`core/serial_manager.py`)

**Responsibilities:**
- Open/close serial port
- Auto-detect device
- Auto-reconnect on disconnect
- Handle timeouts
- Thread-safe read/write operations

**Key Features:**
- Thread-safe operations using locks
- Background reading thread
- Callback system for data notifications
- Queue-based data buffering

**Future Enhancements:**
- USB hot-plug detection
- Multiple serial devices support

### 2. Stream Parser Layer (`core/parser.py`)

**Responsibilities:**
- Convert raw bytes into structured events
- Support multiple parsing modes
- Handle incomplete data (buffering)

**Supported Modes:**

1. **Plain Text**: `[INFO] Boot complete`
2. **JSON**: `{"level":"INFO","temp":42.3}`
3. **Binary**: `[HEADER][LEN][PAYLOAD][CRC]`
4. **Auto**: Attempts to detect format automatically

**Parser Output:**

All formats are converted into unified `Event` objects:

```python
Event(
    type="log" | "metric" | "packet",
    level="INFO",
    data={...},
    timestamp=...
)
```

### 3. Event Abstraction (`core/event.py`)

The `Event` class is the core abstraction that unifies all data formats:

```python
@dataclass
class Event:
    type: EventType          # LOG, METRIC, or PACKET
    timestamp: datetime      # When the event occurred
    level: Optional[LogLevel]  # DEBUG, INFO, WARN, ERROR, etc.
    data: Dict[str, Any]     # Structured data
    raw: Optional[str]       # Original raw data
    source: Optional[str]     # Source identifier
```

**Why This Matters:**

This abstraction enables:
- Uniform processing regardless of input format
- Easy serialization for recording/replay
- Plugin system extensibility
- Filtering and routing logic

### 4. UI Layer (`ui/`)

**Components:**

- **Dashboard** (`dashboard.py`): Main application window
- **LogPanel** (`log_panel.py`): Log display with filtering
- **MetricsPanel**: Real-time telemetry display

**Layout:**

```
+------------------------------------------------+
| SerialScope                                    |
+----------------------+-------------------------+
| Logs                 | System Metrics         |
|----------------------|------------------------|
| [INFO] Boot OK       | Temp: 42.3 °C          |
| [WARN] Low battery   | Voltage: 3.28 V        |
|                      | WiFi RSSI: -62 dBm     |
+----------------------+------------------------+
| Command Input:                                |
+------------------------------------------------+
```

**Technologies:**
- [Textual](https://textual.textualize.io/): Modern terminal UI framework
- [Rich](https://rich.readthedocs.io/): Beautiful terminal formatting

### 5. Recorder/Replay System (`recorder/session.py`)

**SessionRecorder:**
- Saves events to JSON lines format
- Auto-generates filenames with timestamps
- Thread-safe writing

**SessionReplayer:**
- Reads events from session files
- Maintains timing between events
- Supports speed adjustment

**File Format:**

Each line is a JSON-encoded event:

```json
{"type":"log","timestamp":"2026-02-12T10:30:00","level":"INFO","data":{"message":"Boot complete"},"raw":"[INFO] Boot complete","source":null}
```

### 6. Plugin System (`plugins/base.py`)

**Architecture:**

- `Plugin` base class for custom plugins
- `PluginRegistry` for managing plugins
- Decorator-based registration: `@register_plugin("name")`

**Use Cases:**
- IMU visualizer
- GPS map plotter
- WiFi monitor
- Custom packet decoder
- AI anomaly detection

**Example:**

```python
@register_plugin("imu_decoder")
def imu_handler(event: Event) -> Optional[Event]:
    if event.type == EventType.METRIC and "imu" in event.data:
        # Process IMU data
        pass
    return event
```

## Data Flow

```
Serial Port
    |
    v
SerialManager (thread-safe reading)
    |
    v
Raw Bytes Queue
    |
    v
StreamParser (mode: plain/json/binary/auto)
    |
    v
Event Objects
    |
    +---> PluginRegistry (process events)
    |
    +---> Dashboard UI (display)
    |
    +---> SessionRecorder (save to file)
```

## Threading Model

### Serial Reading Thread

- Background thread reads from serial port
- Data is queued for processing
- Callbacks notify registered handlers

### Main Thread

- Runs UI event loop (Textual)
- Processes events from queue
- Updates display

### Thread Safety

- Serial operations use locks
- Queue-based communication
- No shared mutable state

## Error Handling

### Serial Errors

- Auto-reconnect on disconnect
- Timeout handling
- Graceful degradation

### Parser Errors

- Invalid JSON → fallback to plain text
- Corrupted binary → skip packet
- Incomplete data → buffer for next read

### UI Errors

- Exception handling in callbacks
- Error notifications to user
- Graceful shutdown

## Extension Points

### Adding a New Parser Mode

1. Extend `ParserMode` enum
2. Add parsing method to `StreamParser`
3. Update auto-detection logic

### Adding a Plugin

1. Create plugin class or function
2. Register with `PluginRegistry`
3. Process events in `process()` method

### Adding a UI Component

1. Create widget class (inherit from Textual widget)
2. Add to dashboard layout
3. Register event handlers

## Performance Considerations

### Memory Management

- Bounded log buffer (deque with maxlen)
- Streaming parser (processes incrementally)
- Session files written incrementally

### CPU Usage

- Non-blocking serial reads
- Efficient regex matching
- Lazy UI updates

### I/O Optimization

- Buffered file writes
- Batch event processing
- Efficient serial port access

## Security Considerations

### Serial Port Access

- Requires appropriate permissions
- No authentication (local device)
- Input validation on parsed data

### Session Files

- No sensitive data by default
- User controls what's recorded
- Plain text format (can be encrypted if needed)

## Testing Strategy

### Unit Tests

- Test individual components in isolation
- Mock external dependencies (serial port)
- Test edge cases and error conditions

### Integration Tests

- Test component interactions
- Simulated serial data
- End-to-end workflows

### Future: Hardware Tests

- Real device testing
- Stress testing
- Corrupted packet injection

## Deployment

### Docker

- Multi-stage build for smaller image
- Privileged mode for serial access
- Volume mounts for sessions

### CI/CD

- Automated testing
- Code quality checks
- Security scanning

## Future Architecture Enhancements

1. **Web Dashboard**: FastAPI + WebSocket for remote access
2. **MQTT Bridge**: Publish events to MQTT broker
3. **Prometheus Exporter**: Metrics endpoint for monitoring
4. **Distributed Mode**: Multiple devices, centralized dashboard
5. **AI Integration**: Anomaly detection, pattern recognition
