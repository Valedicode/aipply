"""
LaTeX rendering and PDF compilation for CV and cover letter export.

CV layout follows a Harvard-style two-column template driven by JSON Resume
taxonomy (see ``app.services.resume_adapter``).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.resume_adapter import build_harvard_sections

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "latex"

_GERMAN_MONTHS = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def latex_escape(text: str | None) -> str:
    """Escape user-provided text for safe inclusion in LaTeX."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "#": r"\#",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def latex_url(text: str | None) -> str:
    """Escape a URL for use inside ``\\href{...}{...}``."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
    )


def _jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["latex_escape"] = latex_escape
    env.filters["latex_url"] = latex_url
    return env


def render_cv_tex(
    cv_data: dict[str, Any],
    section_order: list[str] | None = None,
) -> str:
    """Render a Harvard-style CV LaTeX document from structured CV JSON."""
    header, sections = build_harvard_sections(cv_data, section_order=section_order)
    env = _jinja_env()
    template = env.get_template("cv.tex.j2")
    return template.render(**header, sections=sections)


def _format_date(language: str) -> str:
    now = datetime.now()
    if language.lower() == "german":
        return f"{now.day}. {_GERMAN_MONTHS[now.month]} {now.year}"
    return now.strftime("%B %d, %Y")


def _short_link_label(url: str, fallback: str) -> str:
    """Human-readable link text for the header column."""
    url = url.strip()
    if not url:
        return fallback
    for prefix in ("https://", "http://", "www."):
        if url.lower().startswith(prefix):
            url = url[len(prefix) :]
    return url.rstrip("/") or fallback


def _cover_letter_header_links(cv_data: dict[str, Any]) -> list[tuple[str, str]]:
    """Up to two (url, label) pairs for the header right column."""
    links: list[tuple[str, str]] = []
    seen: set[str] = set()

    def _add(url: str | None, label: str) -> None:
        if not isinstance(url, str) or not url.strip():
            return
        clean = url.strip()
        if clean in seen or len(links) >= 2:
            return
        seen.add(clean)
        links.append((clean, _short_link_label(clean, label)))

    _add(cv_data.get("linkedin_url"), "LinkedIn")
    _add(cv_data.get("github_url"), "GitHub")
    _add(cv_data.get("portfolio_url"), "Portfolio")
    return links


def extract_recipient_name(job_data: dict[str, Any] | None) -> str:
    """Return a named recipient from job posting data, or empty string."""
    if not isinstance(job_data, dict):
        return ""
    for key in ("recipient_name", "contact_name", "hiring_contact", "contact_person"):
        val = job_data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _cover_letter_salutation(recipient_info: str, *, is_german: bool) -> str:
    recipient = (recipient_info or "").strip()
    if not recipient:
        raise ValueError("recipient_info is required for the cover letter salutation")
    if is_german:
        return f"Sehr geehrte/r {recipient},"
    return f"Dear {recipient},"


def _cover_letter_context(
    cv_data: dict[str, Any] | None,
    job_data: dict[str, Any] | None,
    applicant_name: str,
    applicant_contact: str = "",
) -> dict[str, Any]:
    """Extract header fields for the entry-level cover letter template."""
    cv = cv_data or {}
    job = job_data or {}

    phone = str(cv.get("phone") or "").strip()
    email = str(cv.get("email") or "").strip()
    if not email and applicant_contact and "@" in applicant_contact:
        # Legacy callers pass "email | phone" in applicant_contact.
        email = applicant_contact.split("|")[0].strip()
    if not phone and "|" in applicant_contact:
        parts = [p.strip() for p in applicant_contact.split("|")]
        if len(parts) > 1:
            phone = parts[1]

    target_job = ""
    for key in ("job_title", "title", "position"):
        val = job.get(key)
        if isinstance(val, str) and val.strip():
            target_job = val.strip()
            break

    header_links = _cover_letter_header_links(cv)
    link_1 = header_links[0] if len(header_links) > 0 else None
    link_2 = header_links[1] if len(header_links) > 1 else None

    return {
        "name": str(cv.get("name") or applicant_name or "Applicant").strip(),
        "phone": phone,
        "email": email,
        "target_job": target_job,
        "link_1_url": link_1[0] if link_1 else "",
        "link_1_label": link_1[1] if link_1 else "",
        "link_2_url": link_2[0] if link_2 else "",
        "link_2_label": link_2[1] if link_2 else "",
    }


def render_cover_letter_tex(
    content: dict[str, Any],
    applicant_name: str,
    applicant_contact: str = "",
    recipient_info: str = "",
    cv_data: dict[str, Any] | None = None,
    job_data: dict[str, Any] | None = None,
) -> str:
    """Render a cover letter LaTeX document from CoverLetterContent JSON."""
    language = (content.get("language") or "english").lower()
    is_german = language == "german"

    paragraphs = [
        content.get("opening_paragraph", ""),
        content.get("body_paragraph_1", ""),
        content.get("body_paragraph_2", ""),
    ]
    body_three = content.get("body_paragraph_3", "")
    if isinstance(body_three, str) and body_three.strip():
        paragraphs.append(body_three)
    paragraphs.append(content.get("closing_paragraph", ""))
    paragraphs = [p for p in paragraphs if isinstance(p, str) and p.strip()]

    header = _cover_letter_context(cv_data, job_data, applicant_name, applicant_contact)

    if is_german:
        salutation = _cover_letter_salutation(recipient_info, is_german=True)
        template_name = "cover_letter_de.tex.j2"
        extra = {
            "betreff": content.get("betreff", ""),
            "sign_off": content.get("grussformel", "Mit freundlichen Grüßen"),
            "salutation": salutation,
            "document_title": "ANSCHREIBEN",
            "date_label": "Datum:",
        }
    else:
        template_name = "cover_letter.tex.j2"
        extra = {
            "salutation": _cover_letter_salutation(recipient_info, is_german=False),
            "sign_off": "Yours Faithfully",
            "document_title": "COVER LETTER",
            "date_label": "Date:",
        }

    env = _jinja_env()
    template = env.get_template(template_name)
    return template.render(
        current_date=_format_date(language),
        paragraphs=paragraphs,
        **header,
        **extra,
    )


def _compiler_binary() -> str:
    compiler = os.getenv("LATEX_COMPILER", "tectonic").strip().lower()
    if compiler == "pdflatex":
        return shutil.which("pdflatex") or "pdflatex"
    custom = os.getenv("TECTONIC_PATH", "").strip()
    if custom:
        return custom
    return shutil.which("tectonic") or "tectonic"


def _run_tectonic(tex_path: Path, output_dir: Path) -> None:
    binary = _compiler_binary()
    result = subprocess.run(
        [binary, "-X", "compile", "--outdir", str(output_dir), str(tex_path)],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(
            f"Tectonic compilation failed (exit {result.returncode}).\n{detail}"
        )


def _run_pdflatex(tex_path: Path, output_dir: Path) -> None:
    binary = _compiler_binary()
    command = [
        binary,
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]
    last_error = ""
    for _ in range(2):
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if result.returncode == 0:
            return
        last_error = (result.stderr or result.stdout or "").strip()
    log_path = output_dir / f"{tex_path.stem}.log"
    if log_path.exists():
        last_error = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
    raise RuntimeError(f"pdflatex compilation failed.\n{last_error}")


def compile_tex_to_pdf(tex_content: str, output_dir: Path, job_name: str) -> Path:
    """
    Write ``tex_content`` to ``output_dir/{job_name}.tex`` and compile to PDF.

    Returns the path to the generated PDF file.
    """
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", job_name).strip("_") or "document"
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = output_dir / f"{safe_name}.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    compiler = os.getenv("LATEX_COMPILER", "tectonic").strip().lower()
    try:
        if compiler == "pdflatex":
            _run_pdflatex(tex_path, output_dir)
        else:
            _run_tectonic(tex_path, output_dir)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "LaTeX compiler not found. Install Tectonic "
            "(https://tectonic-typesetting.github.io/) or set LATEX_COMPILER=pdflatex "
            "with a TeX distribution installed."
        ) from exc

    pdf_path = output_dir / f"{safe_name}.pdf"
    if not pdf_path.exists():
        raise RuntimeError(
            f"Compilation finished but PDF was not produced: {pdf_path.name}"
        )
    return pdf_path
