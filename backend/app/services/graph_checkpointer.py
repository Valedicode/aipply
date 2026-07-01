"""
LangGraph checkpointer factory.

Mirrors the singleton + override pattern used by
``app.services.generic_session_manager.get_session_manager``: a thread-safe
lazy initialiser returns the in-process default; ``configure_checkpointer``
swaps in a different backend (e.g. PostgresSaver) at application startup.

The default backend is ``InMemorySaver`` so the orchestrator works out of the
box for development without provisioning Postgres. Production deployments can
call ``configure_checkpointer(PostgresSaver(conn))`` from the FastAPI lifespan
context manager; ``langgraph-checkpoint-postgres`` is already declared in
``backend/requirements.txt``.

thread_id == session_id throughout the codebase.
"""

from __future__ import annotations

import threading
from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver


_checkpointer: Optional[BaseCheckpointSaver] = None
_checkpointer_lock = threading.Lock()


def get_checkpointer() -> BaseCheckpointSaver:
    """
    Return the global checkpointer instance, creating an InMemorySaver on
    first call.

    Thread-safe via double-checked locking so concurrent requests during
    startup cannot construct two checkpointers.
    """
    global _checkpointer

    if _checkpointer is None:
        with _checkpointer_lock:
            if _checkpointer is None:
                _checkpointer = InMemorySaver()

    return _checkpointer


def configure_checkpointer(saver: BaseCheckpointSaver) -> None:
    """
    Replace the global checkpointer.

    Intended for application startup (e.g. wiring up PostgresSaver) and for
    tests that need a fresh, isolated checkpointer per case.
    """
    global _checkpointer
    with _checkpointer_lock:
        _checkpointer = saver


def reset_checkpointer() -> None:
    """Drop the global checkpointer reference. Mainly used by tests."""
    global _checkpointer
    with _checkpointer_lock:
        _checkpointer = None
