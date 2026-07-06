"""
End-to-end harness for the job-tailoring branch of the orchestrator graph.

Every LLM-backed @tool is replaced with a deterministic stub so the test runs
offline. We drive the graph through each gate, verify the interrupt payloads
have the expected ``step`` identifiers, and confirm the final state contains
both the tailored CV files and the cover-letter files.

Run with::

    cd backend
    pytest tests/test_orchestrator_job_tailoring.py -v
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agents.orchestrator.graph import build_graph
from app.agents.orchestrator.nodes_job_tailoring import (
    JT_ENTRY,
    JT_GATE_APPROVE_COVER_LETTER,
    JT_GATE_APPROVE_REWRITE,
    JT_GATE_APPROVE_SELECTION,
    JT_GATE_COVER_LETTER,
    JT_GATE_PRESENT_SCORE,
)


# --------------------------------------------------------------------------- #
# Fixed deterministic fixture data
# --------------------------------------------------------------------------- #

CV = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "phone": "+1 555 0100",
    "skills": ["Python", "Mathematics"],
    "education": ["B.Sc. Computer Science"],
    "experience": [
        {
            "position": "Engineer",
            "company": "Analytical Engines Ltd.",
            "responsibilities": [
                "Designed the first algorithm",
                "Wrote technical notes",
            ],
        }
    ],
    "projects": [],
    "leadership_activities": [],
}

JOB = {
    "job_title": "Senior Python Engineer",
    "job_level": "Senior",
    "required_skills": ["Python", "Algorithms"],
    "preferred_skills": ["Mathematics"],
    "employment_type": "Full-time",
    "location": "Remote",
    "responsibilities": ["Build new things"],
    "qualifications": [],
    "key_requirements": ["5+ yoe"],
}

JOB_SUMMARY = {
    "role": "Senior Python Engineer",
    "responsibilities": ["Build new things"],
    "required_skills": ["Python", "Algorithms"],
    "preferred_skills": ["Mathematics"],
    "key_notes": ["Remote"],
}

COMPATIBILITY_REPORT = {
    "aggregate_score": 0.78,
    "level": "high",
    "interpretation": "Strong match.",
    "dimensions": [
        {"name": "hard_skills", "score": 0.85, "weight": 0.40, "rationale": ""},
        {"name": "experience", "score": 0.70, "weight": 0.15, "rationale": ""},
        {"name": "seniority", "score": 0.75, "weight": 0.15, "rationale": ""},
        {"name": "domain", "score": 0.65, "weight": 0.15, "rationale": ""},
        {"name": "ats_keywords", "score": 0.80, "weight": 0.15, "rationale": ""},
    ],
    "gap_analysis": {
        "matched_skills": [
            {"required_skill": "Python", "matched_with": "Python", "kind": "direct",
             "transferability": 1.0, "rationale": "", "bridge_bullet": None, "is_required": True}
        ],
        "transferable_skills": [],
        "missing_skills": [],
        "over_qualified_signals": [],
    },
    "warnings": [],
}

STRATEGY = {
    "scoring_version": "v2",
    "aggregate_score": 0.78,
    "level": "high",
    "intensity": "minor",
    "strategy": "Polish keywords and ordering.",
    "focus_areas": ["inject_ats_keywords"],
    "directives": [
        {"type": "inject_keywords", "section": "skills_and_summary", "guidance": "Add Python explicitly."}
    ],
    "summary": {"matched_skills_count": 1, "transferable_skills_count": 0,
                "missing_skills_count": 0, "over_qualified_signals_count": 0},
}

SELECTED = {
    "selected_bullets": [
        {"section": "experience", "original_text": "Designed the first algorithm",
         "relevance_score": 0.92, "reason": "matches algorithms keyword"},
    ],
    "section_order": ["experience", "skills", "education"],
    "sections_to_emphasize": ["experience"],
    "items_to_de_emphasize": [],
}

REWRITTEN = {
    "rewritten_bullets": [
        {
            "original": "Designed the first algorithm",
            "rewritten": "Designed and validated the first published algorithm in Python idioms.",
            "confidence": 0.88,
            "keywords_added": ["Python"],
        }
    ],
    "updated_summary": "",
    "keywords_inserted": ["Python", "Algorithms"],
}

COVER_LETTER_CONTENT = {
    "language": "english",
    "betreff": "",
    "grussformel": "",
    "opening_paragraph": "Hello.",
    "body_paragraph_1": "I match well.",
    "body_paragraph_2": "I match more.",
    "body_paragraph_3": "",
    "closing_paragraph": "Thank you.",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _interrupt_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Pull the first interrupt's value out of an invoke() result."""
    interrupts = result.get("__interrupt__")
    assert interrupts, f"expected an interrupt; got {result}"
    first = interrupts[0]
    return first.value if hasattr(first, "value") else first["value"]


def _fake_tool(fn):
    """Wrap a function as a SimpleNamespace with an .invoke method.

    LangChain ``StructuredTool`` instances are frozen Pydantic models, so we
    cannot patch ``.invoke`` on them directly. Replacing the entire bound
    reference inside the node module with a SimpleNamespace gives nodes the
    same ``.invoke(dict)`` interface without touching the real tools.
    """
    return SimpleNamespace(invoke=fn)


@pytest.fixture
def patched_tools():
    """Deterministic stand-ins for every LLM/PDF-backed tool referenced by
    the job-tailoring nodes."""
    stubs = {
        "generate_job_summary": _fake_tool(lambda _: json.dumps(JOB_SUMMARY)),
        "calculate_compatibility_score_v2": _fake_tool(lambda _: json.dumps(COMPATIBILITY_REPORT)),
        "decide_tailoring_strategy": _fake_tool(lambda _: json.dumps(STRATEGY)),
        "select_prioritize_content": _fake_tool(lambda _: json.dumps(SELECTED)),
        "rewrite_enhance_content": _fake_tool(lambda _: json.dumps(REWRITTEN)),
        "generate_cv_pdf": _fake_tool(
            lambda kw: f"CV PDF generated successfully! The file '{kw['output_filename']}' is ready for download."
        ),
        "generate_cover_letter_content": _fake_tool(lambda _: json.dumps(COVER_LETTER_CONTENT)),
        "generate_cover_letter_pdf": _fake_tool(
            lambda kw: f"Cover letter PDF generated successfully! The file '{kw['output_filename']}' is ready for download."
        ),
    }
    contexts = [
        patch(f"app.agents.orchestrator.nodes_job_tailoring.{name}", stub)
        for name, stub in stubs.items()
    ]
    for c in contexts:
        c.start()
    yield
    for c in contexts:
        c.stop()


@pytest.fixture
def graph():
    """Fresh in-memory graph per test."""
    return build_graph(checkpointer=InMemorySaver())


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_full_happy_path_emits_all_five_gates_and_generates_files(graph, patched_tools):
    config = {"configurable": {"thread_id": "test-happy"}}

    # 1. Initial invocation runs entry + steps 1-2, then interrupts at present_score.
    result = graph.invoke(
        {"flow": "job_tailoring", "cv_data": CV, "job_data": JOB},
        config=config,
    )
    payload = _interrupt_payload(result)
    assert payload["step"] == "present_score"
    assert payload["kind"] == "approval"
    assert "aggregate_score" in payload["preview"]

    # 2. Approve compatibility -> runs step 3 + 4, interrupts at approve_selection.
    result = graph.invoke(Command(resume={"action": "approve"}), config=config)
    payload = _interrupt_payload(result)
    assert payload["step"] == "approve_selection"
    assert payload["preview"]["selected_bullets"], "selected content should be in preview"

    # 3. Approve selection -> runs step 5, interrupts at approve_rewrite.
    result = graph.invoke(Command(resume={"action": "approve"}), config=config)
    payload = _interrupt_payload(result)
    assert payload["step"] == "approve_rewrite"
    assert payload["preview"]["rewritten_bullets"][0]["rewritten"].startswith("Designed and validated")

    # 4. Approve rewrite -> runs step 6 + 7, interrupts at cover_letter language.
    result = graph.invoke(Command(resume={"action": "approve"}), config=config)
    payload = _interrupt_payload(result)
    assert payload["step"] == "cover_letter_language"
    assert payload["kind"] == "choice"
    assert "english" in payload["choices"]

    # 5. Pick 'english' -> runs step 8 (cover-letter content), interrupts at approve_cover_letter.
    result = graph.invoke(Command(resume={"action": "choose", "choice": "english"}), config=config)
    payload = _interrupt_payload(result)
    assert payload["step"] == "approve_cover_letter"
    assert payload["preview"]["opening_paragraph"] == "Hello."

    # 6. Approve cover letter -> step 9, then END.
    result = graph.invoke(Command(resume={"action": "approve"}), config=config)
    assert "__interrupt__" not in result, "graph should terminate after step 9"

    state = graph.get_state(config).values
    files = state["generated_files"]
    types = sorted(f["file_type"] for f in files)
    names = [f["filename"] for f in files]
    assert "cv" in types and "cover_letter" in types
    assert any(n.endswith("_cv_tailored.pdf") for n in names)
    assert any(n.endswith("_cover_letter.pdf") for n in names)

    # The first rewritten bullet should have been merged into experience.
    merged_bullet = state["cv_data"]["experience"][0]["responsibilities"][0]
    assert merged_bullet.startswith("Designed and validated")


def test_edit_at_approve_selection_reruns_step_4(graph, patched_tools):
    """An 'edit' action on approve_selection should loop back to step 4."""
    config = {"configurable": {"thread_id": "test-edit-selection"}}

    graph.invoke({"flow": "job_tailoring", "cv_data": CV, "job_data": JOB}, config=config)
    graph.invoke(Command(resume={"action": "approve"}), config=config)  # past present_score

    # Now we're paused at approve_selection. Edit it.
    result = graph.invoke(
        Command(resume={"action": "edit", "feedback": "Use more action verbs."}),
        config=config,
    )
    payload = _interrupt_payload(result)
    # After edit, step 4 reruns and we land on approve_selection again.
    assert payload["step"] == "approve_selection"

    # The feedback should have been recorded in the strategy.
    state = graph.get_state(config).values
    feedback = state["tailoring_strategy"]["user_feedback"]
    assert feedback[-1]["stage"] == "approve_selection"
    assert "action verbs" in feedback[-1]["text"]


def test_reject_at_present_score_terminates_without_files(graph, patched_tools):
    """A 'reject' on the first soft gate should end the graph immediately."""
    config = {"configurable": {"thread_id": "test-reject-score"}}

    graph.invoke({"flow": "job_tailoring", "cv_data": CV, "job_data": JOB}, config=config)
    result = graph.invoke(Command(resume={"action": "reject"}), config=config)

    assert "__interrupt__" not in result
    state = graph.get_state(config).values
    assert state.get("generated_files") in (None, [])
    assert "Stopped" in state["last_narration"]


def test_skip_cover_letter_after_cv_generation(graph, patched_tools):
    """Picking 'skip' at the cover-letter gate should end after CV files only."""
    config = {"configurable": {"thread_id": "test-skip-cover"}}

    graph.invoke({"flow": "job_tailoring", "cv_data": CV, "job_data": JOB}, config=config)
    graph.invoke(Command(resume={"action": "approve"}), config=config)  # present_score
    graph.invoke(Command(resume={"action": "approve"}), config=config)  # approve_selection
    graph.invoke(Command(resume={"action": "approve"}), config=config)  # approve_rewrite
    result = graph.invoke(Command(resume={"action": "choose", "choice": "skip"}), config=config)

    assert "__interrupt__" not in result
    state = graph.get_state(config).values
    files = state["generated_files"]
    types = {f["file_type"] for f in files}
    assert "cover_letter" not in types
    # Only the CV PDF was requested.
    assert any(f["filename"].endswith("_cv_tailored.pdf") for f in files)


def test_discovery_flow_routes_to_stub(graph, patched_tools):
    config = {"configurable": {"thread_id": "test-discovery"}}
    result = graph.invoke({"flow": "discovery", "cv_data": CV}, config=config)
    assert "not yet available" in result["last_narration"]


# NOTE: the previous test asserted cv_review routed to a stub. The cv_review
# branch is now a full 6-step graph; coverage moved to
# tests/test_orchestrator_cv_review.py.
