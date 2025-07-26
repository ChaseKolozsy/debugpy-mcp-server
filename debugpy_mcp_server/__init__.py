"""
Debugpy MCP Server

A Model Context Protocol server for debugging Python programs using debugpy.
"""

__version__ = "1.0.0"
__author__ = "aXaTT Team"
__email__ = "team@axatt.dev"

from .server import DebugpyMCPServer

__all__ = ["DebugpyMCPServer"] 