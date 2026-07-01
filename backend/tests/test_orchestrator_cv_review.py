"""
End-to-end harness for the cv_review branch of the orchestrator graph.

The LLM-backed ``_run_step_review`` is replaced with a deterministic stub that
returns canned per-step payloads, so the test runs offline. We drive the graph
through every gate and verify:

- the entry node routes to step 1 on flow='cv_review';
- each step gate exposes the expected ``step`` identifier;
- ``edit`` loops back into the same step and accumulates feedback;
- the leadership step is skipped when ``leadership_activities`` is empty;
- ``review_outputs`` contains one payload per visited step at the end.

Run with::

    cd backend
    pytest tests/test_orchestrator_cv_review.py -v
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agents.orchestrator.graph import build_graph
from app.agents.orchestrator.nodes_cv_review import (
    CR_GATE_ASSESSMENT,
    CR_GATE_EDUCATION,
    CR_GATE_EXPERIENCE,
    CR_GATE_HEADER,
    CR_GATE_LEADERSHIP,
    CR_GATE_SKILLS_PROJECTS,
)


# --------------------------------------------------------------------------- #
# Fixture CVs
# --------------------------------------------------------------------------- #

CV_WITH_LEADERSHIP = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "phone": "+1 555 0100",
    "location": "London",
    "github_url": "https://github.com/ada",
    "linkedin_url": "",
    "portfolio_url": "",
    "skills": ["Python", "Mathematics", "Algorithms"],
    "education": [
        "B.Sc. Computer Science, University of London, 2020",
        "M.Sc. Applied Math, in progress",
    ],
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
    "leadership_activities": ["Founded the Bayes Reading Group"],
    "projects": ["Difference Engine v0 - Python simulator"],
}


CV_WITHOUT_LEADERSHIP = {
    **CV_WITH_LEADERSHIP,
    "leadership_activities": [],
}


# --------------------------------------------------------------------------- #
# Deterministic LLM stub - returns a canned payload keyed on the schema class.
# --------------------------------------------------------------------------- #

CANNED_REVIEWS: dict[str, dict[str, Any]] = {
    "HeaderReview": {
        "verdict": "Acceptable",
        "critique": ["Missing LinkedIn URL"],
        "suggestions": ["Add LinkedIn"],
        "rewritten_header": "Ada Lovelace | London | ada@example.com | github.com/ada",
    },
    "EducationReview": {
        "critique": [],
        "suggestions": [],
        "improved_entries": [
            "B.Sc. Computer Science, University of London (2017-2020)",
            "M.Sc. Applied Math, University of London (in progress)",
        ],
        "future_degree_recommendation": "PhD not necessary for current target roles.",
    },
    "ExperienceReview": {
        "role_critiques": ["Add metrics to algorithm-design bullet."],
        "rewritten_bullets": [
            {
                "role_index": 0,
                "original": "Designed the first algorithm",
                "rewritten": "Designed the first general-purpose computing algorithm, foundational to modern CS.",
                "rationale": "Adds scope and impact.",
            }
        ],
        "weak_bullets_to_remove": [],
    },
    "LeadershipReview": {
        "critique": ["Reading group impact is unclear."],
        "suggestions": ["State attendance numbers."],
        "activities_to_emphasize": ["Founded the Bayes Reading Group"],
        "activities_to_remove": [],
    },
    "SkillsProjectsReview": {
        "skill_groups": [
            {"name": "Languages", "skills": ["Python"]},
            {"name": "Math", "skills": ["Mathematics", "Algorithms"]},
        ],
        "skills_to_remove": [],
        "project_ranking": ["Difference Engine v0 - Python simulator"],
        "refined_project_descriptions": [
            {
                "project": "Difference Engine v0 - Python simulator",
                "description": "End-to-end Python simulator of Babbage's difference engine; emphasises architecture over feature listing.",
            }
        ],
        "projects_to_remove": [],
    },
    "OverallAssessment": {
        "score": 8.5,
        "strengths": ["Strong CS foundation", "Clear algorithmic depth"],
        "weaknesses": ["Few quantified outcomes"],
        "top_improvements": [
            "Add metrics to experience bullets",
            "Add LinkedIn URL",
            "Quantify project impact",
        ],
        "recommended_pages": 1,
        "role_specific_tailoring": "Lean toward research / algorithmic SWE roles.",
    },
}


def _fake_run_step_review(schema_cls, system_text, section_label, payload, feedback):
    name = schema_cls.__name__
    base = dict(CANNED_REVIEWS.get(name, {}))
    if feedback:
        # Surface feedback receipt in the canned output so the test can prove
        # the edit loop actually fed it back into the next call.
        base = {**base, "_feedback_seen": list(feedback)}
    return base


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def patched_llm():
    with patch(
        "app.agents.orchestrator.nodes_cv_review._run_step_review",
        side_effect=_fake_run_step_review,
    ):
        yield


@pytest.fixture
def graph():
    return build_graph(checkpointer=InMemorySaver())


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _interrupt_step(result: dict[str, Any]) -> str | None:
    interrupts = result.get("__interrupt__") or []
    if not interrupts:
        return None
    first = interrupts[0]
    value = getattr(first, "value", None)
    if isinstance(value, dict):
        return value.get("step")
    return None


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_full_happy_path_visits_all_six_gates(patched_llm, graph):
    cfg = _config("cv-review-happy")
    state_input = {"flow": "cv_review", "cv_data": CV_WITH_LEADERSHIP, "review_outputs": {}}

    out = graph.invoke(state_input, config=cfg)
    assert _interrupt_step(out) == "cv_review_header"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_education"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_experience"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_leadership"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_skills_projects"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_assessment"

    final = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert final.get("pending_gate") is None
    assert "__interrupt__" not in final
    review = final["review_outputs"]
    for step_key in ("header", "education", "experience", "leadership", "skills_projects", "assessment"):
        assert step_key in review, f"missing step output: {step_key}"


def test_leadership_step_is_skipped_when_section_empty(patched_llm, graph):
    cfg = _config("cv-review-no-leadership")
    state_input = {"flow": "cv_review", "cv_data": CV_WITHOUT_LEADERSHIP, "review_outputs": {}}

    out = graph.invoke(state_input, config=cfg)
    assert _interrupt_step(out) == "cv_review_header"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_education"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_experience"

    # Skipping leadership: the next gate after experience should be skills_projects.
    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_skills_projects"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_assessment"

    final = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert "__interrupt__" not in final
    assert "leadership" not in final["review_outputs"]


def test_edit_at_header_reruns_step_and_passes_feedback(patched_llm, graph):
    cfg = _config("cv-review-edit-header")
    state_input = {"flow": "cv_review", "cv_data": CV_WITH_LEADERSHIP, "review_outputs": {}}

    out = graph.invoke(state_input, config=cfg)
    assert _interrupt_step(out) == "cv_review_header"

    # Edit -> back to header.
    out = graph.invoke(
        Command(resume={"action": "edit", "feedback": "Emphasise the portfolio URL more."}),
        config=cfg,
    )
    assert _interrupt_step(out) == "cv_review_header"

    # The stub records seen feedback in the review output.
    snapshot = graph.get_state(cfg)
    review = (snapshot.values.get("review_outputs") or {}).get("header") or {}
    assert review.get("_feedback_seen") == ["Emphasise the portfolio URL more."]

    # Approving now completes the header step.
    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_education"


def test_reject_at_education_terminates_without_later_steps(patched_llm, graph):
    cfg = _config("cv-review-reject")
    state_input = {"flow": "cv_review", "cv_data": CV_WITH_LEADERSHIP, "review_outputs": {}}

    out = graph.invoke(state_input, config=cfg)
    assert _interrupt_step(out) == "cv_review_header"

    out = graph.invoke(Command(resume={"action": "approve"}), config=cfg)
    assert _interrupt_step(out) == "cv_review_education"

    final = graph.invoke(Command(resume={"action": "reject"}), config=cfg)
    assert "__interrupt__" not in final
    # No experience/skills/assessment review should have been produced.
    review = final["review_outputs"]
    assert "experience" not in review
    assert "skills_projects" not in review
    assert "assessment" not in review
