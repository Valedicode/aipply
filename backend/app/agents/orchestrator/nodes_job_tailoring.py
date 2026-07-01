"""
Job-tailoring branch nodes for the orchestrator graph.

Each step node is a deterministic wrapper around an existing ``@tool`` function
in ``app.agents.writer_agent`` or ``app.agents.scoring_agent``. The giant
prompt-driven sequencing that lived inside ``writer_agent.agent`` is now
expressed as the edges of the graph instead.

Gate nodes emit a ``GatePayload`` via ``langgraph.types.interrupt`` and route on
the user's ``GateResolution`` reply:

    [step]  generic step node:  call a tool, store output in state.
    [gate]  approval / choice:  interrupt(), then Command(goto=..., update=...).

The node names below match the labels in the architecture mermaid diagram.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.graph import END
from langgraph.types import Command, interrupt

from app.agents.orchestrator.gates import GatePayload, GateResolution
from app.agents.orchestrator.state import OrchestratorState
from app.agents.writer_agent import (
    decide_tailoring_strategy,
    generate_cover_letter_content,
    generate_cover_letter_docx,
    generate_cover_letter_pdf,
    generate_cv_docx,
    generate_cv_pdf,
    generate_job_summary,
    generate_tailored_cv_html,
    rewrite_enhance_content,
    select_prioritize_content,
)
from app.agents.scoring_agent import calculate_compatibility_score_v2


# --------------------------------------------------------------------------- #
# Node-name constants
# Keeping these as module-level constants so graph.py and the API layer can
# refer to them without duplicating string literals.
# --------------------------------------------------------------------------- #

JT_ENTRY = "jt_entry"
JT_STEP1_SUMMARIZE = "jt_step1_summarize_job"
JT_STEP2_COMPATIBILITY = "jt_step2_compute_compatibility"
JT_GATE_PRESENT_SCORE = "jt_gate_present_score"
JT_STEP3_STRATEGY = "jt_step3_decide_strategy"
JT_STEP4_SELECT = "jt_step4_select_prioritize"
JT_GATE_APPROVE_SELECTION = "jt_gate_approve_selection"
JT_STEP5_REWRITE = "jt_step5_rewrite_enhance"
JT_GATE_APPROVE_REWRITE = "jt_gate_approve_rewrite"
JT_STEP6_ASSEMBLE = "jt_step6_assemble_cv"
JT_GATE_EXPORT_FORMAT = "jt_gate_export_format"
JT_STEP7_GENERATE_CV_FILES = "jt_step7_generate_cv_files"
JT_GATE_COVER_LETTER = "jt_gate_cover_letter"
JT_STEP8_COVER_LETTER_CONTENT = "jt_step8_cover_letter_content"
JT_GATE_APPROVE_COVER_LETTER = "jt_gate_approve_cover_letter"
JT_STEP9_COVER_LETTER_FILES = "jt_step9_cover_letter_files"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _narrate(state_update: dict[str, Any], text: str) -> dict[str, Any]:
    """
    Attach a narration string to a state update.

    The text becomes both ``last_narration`` (the next assistant chat bubble
    returned by the API) and a new ``AIMessage`` appended to ``messages`` via
    LangGraph's ``add_messages`` reducer.
    """
    state_update["last_narration"] = text
    state_update.setdefault("messages", []).append(AIMessage(content=text))
    state_update["pending_gate"] = None
    return state_update


def _safe_json_loads(text: str, fallback: Any) -> Any:
    """Defensive JSON parse for tool outputs that may have stringified errors."""
    if not isinstance(text, str):
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def _slugify(name: str) -> str:
    """Filesystem-safe lowercase slug for output filenames."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", (name or "applicant")).strip("_").lower()
    return slug or "applicant"


def _filename_base(cv_data: dict[str, Any]) -> str:
    return _slugify(str(cv_data.get("name", "applicant")))


def _applicant_contact(cv_data: dict[str, Any]) -> str:
    email = str(cv_data.get("email", "") or "").strip()
    phone = str(cv_data.get("phone", "") or "").strip()
    if email and phone:
        return f"{email} | {phone}"
    return email or phone


def _required_skills(job_data: dict[str, Any] | None) -> list[str]:
    if not isinstance(job_data, dict):
        return []
    skills = job_data.get("required_skills") or []
    return [s for s in skills if isinstance(s, str)]


def _merge_rewrites_into_cv(
    cv_data: dict[str, Any],
    rewritten_bullets: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Apply ``rewritten`` text in place of ``original`` text wherever the
    original appears as a bullet/description inside experience or projects.

    Substring matching is exact-string only, mirroring how
    ``rewrite_enhance_content`` echoes the original bullet back. If no match
    is found the original is kept untouched - we never fabricate.
    """
    if not rewritten_bullets:
        return cv_data

    replacements: dict[str, str] = {}
    for entry in rewritten_bullets:
        if not isinstance(entry, dict):
            continue
        original = entry.get("original")
        rewritten = entry.get("rewritten")
        if isinstance(original, str) and isinstance(rewritten, str) and original.strip():
            replacements[original.strip()] = rewritten

    if not replacements:
        return cv_data

    def replace_text(value: str) -> str:
        return replacements.get(value.strip(), value)

    def visit_section(section: Any) -> Any:
        if not isinstance(section, list):
            return section
        new_section = []
        for item in section:
            if isinstance(item, str):
                new_section.append(replace_text(item))
            elif isinstance(item, dict):
                new_item = dict(item)
                for bullet_field in ("responsibilities", "outcomes", "achievements"):
                    val = new_item.get(bullet_field)
                    if isinstance(val, list):
                        new_item[bullet_field] = [
                            replace_text(b) if isinstance(b, str) else b for b in val
                        ]
                for text_field in ("description", "summary"):
                    val = new_item.get(text_field)
                    if isinstance(val, str):
                        new_item[text_field] = replace_text(val)
                new_section.append(new_item)
            else:
                new_section.append(item)
        return new_section

    merged = dict(cv_data)
    for key in ("experience", "projects", "leadership_activities"):
        if key in merged:
            merged[key] = visit_section(merged[key])
    return merged


def _build_tailoring_plan_from_artifacts(
    compatibility_report: dict[str, Any] | None,
    selected_content: dict[str, Any] | None,
    rewritten_content: dict[str, Any] | None,
    job_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Synthesise a minimal CVTailoringPlan from artifacts already in state.

    ``generate_tailored_cv_html`` was designed for the old flow where a single
    LLM call produced this plan; here we already have richer per-step outputs,
    so we just project them into the legacy schema instead of doing another
    LLM round-trip.
    """
    matching_skills: list[str] = []
    if compatibility_report:
        gap = compatibility_report.get("gap_analysis", {}) or {}
        for sm in gap.get("matched_skills", []) or []:
            name = sm.get("matched_with") or sm.get("required_skill")
            if isinstance(name, str):
                matching_skills.append(name)

    keywords: list[str] = []
    if rewritten_content:
        for kw in rewritten_content.get("keywords_inserted", []) or []:
            if isinstance(kw, str):
                keywords.append(kw)
    if not keywords:
        keywords = _required_skills(job_data)

    section_order: list[str] = []
    sections_to_emphasize: list[str] = []
    if selected_content:
        section_order = list(selected_content.get("section_order", []) or [])
        sections_to_emphasize = list(selected_content.get("sections_to_emphasize", []) or [])

    matching_experiences: list[str] = []
    relevant_projects: list[str] = []
    if selected_content:
        for sb in selected_content.get("selected_bullets", []) or []:
            if not isinstance(sb, dict):
                continue
            section = (sb.get("section") or "").lower()
            text = sb.get("original_text")
            if not isinstance(text, str):
                continue
            if "project" in section:
                relevant_projects.append(text)
            else:
                matching_experiences.append(text)

    reasoning_parts = []
    if compatibility_report:
        score = compatibility_report.get("aggregate_score")
        level = compatibility_report.get("level")
        if score is not None and level:
            reasoning_parts.append(f"Compatibility {level} ({score:.2f}).")
    reasoning_parts.append("Plan synthesised from v2 compatibility report and selected/rewritten content.")

    return {
        "matching_experiences": matching_experiences,
        "matching_skills": matching_skills,
        "relevant_projects": relevant_projects,
        "keywords_to_incorporate": keywords,
        "reordering_suggestions": (
            "Reorder sections as: " + ", ".join(section_order) if section_order else ""
        ),
        "emphasis_points": sections_to_emphasize,
        "reasoning": " ".join(reasoning_parts).strip(),
    }


def _file_record(filename: str, file_type: str) -> dict[str, str]:
    return {
        "filename": filename,
        "file_type": file_type,
        "download_url": f"/api/files/{filename}",
    }


def _extract_filename(tool_message: str) -> str | None:
    """Pull a filename out of a generate_* tool success message."""
    match = re.search(r"The file '([^']+)' is ready for download", tool_message or "")
    return match.group(1) if match else None


# --------------------------------------------------------------------------- #
# Entry node
# --------------------------------------------------------------------------- #

def jt_entry(state: OrchestratorState) -> dict[str, Any]:
    """
    Validate inputs and produce the opening narration.

    We do NOT call the LLM here - the goal is to confirm the CV/job pair is
    present and well-formed before we burn tokens on step 1.
    """
    cv_data = state.get("cv_data") or {}
    job_data = state.get("job_data") or {}
    name = cv_data.get("name", "you")
    job_title = job_data.get("job_title") or "the target role"

    narration = (
        f"Starting the job-tailoring flow for {name} against {job_title}. "
        "I'll summarise the posting, score the match, propose a tailoring "
        "strategy, then walk you through bullet selection and rewriting "
        "with explicit approvals before any documents are generated."
    )
    return _narrate({}, narration)


# --------------------------------------------------------------------------- #
# Step 1: summarise job posting
# --------------------------------------------------------------------------- #

def jt_step1_summarize_job(state: OrchestratorState) -> dict[str, Any]:
    job_data = state.get("job_data") or {}
    job_json = json.dumps(job_data)
    summary_json = generate_job_summary.invoke({"job_json": job_json})
    summary = _safe_json_loads(summary_json, {
        "role": job_data.get("job_title", "Unknown"),
        "responsibilities": job_data.get("responsibilities", []),
        "required_skills": _required_skills(job_data),
        "preferred_skills": job_data.get("preferred_skills", []),
        "key_notes": [],
    })

    narration_lines = [
        "Job summary",
        "",
        f"Role: {summary.get('role', '')}",
    ]
    resp = summary.get("responsibilities") or []
    if resp:
        narration_lines.append("Responsibilities:")
        narration_lines.extend(resp[:6])
    req = summary.get("required_skills") or []
    if req:
        narration_lines.append("Required skills: " + ", ".join(req[:12]))
    pref = summary.get("preferred_skills") or []
    if pref:
        narration_lines.append("Preferred skills: " + ", ".join(pref[:8]))
    notes = summary.get("key_notes") or []
    if notes:
        narration_lines.append("Notes: " + " | ".join(notes[:4]))

    return _narrate({"job_summary": summary}, "\n".join(narration_lines))


# --------------------------------------------------------------------------- #
# Step 2: compute compatibility score (v2)
# --------------------------------------------------------------------------- #

def jt_step2_compute_compatibility(state: OrchestratorState) -> dict[str, Any]:
    cv_json = json.dumps(state.get("cv_data") or {})
    job_json = json.dumps(state.get("job_data") or {})
    report_json = calculate_compatibility_score_v2.invoke({
        "cv_json": cv_json,
        "job_json": job_json,
    })
    report = _safe_json_loads(report_json, {
        "aggregate_score": 0.0,
        "level": "unknown",
        "interpretation": "Compatibility scoring failed.",
        "dimensions": [],
        "gap_analysis": {"matched_skills": [], "transferable_skills": [], "missing_skills": [], "over_qualified_signals": []},
        "warnings": ["scoring v2 returned non-JSON output"],
    })

    score = report.get("aggregate_score", 0.0)
    level = (report.get("level") or "unknown").upper()
    lines = [
        "Compatibility analysis",
        "",
        f"Compatibility Score: {score:.2f} ({level})",
        "",
        "Dimension Breakdown:",
    ]
    for dim in report.get("dimensions", []) or []:
        name = dim.get("name", "?")
        ds = dim.get("score", 0.0)
        dw = dim.get("weight", 0.0)
        lines.append(f"{name} ({int(round(dw * 100))}%): {ds:.2f}")
    gap = report.get("gap_analysis", {}) or {}
    matched = gap.get("matched_skills", []) or []
    transferable = gap.get("transferable_skills", []) or []
    missing = gap.get("missing_skills", []) or []
    lines.append("")
    lines.append(f"Matched: {len(matched)} | Transferable: {len(transferable)} | Missing: {len(missing)}")
    if report.get("interpretation"):
        lines.append("")
        lines.append(report["interpretation"])

    return _narrate({"compatibility_report": report}, "\n".join(lines))


# --------------------------------------------------------------------------- #
# Gate: present score (soft gate - user just acknowledges before strategy)
# --------------------------------------------------------------------------- #

def jt_gate_present_score(state: OrchestratorState) -> Command:
    report = state.get("compatibility_report") or {}
    payload = GatePayload(
        step="present_score",
        kind="approval",
        narration="Proceed to design the tailoring strategy?",
        preview={
            "aggregate_score": report.get("aggregate_score"),
            "level": report.get("level"),
            "dimensions": report.get("dimensions", []),
            "gap_analysis": report.get("gap_analysis", {}),
            "interpretation": report.get("interpretation", ""),
        },
        allowed_actions=["approve", "reject"],
    ).model_dump()

    raw = interrupt(payload)
    resolution = GateResolution.model_validate(raw)

    if resolution.action == "approve":
        return Command(
            update={"pending_gate": None},
            goto=JT_STEP3_STRATEGY,
        )
    return Command(
        update=_narrate({}, "Stopped at the compatibility-score review. No documents were generated."),
        goto=END,
    )


# --------------------------------------------------------------------------- #
# Step 3: decide tailoring strategy
# --------------------------------------------------------------------------- #

def jt_step3_decide_strategy(state: OrchestratorState) -> dict[str, Any]:
    compatibility_json = json.dumps(state.get("compatibility_report") or {})
    cv_json = json.dumps(state.get("cv_data") or {})
    job_json = json.dumps(state.get("job_data") or {})
    strategy_json = decide_tailoring_strategy.invoke({
        "compatibility_score_json": compatibility_json,
        "cv_json": cv_json,
        "job_json": job_json,
    })
    strategy = _safe_json_loads(strategy_json, {
        "strategy": "standard",
        "intensity": "moderate",
        "focus_areas": [],
        "directives": [],
    })

    focus = ", ".join(strategy.get("focus_areas", []) or []) or "none"
    lines = [
        "Tailoring strategy",
        "",
        f"Strategy: {strategy.get('strategy', '')}",
        f"Intensity: {strategy.get('intensity', 'moderate')}",
        f"Focus areas: {focus}",
        f"Directives: {len(strategy.get('directives', []) or [])}",
    ]
    return _narrate({"tailoring_strategy": strategy}, "\n".join(lines))


# --------------------------------------------------------------------------- #
# Step 4: select & prioritise content
# --------------------------------------------------------------------------- #

def jt_step4_select_prioritize(state: OrchestratorState) -> dict[str, Any]:
    cv_json = json.dumps(state.get("cv_data") or {})
    job_json = json.dumps(state.get("job_data") or {})
    strategy_json = json.dumps(state.get("tailoring_strategy") or {})

    selected_json = select_prioritize_content.invoke({
        "cv_json": cv_json,
        "job_json": job_json,
        "tailoring_strategy_json": strategy_json,
    })
    selected = _safe_json_loads(selected_json, {
        "selected_bullets": [],
        "section_order": [],
        "sections_to_emphasize": [],
        "items_to_de_emphasize": [],
    })

    bullets = selected.get("selected_bullets", []) or []
    order = selected.get("section_order", []) or []
    lines = [
        "Selected content",
        "",
        f"Top bullets: {len(bullets)}",
        f"Recommended section order: {', '.join(order) if order else '(unchanged)'}",
        f"Emphasised sections: {', '.join(selected.get('sections_to_emphasize', []) or []) or '(none)'}",
    ]
    return _narrate({"selected_content": selected}, "\n".join(lines))


# --------------------------------------------------------------------------- #
# Gate: approve selection (HARD GATE - edit loops back to step 4)
# --------------------------------------------------------------------------- #

def jt_gate_approve_selection(state: OrchestratorState) -> Command:
    selected = state.get("selected_content") or {}
    payload = GatePayload(
        step="approve_selection",
        kind="approval",
        narration=(
            "Review the selected bullets and proposed section ordering. "
            "Approve to continue to rewriting, or edit with feedback to "
            "re-run selection."
        ),
        preview=selected,
        allowed_actions=["approve", "edit", "reject"],
    ).model_dump()

    raw = interrupt(payload)
    resolution = GateResolution.model_validate(raw)

    if resolution.action == "approve":
        return Command(
            update={"pending_gate": None},
            goto=JT_STEP5_REWRITE,
        )
    if resolution.action == "edit":
        # Merge feedback into strategy so the next pass of step 4 sees it.
        strategy = dict(state.get("tailoring_strategy") or {})
        feedback_history = list(strategy.get("user_feedback", []) or [])
        feedback_history.append({"stage": "approve_selection", "text": resolution.feedback or ""})
        strategy["user_feedback"] = feedback_history
        return Command(
            update=_narrate(
                {"tailoring_strategy": strategy, "selected_content": None},
                f"Got it - re-running selection with your feedback: {resolution.feedback}",
            ),
            goto=JT_STEP4_SELECT,
        )
    return Command(
        update=_narrate({}, "Stopped before rewriting. No documents were generated."),
        goto=END,
    )


# --------------------------------------------------------------------------- #
# Step 5: rewrite & enhance content
# --------------------------------------------------------------------------- #

def jt_step5_rewrite_enhance(state: OrchestratorState) -> dict[str, Any]:
    cv_json = json.dumps(state.get("cv_data") or {})
    job_json = json.dumps(state.get("job_data") or {})
    selected_json = json.dumps(state.get("selected_content") or {})
    strategy_json = json.dumps(state.get("tailoring_strategy") or {})

    rewritten_json = rewrite_enhance_content.invoke({
        "cv_json": cv_json,
        "job_json": job_json,
        "selected_content_json": selected_json,
        "tailoring_strategy_json": strategy_json,
    })
    rewritten = _safe_json_loads(rewritten_json, {
        "rewritten_bullets": [],
        "updated_summary": "",
        "keywords_inserted": [],
    })

    bullets = rewritten.get("rewritten_bullets", []) or []
    avg_conf = (
        sum(float(b.get("confidence", 0.0)) for b in bullets) / max(1, len(bullets))
        if bullets else 0.0
    )
    lines = [
        "Rewritten content",
        "",
        f"Bullets rewritten: {len(bullets)}",
        f"Average rewrite confidence: {avg_conf:.2f}",
        f"Keywords woven in: {', '.join(rewritten.get('keywords_inserted', []) or []) or '(none)'}",
    ]
    return _narrate({"rewritten_content": rewritten}, "\n".join(lines))


# --------------------------------------------------------------------------- #
# Gate: approve rewrite (HARD GATE - edit loops back to step 5)
# --------------------------------------------------------------------------- #

def jt_gate_approve_rewrite(state: OrchestratorState) -> Command:
    rewritten = state.get("rewritten_content") or {}
    payload = GatePayload(
        step="approve_rewrite",
        kind="approval",
        narration=(
            "Review each rewritten bullet against its original. Approve to "
            "assemble the tailored CV, edit with notes to re-run the rewrite, "
            "or reject to stop."
        ),
        preview=rewritten,
        allowed_actions=["approve", "edit", "reject"],
    ).model_dump()

    raw = interrupt(payload)
    resolution = GateResolution.model_validate(raw)

    if resolution.action == "approve":
        return Command(
            update={"pending_gate": None},
            goto=JT_STEP6_ASSEMBLE,
        )
    if resolution.action == "edit":
        strategy = dict(state.get("tailoring_strategy") or {})
        feedback_history = list(strategy.get("user_feedback", []) or [])
        feedback_history.append({"stage": "approve_rewrite", "text": resolution.feedback or ""})
        strategy["user_feedback"] = feedback_history
        return Command(
            update=_narrate(
                {"tailoring_strategy": strategy, "rewritten_content": None},
                f"Re-running rewrite with your feedback: {resolution.feedback}",
            ),
            goto=JT_STEP5_REWRITE,
        )
    return Command(
        update=_narrate({}, "Stopped before document assembly. No documents were generated."),
        goto=END,
    )


# --------------------------------------------------------------------------- #
# Step 6: assemble CV (merge rewrites + generate_tailored_cv_html)
# --------------------------------------------------------------------------- #

def jt_step6_assemble_cv(state: OrchestratorState) -> dict[str, Any]:
    cv_data = state.get("cv_data") or {}
    rewritten = state.get("rewritten_content") or {}
    merged_cv = _merge_rewrites_into_cv(cv_data, rewritten.get("rewritten_bullets", []) or [])
    tailoring_plan = _build_tailoring_plan_from_artifacts(
        state.get("compatibility_report"),
        state.get("selected_content"),
        rewritten,
        state.get("job_data"),
    )

    html_content = generate_tailored_cv_html.invoke({
        "cv_json": json.dumps(merged_cv),
        "tailoring_plan_json": json.dumps(tailoring_plan),
    })

    narration = (
        "Assembled the tailored CV. Ready to export - which format would you like?"
    )
    return _narrate(
        {
            "cv_data": merged_cv,
            "tailored_cv_html": html_content if isinstance(html_content, str) else "",
        },
        narration,
    )


# --------------------------------------------------------------------------- #
# Gate: choose export format (PDF / DOCX / both)
# --------------------------------------------------------------------------- #

EXPORT_CHOICES = ["pdf", "docx", "both"]


def jt_gate_export_format(state: OrchestratorState) -> Command:
    payload = GatePayload(
        step="export_format",
        kind="choice",
        narration="Which CV format(s) should I generate?",
        preview={},
        allowed_actions=["choose", "reject"],
        choices=EXPORT_CHOICES,
    ).model_dump()

    raw = interrupt(payload)
    resolution = GateResolution.model_validate(raw)

    if resolution.action == "reject":
        return Command(
            update=_narrate({"cv_export_choice": None}, "Skipped CV file generation."),
            goto=JT_GATE_COVER_LETTER,
        )
    choice = (resolution.choice or "").lower()
    if choice not in EXPORT_CHOICES:
        choice = "pdf"
    return Command(
        update={"pending_gate": None, "cv_export_choice": choice},
        goto=JT_STEP7_GENERATE_CV_FILES,
    )


# --------------------------------------------------------------------------- #
# Step 7: generate CV files (PDF and/or DOCX)
# --------------------------------------------------------------------------- #

def jt_step7_generate_cv_files(state: OrchestratorState) -> dict[str, Any]:
    """Emit PDF and/or DOCX of the tailored CV based on the upstream choice."""
    cv_data = state.get("cv_data") or {}
    html_content = state.get("tailored_cv_html") or ""
    applicant_name = cv_data.get("name", "Applicant")
    base = _filename_base(cv_data)
    choice = state.get("cv_export_choice") or "both"

    generated: list[dict[str, str]] = list(state.get("generated_files") or [])
    messages: list[str] = []

    if choice in ("pdf", "both") and html_content:
        pdf_name = f"{base}_cv_tailored.pdf"
        pdf_msg = generate_cv_pdf.invoke({
            "html_content": html_content,
            "output_filename": pdf_name,
            "applicant_name": applicant_name,
        })
        if isinstance(pdf_msg, str) and "Error" not in pdf_msg:
            filename = _extract_filename(pdf_msg) or pdf_name
            generated.append(_file_record(filename, "cv"))
            messages.append(f"PDF: {filename}")
        else:
            messages.append(f"PDF generation failed: {pdf_msg}")

    if choice in ("docx", "both"):
        docx_name = f"{base}_cv_tailored.docx"
        docx_msg = generate_cv_docx.invoke({
            "cv_json": json.dumps(cv_data),
            "output_filename": docx_name,
            "applicant_name": applicant_name,
        })
        if isinstance(docx_msg, str) and "Error" not in docx_msg:
            filename = _extract_filename(docx_msg) or docx_name
            generated.append(_file_record(filename, "docx"))
            messages.append(f"Word: {filename}")
        else:
            messages.append(f"Word generation failed: {docx_msg}")

    narration = "Generated CV files:\n" + "\n".join(messages) if messages else "No CV files were generated."
    return _narrate({"generated_files": generated}, narration)


# --------------------------------------------------------------------------- #
# Gate: cover letter language choice (en / de / skip)
# --------------------------------------------------------------------------- #

COVER_LETTER_CHOICES = ["english", "german", "skip"]


def jt_gate_cover_letter(state: OrchestratorState) -> Command:
    payload = GatePayload(
        step="cover_letter_language",
        kind="choice",
        narration=(
            "Would you like a matching cover letter? Pick a language or skip."
        ),
        preview={},
        allowed_actions=["choose"],
        choices=COVER_LETTER_CHOICES,
    ).model_dump()

    raw = interrupt(payload)
    resolution = GateResolution.model_validate(raw)
    choice = (resolution.choice or "skip").lower()
    if choice not in COVER_LETTER_CHOICES:
        choice = "skip"

    if choice == "skip":
        return Command(
            update=_narrate({"cover_letter_language": None}, "All done. Skipping the cover letter."),
            goto=END,
        )
    return Command(
        update={
            "pending_gate": None,
            "cover_letter_language": choice,  # type: ignore[typeddict-item]
        },
        goto=JT_STEP8_COVER_LETTER_CONTENT,
    )


# --------------------------------------------------------------------------- #
# Step 8: cover letter content
# --------------------------------------------------------------------------- #

def jt_step8_cover_letter_content(state: OrchestratorState) -> dict[str, Any]:
    cv_json = json.dumps(state.get("cv_data") or {})
    job_json = json.dumps(state.get("job_data") or {})
    company_json = json.dumps(state.get("company_data") or {}) if state.get("company_data") else ""
    language = state.get("cover_letter_language") or "english"

    content_json = generate_cover_letter_content.invoke({
        "cv_json": cv_json,
        "job_json": job_json,
        "company_json": company_json,
        "language": language,
    })
    content = _safe_json_loads(content_json, {})

    narration_lines = [
        f"Cover letter drafted ({language}). Review the paragraphs and approve to export."
    ]
    if content.get("betreff"):
        narration_lines.append(f"Betreff: {content['betreff']}")

    return _narrate({"cover_letter_content": content}, "\n".join(narration_lines))


# --------------------------------------------------------------------------- #
# Gate: approve cover letter
# --------------------------------------------------------------------------- #

def jt_gate_approve_cover_letter(state: OrchestratorState) -> Command:
    payload = GatePayload(
        step="approve_cover_letter",
        kind="approval",
        narration="Approve to export the cover letter, or edit to regenerate.",
        preview=state.get("cover_letter_content") or {},
        allowed_actions=["approve", "edit", "reject"],
    ).model_dump()

    raw = interrupt(payload)
    resolution = GateResolution.model_validate(raw)

    if resolution.action == "approve":
        return Command(
            update={"pending_gate": None},
            goto=JT_STEP9_COVER_LETTER_FILES,
        )
    if resolution.action == "edit":
        company = state.get("company_data") or {}
        company["user_feedback"] = (company.get("user_feedback") or []) + [resolution.feedback or ""]
        return Command(
            update=_narrate(
                {"company_data": company, "cover_letter_content": None},
                f"Regenerating the cover letter with your feedback: {resolution.feedback}",
            ),
            goto=JT_STEP8_COVER_LETTER_CONTENT,
        )
    return Command(
        update=_narrate({}, "Stopped before cover-letter export. CV files (if generated) are still available."),
        goto=END,
    )


# --------------------------------------------------------------------------- #
# Step 9: cover letter files (PDF/DOCX based on prior export choice)
# --------------------------------------------------------------------------- #

def jt_step9_cover_letter_files(state: OrchestratorState) -> dict[str, Any]:
    cv_data = state.get("cv_data") or {}
    content = state.get("cover_letter_content") or {}
    language = state.get("cover_letter_language") or "english"
    base = _filename_base(cv_data)
    applicant_name = cv_data.get("name", "Applicant")
    applicant_contact = _applicant_contact(cv_data)
    # Default recipient; the v1 orchestrator does not currently extract one.
    recipient_info = "Hiring Manager"

    # Match whatever the user picked for the CV export. If the user skipped CV
    # generation we still default to 'both' here so they get something usable.
    choice = state.get("cv_export_choice") or "both"
    if choice not in ("pdf", "docx", "both"):
        choice = "both"

    suffix = "anschreiben" if language == "german" else "cover_letter"
    generated: list[dict[str, str]] = list(state.get("generated_files") or [])
    messages: list[str] = []

    if choice in ("pdf", "both"):
        pdf_name = f"{base}_{suffix}.pdf"
        pdf_msg = generate_cover_letter_pdf.invoke({
            "content_json": json.dumps(content),
            "output_filename": pdf_name,
            "applicant_name": applicant_name,
            "applicant_contact": applicant_contact,
            "recipient_info": recipient_info,
        })
        if isinstance(pdf_msg, str) and "Error" not in pdf_msg:
            filename = _extract_filename(pdf_msg) or pdf_name
            generated.append(_file_record(filename, "cover_letter"))
            messages.append(f"PDF: {filename}")
        else:
            messages.append(f"Cover-letter PDF failed: {pdf_msg}")

    if choice in ("docx", "both"):
        docx_name = f"{base}_{suffix}.docx"
        docx_msg = generate_cover_letter_docx.invoke({
            "content_json": json.dumps(content),
            "output_filename": docx_name,
            "applicant_name": applicant_name,
            "applicant_contact": applicant_contact,
            "recipient_info": recipient_info,
        })
        if isinstance(docx_msg, str) and "Error" not in docx_msg:
            filename = _extract_filename(docx_msg) or docx_name
            generated.append(_file_record(filename, "docx"))
            messages.append(f"Word: {filename}")
        else:
            messages.append(f"Cover-letter Word failed: {docx_msg}")

    narration = (
        "Cover letter exported:\n" + "\n".join(messages)
        if messages else "No cover-letter files were generated."
    )
    return _narrate({"generated_files": generated}, narration)
