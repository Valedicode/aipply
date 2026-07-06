"""Unit tests for LaTeX rendering and JSON Resume adapter."""

from __future__ import annotations

from app.services.latex_renderer import latex_escape, render_cv_tex
from app.services.resume_adapter import build_harvard_sections, to_json_resume


def test_latex_escape_special_characters():
    assert latex_escape("50%") == r"50\%"
    assert latex_escape("R&D") == r"R\&D"
    assert latex_escape("C++") == r"C++"
    assert latex_escape("foo_bar") == r"foo\_bar"


def test_legacy_resume_info_maps_to_json_resume_work():
    cv = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1 555 0100",
        "skills": ["Python", "Algorithms"],
        "education": ["B.Sc. Mathematics, Cambridge"],
        "experience": [
            {
                "position": "Engineer",
                "company": "Analytical Engines Ltd.",
                "duration": "1843 -- 1852",
                "responsibilities": ["Designed the first algorithm"],
            }
        ],
        "projects": [],
        "leadership_activities": ["Founded the Bayes Reading Group"],
    }
    doc = to_json_resume(cv)
    assert doc["basics"]["name"] == "Ada Lovelace"
    assert doc["work"][0]["name"] == "Analytical Engines Ltd."
    assert doc["work"][0]["highlights"] == ["Designed the first algorithm"]
    assert doc["volunteer"][0]["position"] == "Founded the Bayes Reading Group"


def test_render_cv_tex_includes_harvard_sections():
    cv = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1 555 0100",
        "skills": ["Python"],
        "education": ["B.Sc. Mathematics"],
        "experience": [
            {
                "position": "Engineer",
                "company": "Analytical Engines Ltd.",
                "duration": "1843 -- 1852",
                "responsibilities": ["Designed the first algorithm"],
            }
        ],
        "projects": [],
        "leadership_activities": [],
    }
    tex = render_cv_tex(cv, section_order=["experience", "education", "skills"])
    assert "Ada Lovelace" in tex
    assert "Analytical Engines Ltd." in tex
    assert r"Designed the first algorithm" in tex or "Designed the first algorithm" in tex
    assert "\\documentclass" in tex


def test_build_harvard_sections_respects_section_order():
    cv = {
        "name": "Test User",
        "email": "t@example.com",
        "phone": "123",
        "skills": ["Go"],
        "education": ["M.S. CS"],
        "experience": [
            {
                "position": "Dev",
                "company": "Co",
                "duration": "2020",
                "responsibilities": ["Built APIs"],
            }
        ],
        "projects": [],
        "leadership_activities": [],
    }
    _, sections = build_harvard_sections(cv, section_order=["skills", "experience", "education"])
    assert [s["type"] for s in sections] == ["skills", "work", "education"]
