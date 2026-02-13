"""
Base plugin system for extensibility.

Allows registering custom handlers for events, enabling features like:
- IMU visualizer
- GPS map plotter
- WiFi monitor
- Custom packet decoder
- AI anomaly detection
"""

import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from serialscope.core.event import Event

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """
    Base class for plugins.

    Plugins can process events and extend functionality.
    """

    def __init__(self, name: str):
        """
        Initialize plugin.

        Args:
            name: Unique plugin name
        """
        self.name = name
        self.enabled = True

    @abstractmethod
    def process(self, event: Event) -> Optional[Event]:
        """
        Process an event.

        Args:
            event: Event to process

        Returns:
            Modified event, or None to drop event
        """
        pass

    def on_start(self) -> None:
        """Called when plugin is enabled."""
        pass

    def on_stop(self) -> None:
        """Called when plugin is disabled."""
        pass


class PluginRegistry:
    """
    Registry for managing plugins.

    Example usage:
        @register_plugin("imu_decoder")
        def imu_handler(event):
            ...
    """

    def __init__(self):
        """Initialize plugin registry."""
        self.plugins: Dict[str, Plugin] = {}
        self.handlers: List[Callable[[Event], Optional[Event]]] = []

    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register
        """
        if plugin.name in self.plugins:
            logger.warning(f"Plugin {plugin.name} already registered, overwriting")
        self.plugins[plugin.name] = plugin
        plugin.on_start()
        logger.info(f"Registered plugin: {plugin.name}")

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin.

        Args:
            name: Plugin name
        """
        if name in self.plugins:
            plugin = self.plugins[name]
            plugin.on_stop()
            del self.plugins[name]
            logger.info(f"Unregistered plugin: {name}")

    def register_handler(self, handler: Callable[[Event], Optional[Event]]) -> None:
        """
        Register a simple handler function.

        Args:
            handler: Function that processes events
        """
        self.handlers.append(handler)

    def process(self, event: Event) -> Optional[Event]:
        """
        Process event through all registered plugins and handlers.

        Args:
            event: Event to process

        Returns:
            Processed event, or None if dropped
        """
        # Process through plugins
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            try:
                event = plugin.process(event)
                if event is None:
                    return None  # Event was dropped
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}: {e}", exc_info=True)

        # Process through handlers
        for handler in self.handlers:
            try:
                event = handler(event)
                if event is None:
                    return None  # Event was dropped
            except Exception as e:
                logger.error(f"Error in handler: {e}", exc_info=True)

        return event


# Global plugin registry instance
_registry = PluginRegistry()


def register_plugin(name: str) -> Callable:
    """
    Decorator to register a plugin handler.

    Example:
        @register_plugin("imu_decoder")
        def imu_handler(event: Event) -> Optional[Event]:
            if event.type == EventType.METRIC and "imu" in event.data:
                # Process IMU data
                pass
            return event
    """

    def decorator(func: Callable[[Event], Optional[Event]]) -> Callable[[Event], Optional[Event]]:
        _registry.register_handler(func)
        logger.info(f"Registered handler plugin: {name}")
        return func

    return decorator
