## Resume Agent

An autonomous **human-in-the-loop AI agent** that takes your **generic PDF resume** and a **specific Job Description URL**, then iteratively rewrites and optimizes your resume until it tightly matches the job requirements and passes your personal approval.

---

## Concept

You provide:

- **Generic resume** as a PDF file
- **Job Description** as a URL (or pasted text, depending on the interface)

The agent:

- Scrapes and parses the job description
- Parses your existing resume from PDF
- Runs a **gap analysis** between JD requirements and your current resume
- Iteratively **rewrites and optimizes** bullets, summary, and skills
- **Pauses for your review and feedback** (human-in-the-loop)
- Incorporates your feedback into the next iteration
- Outputs a **clean, professional, targeted PDF resume**

---

## Example Workflow

1. Upload your **base resume PDF**.
2. Provide a **JD URL** (or paste the job description text).
3. The agent:
   - Scrapes/parses the JD  
   - Parses your resume  
   - Runs gap analysis and generates a first tailored draft  
4. Review a **diff view** of proposed changes:
   - Original vs rewritten bullets and sections  
   - Notes on which JD requirements are being satisfied  
5. Give feedback like:
   - “This looks too formal, make it punchier.”
6. The agent regenerates the draft with your style preferences.
7. When satisfied, click **Approve**.
8. Download your **targeted PDF resume**.


## Getting Started

### Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed
- Python 3.12 (recommended) or 3.11+ (managed by conda)

### Backend setup

1. **Clone the repo**

```bash
git clone https://github.com/Valedicode/resume-agent.git
cd resume-agent
```

2. **Create and activate the conda environment**

```bash
conda env create -f environment.yml
conda activate resume-agent
```

3. **Install backend Python dependencies**

```bash
pip install -r backend/requirements.txt
```

4. **Configure backend environment variables**

Create a `.env` file inside the `backend/` directory (next to `requirements.txt`).  
Use `backend/env.example` as a reference; at minimum you should set:

```bash
# backend/.env
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GEMINI_API_KEY=your_gemini_api_key_here
# GROQ_API_KEY=your_groq_api_key_here
```

### Frontend setup

1. **Install frontend dependencies**

```bash
cd frontend
npm install
```

2. **Configure frontend environment variables**

Create a `.env.local` file in `frontend/` (based on `frontend/env.example` if present).

### Running the app

In one terminal, start the backend from the project root:

```bash
cd backend
uvicorn app.main:app --reload
```

In another terminal, start the frontend:

```bash
cd frontend
pnpm dev
```

Then open the printed URL (typically `http://localhost:3000`) in your browser.

---

