"""
CLI package for AI Chatbot.

This package provides an interactive command-line interface for chatting
with the AI. It uses Rich for beautiful terminal output and Prompt Toolkit
for advanced input handling.

Main components:
- client: HTTP client for API communication
- interface: Interactive chat interface
- main: CLI entry point

Usage:
    poetry run python -m cli.main
"""

from .client import APIClient, APIClientError
from .interface import ChatInterface

__all__ = ["APIClient", "APIClientError", "ChatInterface"]
