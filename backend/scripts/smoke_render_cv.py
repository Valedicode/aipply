"""Smoke test: render a Kevin-like CV through the new template and compile it."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.services.latex_renderer import render_cv_tex, compile_tex_to_pdf

cv = {
    "name": "Kevin Ha",
    "email": "kevinhachong@gmail.com",
    "phone": "",
    "location": "Aachen, 52070",
    "github_url": "https://github.com/Valedicode",
    "summary": (
        "M.Sc. Computer Science student building multi-agent LLM systems and applied ML "
        "pipelines. Google Gemma 4 Developer Competition finalist. Seeking Multi-agent "
        "systems / ML engineering roles."
    ),
    "skills": [
        {"name": "ML / Agent Frameworks", "keywords": ["LangChain", "LangGraph", "AI SDK 5", "PyTorch", "Gemma", "FinBERT", "YOLOv8", "Whisper"]},
        {"name": "Backend, Frontend & Tools", "keywords": ["FastAPI", "Django", "PostgreSQL", "Docker", "React", "Next.js", "Tailwind CSS", "Git"]},
        {"name": "Languages", "keywords": ["Python", "Java", "C", "JavaScript"]},
    ],
    "education": [
        {
            "institution": "RWTH Aachen University",
            "degree": "M.Sc. in Computer Science",
            "location": "Aachen, Germany",
            "dates": "Expected: September 2027",
            "grade": "Current Grade: 1.6 (German System)",
        },
        {
            "institution": "RWTH Aachen University",
            "degree": "B.Sc. in Computer Science",
            "location": "Aachen, Germany",
            "dates": "Graduation Date: September 2025",
            "grade": "2.0 (German System)",
        },
        {
            "institution": "Study Abroad: Shanghai Jiao Tong University",
            "degree": "Exchange Semester in Computer Science",
            "location": "Shanghai, China",
            "dates": "March 2026 -- August 2026",
            "grade": "1.0 (German System)",
        },
        {
            "institution": "Gymnasium an der Gartenstraße",
            "degree": "Higher School Certificate",
            "location": "Mönchengladbach, Germany",
            "dates": "Graduation Date: July 2022",
            "grade": "1.0 (German System)",
            "details": ["Awards: Arconic Foundation Innovative Sustainability Business Idea Award"],
        },
    ],
    "experience": [
        {
            "position": "Internship -- Software Development",
            "company": "Fraunhofer-Institut für Produktionstechnologie IPT",
            "location": "Aachen, Germany",
            "duration": "April 2024 -- July 2024",
            "responsibilities": [
                "Developed YAMS, a management website (Python/Django/PostgreSQL) for handling institute inquiries and acquisition data; improved usability with a responsive Bootstrap redesign.",
            ],
        },
        {
            "position": "Private Tutor -- Mathematics",
            "company": "",
            "duration": "April 2022 -- December 2024",
            "responsibilities": [
                "Designed personalized lesson plans for high school students; helped students improve by at least one grade level.",
            ],
        },
    ],
    "projects": [
        {
            "name": "BiasLens (Google Gemma 4 Developer Competition Finalist)",
            "description": "Explainable multimodal bias-analysis pipeline for short-form video with a LangGraph-orchestrated multi-agent architecture.",
            "technologies": ["Gemma 4", "LangGraph", "YOLOv8", "Whisper", "FastAPI", "Next.js"],
            "outcomes": [],
        },
        {
            "name": "Financial Sentiment Analyzer",
            "description": "Led a 5-person team building an AI sentiment analysis platform for the Aachen Investment Club.",
            "technologies": ["FastAPI", "FinBERT"],
            "outcomes": ["Feeds the club newsletter."],
        },
    ],
    "leadership_activities": [
        {
            "role": "Project Manager -- Sentiment Analysis Initiative",
            "organization": "Aachen Investment Club",
            "location": "Aachen, Germany",
            "dates": "October 2025 -- January 2026",
            "highlights": [
                "Led a 5-person student team building a financial sentiment analysis system; owned planning, task allocation, and weekly reviews.",
            ],
        },
        {
            "role": "Deputy Course Instructor -- Digital Café",
            "organization": "Mehrgenerationenhaus",
            "dates": "July 2022 -- January 2025",
            "description": "One-on-one digital literacy support for senior citizens on smartphones, computers, and online safety.",
        },
    ],
}

tex = render_cv_tex(cv)
out = Path("data")
tex_path = out / "smoke_kevin_cv.tex"
pdf = compile_tex_to_pdf(tex, out, "smoke_kevin_cv")
print("TEX written:", tex_path.resolve())
print("PDF created:", pdf.resolve(), pdf.stat().st_size, "bytes")
