"""
Discovery flow nodes (placeholder).

The discovery experience (Phase 5/6) has not been built yet. We reserve an
entry point in the graph so wiring exists from day one and the eventual
implementation drops into the same node slot without re-architecting the API
or the frontend router.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from app.agents.orchestrator.state import OrchestratorState


DISC_STUB = "discovery_stub"


def discovery_stub(state: OrchestratorState) -> dict[str, Any]:
    text = (
        "The career-discovery experience is not yet available. "
        "This entry point exists so the orchestrator can route to it as soon "
        "as the discovery flow is implemented."
    )
    return {
        "last_narration": text,
        "messages": [AIMessage(content=text)],
        "pending_gate": None,
    }
