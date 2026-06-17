"""
Tests for scoring_agent.py — the standalone compatibility-scoring module.

These tests verify that the extracted module works independently of the Writer
agent's chat workflow.  LLM and embedding calls are mocked so the suite runs
without network access or API keys.

Run with:
    cd backend
    pytest tests/test_compatibility_v2.py -v
"""

import json
from unittest.mock import MagicMock, patch
from typing import List

import pytest

from app.agents.scoring_agent import (
    # Public @tool functions
    calculate_semantic_similarity,
    calculate_bm25_score,
    calculate_compatibility_score_v2,
    calculate_compatibility_score,
    match_skill_pairs,
    assess_transferability_llm,
    build_gap_analysis,
    # Internal function used by decide_tailoring_strategy fallback
    _calculate_compatibility_score_v2_internal,
    # Constants
    MATCHED_THRESHOLD,
    TRANSFERABLE_THRESHOLD,
)
from app.models.schemas import (
    CompatibilityReport,
    GapAnalysis,
    SkillMatch,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_CV = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "000-000-0000",
    "skills": ["python", "fastapi", "react"],
    "education": ["BSc Computer Science"],
    "experience": [
        {
            "position": "Senior Software Engineer",
            "company": "Acme Corp",
            "duration": "2020-2024",
            "responsibilities": ["Built REST APIs with FastAPI and Python"],
        }
    ],
    "projects": [],
}

MINIMAL_JOB = {
    "job_title": "Software Engineer",
    "job_level": "senior",
    "required_skills": ["python", "fastapi"],
    "preferred_skills": ["react"],
    "years_experience": 3,
    "employment_type": "Full-time",
    "location": "Remote",
    "responsibilities": ["Build backend services"],
    "qualifications": [],
    "key_requirements": ["python"],
}

FAMILY_JOB = {
    **MINIMAL_JOB,
    "required_skills": ["vue"],  # candidate has react — same family
    "preferred_skills": [],
}


def _fake_embedding(text: str) -> List[float]:
    """Return a deterministic unit vector for testing."""
    return [1.0] + [0.0] * 1535


# ---------------------------------------------------------------------------
# Test 1: calculate_compatibility_score_v2 returns a valid CompatibilityReport
# ---------------------------------------------------------------------------

def test_calculate_compatibility_score_v2_returns_report():
    """Call the tool with mocked embeddings; result must be a valid CompatibilityReport."""
    with patch("app.agents.scoring_agent.get_embeddings", return_value=[[1.0] + [0.0] * 1535]):
        raw = calculate_compatibility_score_v2.invoke({
            "cv_json": json.dumps(MINIMAL_CV),
            "job_json": json.dumps(MINIMAL_JOB),
        })

    report = CompatibilityReport.model_validate_json(raw)
    assert 0.0 <= report.aggregate_score <= 1.0
    assert report.level in ("low", "medium", "high", "excellent", "unknown")
    assert len(report.dimensions) == 5
    dim_names = {d.name for d in report.dimensions}
    assert dim_names == {"hard_skills", "experience", "seniority", "domain", "ats_keywords"}


# ---------------------------------------------------------------------------
# Test 2: match_skill_pairs — direct match
# ---------------------------------------------------------------------------

def test_match_skill_pairs_direct_match():
    """When the CV lists the required skill exactly, expect kind='direct' with transferability=1.0."""
    raw = match_skill_pairs.invoke({
        "cv_json": json.dumps(MINIMAL_CV),
        "job_json": json.dumps(MINIMAL_JOB),
    })

    matches = json.loads(raw)
    # python is in both CV skills and required_skills
    python_match = next((m for m in matches if m["required_skill"] == "python"), None)
    assert python_match is not None
    assert python_match["kind"] == "direct"
    assert python_match["transferability"] == 1.0


# ---------------------------------------------------------------------------
# Test 3: match_skill_pairs — family match (react -> vue, same skill-graph family)
# ---------------------------------------------------------------------------

def test_match_skill_pairs_family_match():
    """When the CV has 'react' and the job requires 'vue', expect kind='family'."""
    with patch("app.agents.scoring_agent.get_embeddings", return_value=[[1.0] + [0.0] * 1535]):
        raw = match_skill_pairs.invoke({
            "cv_json": json.dumps(MINIMAL_CV),
            "job_json": json.dumps(FAMILY_JOB),
        })

    matches = json.loads(raw)
    vue_match = next((m for m in matches if m["required_skill"] == "vue"), None)
    assert vue_match is not None
    assert vue_match["kind"] == "family"
    assert vue_match["transferability"] > 0.5


# ---------------------------------------------------------------------------
# Test 4: build_gap_analysis — correct bucketing of SkillMatch entries
# ---------------------------------------------------------------------------

def test_build_gap_analysis_buckets():
    """Hand-craft SkillMatch entries and verify they land in the right buckets."""
    skill_matches = [
        {
            "required_skill": "python",
            "matched_with": "python",
            "kind": "direct",
            "transferability": 1.0,
            "rationale": "direct",
            "bridge_bullet": None,
            "is_required": True,
        },
        {
            "required_skill": "vue",
            "matched_with": "react",
            "kind": "family",
            "transferability": 0.85,  # above TRANSFERABLE_THRESHOLD but below MATCHED_THRESHOLD
            "rationale": "same family",
            "bridge_bullet": None,
            "is_required": True,
        },
        {
            "required_skill": "kubernetes",
            "matched_with": None,
            "kind": "missing",
            "transferability": 0.1,  # below TRANSFERABLE_THRESHOLD
            "rationale": "no match",
            "bridge_bullet": None,
            "is_required": True,
        },
    ]

    raw = build_gap_analysis.invoke({
        "skill_matches_json": json.dumps(skill_matches),
        "cv_json": json.dumps(MINIMAL_CV),
        "job_json": json.dumps(MINIMAL_JOB),
    })

    gap = GapAnalysis.model_validate_json(raw)
    matched_skills = [m.required_skill for m in gap.matched_skills]
    transferable_skills = [m.required_skill for m in gap.transferable_skills]
    missing_skills = [m.required_skill for m in gap.missing_skills]

    assert "python" in matched_skills          # transferability=1.0 >= MATCHED_THRESHOLD
    assert "vue" in transferable_skills        # 0.55 <= 0.85 < 0.95
    assert "kubernetes" in missing_skills      # transferability=0.1 < TRANSFERABLE_THRESHOLD


# ---------------------------------------------------------------------------
# Test 5: calculate_semantic_similarity — structure check with mocked embeddings
# ---------------------------------------------------------------------------

def test_calculate_semantic_similarity_structure():
    """Mocked embeddings; result must have similarity_score in [0, 1]."""
    fake_emb = [[1.0] + [0.0] * 1535]
    with patch("app.agents.scoring_agent.get_embeddings", return_value=fake_emb):
        raw = calculate_semantic_similarity.invoke({
            "resume_text": "Python developer with FastAPI experience",
            "job_text": "Looking for a Python backend engineer",
        })

    result = json.loads(raw)
    assert "similarity_score" in result
    assert 0.0 <= result["similarity_score"] <= 1.0
    assert result.get("method") == "cosine_similarity"


# ---------------------------------------------------------------------------
# Test 6: calculate_bm25_score — structure check
# ---------------------------------------------------------------------------

def test_calculate_bm25_score_structure():
    """BM25 result must contain bm25_scores list and average_score."""
    sections = json.dumps(["Python and FastAPI experience", "React frontend work"])
    raw = calculate_bm25_score.invoke({
        "resume_sections": sections,
        "job_requirements": "senior python fastapi engineer",
    })

    result = json.loads(raw)
    assert "bm25_scores" in result
    assert isinstance(result["bm25_scores"], list)
    assert len(result["bm25_scores"]) == 2
    assert "average_score" in result
    assert 0.0 <= result["average_score"] <= 1.0


# ---------------------------------------------------------------------------
# Test 7: calculate_compatibility_score_v2 — invalid JSON returns level='unknown'
# ---------------------------------------------------------------------------

def test_compatibility_score_v2_invalid_json():
    """Garbage input must return a CompatibilityReport with level='unknown', not raise."""
    raw = calculate_compatibility_score_v2.invoke({
        "cv_json": "not valid json }{",
        "job_json": '{"job_title": "Engineer"}',
    })

    report = CompatibilityReport.model_validate_json(raw)
    assert report.level == "unknown"
    assert report.aggregate_score == 0.0
    assert len(report.warnings) > 0


# ---------------------------------------------------------------------------
# Test 8: writer_agent's tools list still contains all 8 scoring tool names
# ---------------------------------------------------------------------------

def test_writer_agent_tools_list_unchanged():
    """
    Import the agent from writer_agent and assert that all scoring tools
    are present in its tools list. This proves the refactor didn't drop
    any tool from the LangChain agent registration.
    """
    expected_scoring_tools = {
        "calculate_semantic_similarity",
        "calculate_bm25_score",
        "calculate_compatibility_score",
        "match_skill_pairs",
        "assess_transferability_llm",
        "calculate_compatibility_score_v2",
        "build_gap_analysis",
        "decide_tailoring_strategy",
    }

    # Import lazily to avoid any module-level side effects during test collection
    from app.agents.writer_agent import agent as writer_agent  # noqa: PLC0415

    # create_agent returns a LangGraph CompiledStateGraph; tools live on the
    # "tools" node's bound runnable, not on agent.tools.
    tools_node = writer_agent.nodes["tools"]
    tool_names = set(tools_node.bound._tools_by_name.keys())
    missing = expected_scoring_tools - tool_names
    assert not missing, f"Missing tools in writer_agent: {missing}"
