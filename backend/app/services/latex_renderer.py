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


def _jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["latex_escape"] = latex_escape
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


def render_cover_letter_tex(
    content: dict[str, Any],
    applicant_name: str,
    applicant_contact: str,
    recipient_info: str = "Hiring Manager",
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

    if is_german:
        recipient = recipient_info.strip() if recipient_info else "Hiring Manager"
        if recipient and recipient != "Hiring Manager":
            salutation = f"Sehr geehrte/r {recipient},"
        else:
            salutation = "Sehr geehrte Damen und Herren,"
        template_name = "cover_letter_de.tex.j2"
        extra = {
            "betreff": content.get("betreff", ""),
            "grussformel": content.get("grussformel", "Mit freundlichen Grüßen"),
            "salutation": salutation,
        }
    else:
        template_name = "cover_letter.tex.j2"
        extra = {
            "salutation": f"Dear {recipient_info or 'Hiring Manager'},",
            "closing": "Sincerely,",
        }

    env = _jinja_env()
    template = env.get_template(template_name)
    return template.render(
        applicant_name=applicant_name,
        applicant_contact=applicant_contact,
        current_date=_format_date(language),
        paragraphs=paragraphs,
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
