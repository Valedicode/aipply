"""Smoke test: render a cover letter through the entry-level template and compile it."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.services.latex_renderer import compile_tex_to_pdf, render_cover_letter_tex

content = {
    "language": "english",
    "opening_paragraph": "I am excited to apply for the ML Engineer role at your company.",
    "body_paragraph_1": (
        "My experience in machine learning and multi-agent systems aligns well with your requirements."
    ),
    "body_paragraph_2": (
        "I have built production ML pipelines and enjoy solving complex engineering problems."
    ),
    "closing_paragraph": "Thank you for your consideration. I look forward to hearing from you.",
}
cv = {
    "name": "Kevin Ha",
    "email": "kevinhachong@gmail.com",
    "phone": "+49 123 456",
    "linkedin_url": "https://linkedin.com/in/kevinha",
    "github_url": "https://github.com/Valedicode",
}
job = {"job_title": "ML Engineer"}

tex = render_cover_letter_tex(
    content,
    "Kevin Ha",
    recipient_info="Dr. Jane Smith",
    cv_data=cv,
    job_data=job,
)
out = Path("data")
tex_path = out / "smoke_kevin_cover_letter.tex"
tex_path.write_text(tex, encoding="utf-8")
pdf = compile_tex_to_pdf(tex, out, "smoke_kevin_cover_letter")
print("TEX written:", tex_path.resolve())
print("PDF created:", pdf.resolve(), pdf.stat().st_size, "bytes")
