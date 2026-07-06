"""
Orchestrator API - thin REST shell around the LangGraph orchestrator.

Three endpoints:
- POST /api/orchestrator/start         : create thread + run until first gate
- POST /api/orchestrator/message       : resume with a gate resolution (or chat)
- GET  /api/orchestrator/state/{id}    : debug snapshot of the current thread

Thread / session identity:
    session_id (HTTP layer) == thread_id (LangGraph checkpointer key).

A single compiled graph instance is cached at module load time and reused
across requests. Per-session isolation is provided by the checkpointer.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from app.agents.orchestrator import GateResolution, build_graph
from app.models.schemas import (
    GeneratedFile,
    OrchestratorGatePayload,
    OrchestratorMessageRequest,
    OrchestratorResponse,
    OrchestratorStartRequest,
    OrchestratorStateResponse,
)
from app.services.generic_session_manager import get_session_manager

router = APIRouter(prefix="/api/orchestrator", tags=["Orchestrator"])


# --------------------------------------------------------------------------- #
# Cached graph singleton
# --------------------------------------------------------------------------- #

_graph = None


def _get_graph():
    """Lazy singleton so the graph is built at first use rather than import."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _thread_config(session_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


def _pending_gate_from_invoke_result(result: dict[str, Any]) -> OrchestratorGatePayload | None:
    """Extract the gate payload from the ``__interrupt__`` slot, if present."""
    interrupts = result.get("__interrupt__") if isinstance(result, dict) else None
    if not interrupts:
        return None
    first = interrupts[0]
    value = first.value if hasattr(first, "value") else first.get("value")  # type: ignore[union-attr]
    if not isinstance(value, dict):
        return None
    return OrchestratorGatePayload.model_validate(value)


def _files_from_state(state_values: dict[str, Any]) -> list[GeneratedFile]:
    raw = state_values.get("generated_files") or []
    return [GeneratedFile(**f) for f in raw if isinstance(f, dict)]


def _pending_gate_from_snapshot(snapshot: Any) -> OrchestratorGatePayload | None:
    """Extract the pending gate directly from a graph state snapshot's tasks."""
    if snapshot is None:
        return None
    for task in snapshot.tasks or []:
        for task_interrupt in task.interrupts or []:
            value = task_interrupt.value if hasattr(task_interrupt, "value") else None
            if isinstance(value, dict):
                try:
                    return OrchestratorGatePayload.model_validate(value)
                except Exception:
                    continue
    return None


def _snapshot_response(
    *,
    session_id: str,
    invoke_result: dict[str, Any],
) -> OrchestratorResponse:
    """Build an OrchestratorResponse from a graph.invoke() return value."""
    graph = _get_graph()
    snapshot = graph.get_state(_thread_config(session_id))
    state_values = snapshot.values if snapshot else {}

    gate = _pending_gate_from_invoke_result(invoke_result)
    files = _files_from_state(state_values)
    narration = (
        gate.narration if gate is not None
        else state_values.get("last_narration", "")
    )

    return OrchestratorResponse(
        success=True,
        session_id=session_id,
        narration=narration,
        pending_gate=gate,
        generated_files=files,
        done=gate is None,
        message="ok",
    )


# --------------------------------------------------------------------------- #
# POST /start
# --------------------------------------------------------------------------- #

@router.post(
    "/start",
    response_model=OrchestratorResponse,
    summary="Start an orchestrator session",
    description=(
        "Create a new graph thread and run until the first interrupt or END. "
        "Use the returned session_id with /message to resolve subsequent gates."
    ),
)
async def orchestrator_start(
    request: OrchestratorStartRequest,
) -> OrchestratorResponse:
    if request.flow == "job_tailoring" and not request.job_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="flow='job_tailoring' requires job_data.",
        )

    session_id = str(uuid.uuid4())
    # Run an opportunistic TTL sweep so long-lived dev servers do not leak
    # checkpointer state for abandoned sessions.
    session_manager = get_session_manager()
    session_manager.cleanup_expired_sessions()
    session_manager.register(session_id, request.flow)
    graph = _get_graph()
    initial_state = {
        "flow": request.flow,
        "cv_data": request.cv_data,
        "job_data": request.job_data,
        "company_data": request.company_data,
        "review_outputs": {},
        "generated_files": [],
        "messages": [],
        "last_narration": "",
        "pending_gate": None,
    }

    try:
        result = graph.invoke(initial_state, config=_thread_config(session_id))
    except GraphInterrupt as exc:
        # Defensive: graph.invoke() normally returns a state with __interrupt__
        # rather than raising, but we surface it cleanly either way.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph raised an unhandled interrupt: {exc}",
        ) from exc

    return _snapshot_response(session_id=session_id, invoke_result=result)


# --------------------------------------------------------------------------- #
# POST /message
# --------------------------------------------------------------------------- #

@router.post(
    "/message",
    response_model=OrchestratorResponse,
    summary="Send a message to the orchestrator",
    description=(
        "Resume a paused session with a structured gate resolution, or push a "
        "free-text chat turn (folded in as 'edit' feedback for the current "
        "gate when the gate allows edits). Returns the next narration and the "
        "next pending gate (if any)."
    ),
)
async def orchestrator_message(
    request: OrchestratorMessageRequest,
) -> OrchestratorResponse:
    graph = _get_graph()
    config = _thread_config(request.session_id)

    snapshot = graph.get_state(config)
    if snapshot is None or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired. Start a new session with /start.",
        )

    get_session_manager().touch(request.session_id)

    if request.kind == "gate_resolution":
        if request.resolution is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="kind='gate_resolution' requires a 'resolution' object.",
            )
        # Re-validate through the orchestrator-internal model to catch shape
        # issues missed by the API-layer Pydantic types (e.g. missing feedback
        # on action='edit').
        try:
            internal = GateResolution.model_validate(request.resolution.model_dump())
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid gate resolution: {exc}",
            ) from exc

        try:
            result = graph.invoke(Command(resume=internal.model_dump()), config=config)
        except GraphInterrupt as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Graph raised an unhandled interrupt: {exc}",
            ) from exc

        return _snapshot_response(session_id=request.session_id, invoke_result=result)

    # kind == "chat"
    if not (request.text and request.text.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="kind='chat' requires non-empty 'text'.",
        )

    pending = _pending_gate_from_snapshot(snapshot)

    if pending is None:
        # Nothing to resume - the run already reached END.
        return OrchestratorResponse(
            success=True,
            session_id=request.session_id,
            narration="This session has already finished. Start a new session to continue.",
            pending_gate=None,
            generated_files=_files_from_state(snapshot.values),
            done=True,
            message="ok",
        )

    if "edit" not in pending.allowed_actions:
        # This gate only supports approve/reject/choose - free text can't be
        # folded in automatically, so surface the allowed actions instead.
        actions = " / ".join(pending.allowed_actions)
        return OrchestratorResponse(
            success=True,
            session_id=request.session_id,
            narration=(
                f"This step doesn't accept free-form notes - please use one of the "
                f"available actions instead ({actions})."
            ),
            pending_gate=pending,
            generated_files=_files_from_state(snapshot.values),
            done=False,
            message="ok",
        )

    # Treat the free-text message as edit feedback for the currently pending
    # gate, so users can just type what they want changed instead of clicking
    # "Edit" first.
    try:
        internal = GateResolution.model_validate({"action": "edit", "feedback": request.text.strip()})
        result = graph.invoke(Command(resume=internal.model_dump()), config=config)
    except GraphInterrupt as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph raised an unhandled interrupt: {exc}",
        ) from exc

    return _snapshot_response(session_id=request.session_id, invoke_result=result)


# --------------------------------------------------------------------------- #
# GET /state/{session_id}
# --------------------------------------------------------------------------- #

@router.get(
    "/state/{session_id}",
    response_model=OrchestratorStateResponse,
    summary="Inspect orchestrator session state",
    description="Debug-only snapshot of the latest checkpointed state for a session.",
)
async def orchestrator_state(
    session_id: str,
) -> OrchestratorStateResponse:
    graph = _get_graph()
    snapshot = graph.get_state(_thread_config(session_id))
    if snapshot is None or not snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    state_values = snapshot.values
    # Pending gate is exposed via snapshot.tasks[].interrupts; when there are
    # no tasks left the run is done.
    pending = _pending_gate_from_snapshot(snapshot)

    return OrchestratorStateResponse(
        success=True,
        session_id=session_id,
        flow=state_values.get("flow"),
        pending_gate=pending,
        generated_files=_files_from_state(state_values),
        last_narration=state_values.get("last_narration", ""),
        done=pending is None,
    )
