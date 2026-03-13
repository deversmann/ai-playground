"""
Memory systems for conversation context management.

This package provides short-term (in-memory) conversation memory for
multi-turn conversations. Future phases will add long-term (database)
and semantic (vector) memory.

Exports:
    ShortTermMemory: Single conversation's message queue (deque-based)
    MemoryManager: Thread-safe multi-session coordinator
"""

from .manager import MemoryManager
from .short_term import ShortTermMemory

__all__ = ["ShortTermMemory", "MemoryManager"]
