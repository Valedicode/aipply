"""
LangGraph-based orchestrator for JobWriterAI.

Three entry points (job_tailoring, cv_review, discovery) are exposed through a
single StateGraph. Workflow state lives in a LangGraph checkpointer keyed by
thread_id == session_id. Human-in-the-loop approval is modelled as structured
LangGraph interrupts surfaced to the frontend as GatePayload dicts.

Public surface:
- OrchestratorState   : the TypedDict carried through every node
- GatePayload         : structured interrupt emitted by approval/choice nodes
- GateResolution      : the user's reply to a GatePayload
- build_graph()       : compile the orchestrator graph against a checkpointer
"""

from app.agents.orchestrator.gates import (
    GateAction,
    GateKind,
    GatePayload,
    GateResolution,
)
from app.agents.orchestrator.graph import build_graph
from app.agents.orchestrator.state import OrchestratorState

__all__ = [
    "OrchestratorState",
    "GatePayload",
    "GateResolution",
    "GateKind",
    "GateAction",
    "build_graph",
]
