"""
Plugin architecture for extensibility.

Allows registering custom handlers for events.
"""

from serialscope.plugins.base import Plugin, PluginRegistry

__all__ = ["Plugin", "PluginRegistry"]
