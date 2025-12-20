"""
API Request and Response Models

This module defines all Pydantic models used for API communication.
These models provide validation, serialization, and documentation for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


# ============================================
# CV Agent Models
# ============================================

class CVUploadRequest(BaseModel):
    """Request to extract CV information from a PDF file."""
    pdf_path: str = Field(
        ...,
        description="Path to the PDF resume file",
        example="C:/Documents/resume.pdf"
    )


class ResumeInfo(BaseModel):
    """Structured resume information extracted from CV."""
    name: str = Field(description="Full name of the applicant")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    skills: List[str] = Field(description="List of professional skills")
    education: List[str] = Field(description="Educational qualifications")
    experience: List[str] = Field(description="Work experience entries")
    projects: List[str] = Field(description="List of projects the applicant has worked on")


class CVExtractionResponse(BaseModel):
    """Response from CV extraction."""
    success: bool
    cv_data: Optional[ResumeInfo] = None
    needs_clarification: bool = False
    questions: Optional[List[str]] = None
    message: str


class CVClarificationRequest(BaseModel):
    """Request to update CV with clarification answers."""
    cv_data: Dict[str, Any] = Field(description="Original CV data as JSON")
    clarifications: str = Field(description="User's answers to clarifying questions")


class CVClarificationResponse(BaseModel):
    """Response from CV clarification."""
    success: bool
    updated_cv_data: Optional[ResumeInfo] = None
    message: str


# ============================================
# Job Agent Models
# ============================================

class JobURLRequest(BaseModel):
    """Request to extract job information from URL."""
    urls: List[str] = Field(
        ...,
        description="List of job posting URLs",
        example=["https://example.com/careers/job/123"]
    )


class JobTextRequest(BaseModel):
    """Request to extract job information from pasted text."""
    job_text: str = Field(
        ...,
        description="Raw job posting text",
        example="We are looking for a Senior Software Engineer..."
    )


class JobRequirements(BaseModel):
    """Structured job requirements extracted from posting."""
    job_title: str = Field(description="Job title")
    job_level: str = Field(description="Experience level (entry, mid, senior, etc.)")
    required_skills: List[str] = Field(description="Required technical skills")
    preferred_skills: List[str] = Field(default=[], description="Preferred skills")
    years_experience: Optional[int] = Field(default=None, description="Years of experience required")
    employment_type: str = Field(description="Employment type (Full-time, Contract, etc.)")
    location: str = Field(description="Job location")
    responsibilities: List[str] = Field(description="Key responsibilities")
    qualifications: List[str] = Field(default=[], description="Required qualifications")
    key_requirements: List[str] = Field(description="Critical must-have requirements")


class JobExtractionResponse(BaseModel):
    """Response from job extraction."""
    success: bool
    job_data: Optional[JobRequirements] = None
    message: str


class CompanyResearchRequest(BaseModel):
    """Request to research company information."""
    company_name: str = Field(
        ...,
        description="Name of the company to research",
        example="Google"
    )


class CompanyInfo(BaseModel):
    """Structured company information from research."""
    company_name: str = Field(description="Official company name")
    industry: str = Field(description="Industry sector")
    company_size: Optional[str] = Field(default=None, description="Company size category")
    mission_statement: Optional[str] = Field(default=None, description="Mission statement")
    core_values: List[str] = Field(description="Core values and principles")
    recent_news: List[str] = Field(default=[], description="Recent news and developments")
    company_culture: str = Field(description="Company culture description")
    products_services: List[str] = Field(default=[], description="Main products or services")


class CompanyResearchResponse(BaseModel):
    """Response from company research."""
    success: bool
    company_data: Optional[CompanyInfo] = None
    message: str


# ============================================
# Writer Agent Models
# ============================================

class CVJobAlignmentRequest(BaseModel):
    """Request to analyze CV-job alignment."""
    cv_data: Dict[str, Any] = Field(description="Resume data from CV agent")
    job_data: Dict[str, Any] = Field(description="Job requirements from job agent")


class CVTailoringPlan(BaseModel):
    """Plan for tailoring CV to match job."""
    matching_experiences: List[str] = Field(description="Matching experience entries")
    matching_skills: List[str] = Field(description="Matching skills")
    relevant_projects: List[str] = Field(description="Relevant projects")
    keywords_to_incorporate: List[str] = Field(description="Keywords to include")
    reordering_suggestions: str = Field(description="Suggestions for reordering")
    emphasis_points: List[str] = Field(description="Points to emphasize")
    reasoning: str = Field(description="Reasoning for changes")


class CVJobAlignmentResponse(BaseModel):
    """Response from alignment analysis."""
    success: bool
    tailoring_plan: Optional[CVTailoringPlan] = None
    message: str


class GenerateTailoredCVRequest(BaseModel):
    """Request to generate tailored CV."""
    cv_data: Dict[str, Any] = Field(description="Original CV data")
    tailoring_plan: Dict[str, Any] = Field(description="Tailoring plan from alignment analysis")
    output_filename: str = Field(
        description="Desired filename for PDF",
        example="john_doe_cv_tailored.pdf"
    )


class GenerateTailoredCVResponse(BaseModel):
    """Response from CV generation."""
    success: bool
    pdf_path: Optional[str] = None
    html_preview: Optional[str] = None
    message: str


class GenerateCoverLetterRequest(BaseModel):
    """Request to generate cover letter."""
    cv_data: Dict[str, Any] = Field(description="Resume data")
    job_data: Dict[str, Any] = Field(description="Job requirements")
    company_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional company info")
    output_filename: str = Field(
        description="Desired filename for PDF",
        example="john_doe_cover_letter.pdf"
    )
    recipient_info: str = Field(
        default="Hiring Manager",
        description="Who the letter is addressed to"
    )


class CoverLetterContent(BaseModel):
    """Structured cover letter content."""
    opening_paragraph: str
    body_paragraph_1: str
    body_paragraph_2: str
    body_paragraph_3: Optional[str] = ""
    closing_paragraph: str


class GenerateCoverLetterResponse(BaseModel):
    """Response from cover letter generation."""
    success: bool
    pdf_path: Optional[str] = None
    content: Optional[CoverLetterContent] = None
    message: str


# ============================================
# Supervisor Agent Models
# ============================================

class SupervisorMessage(BaseModel):
    """A single message in supervisor conversation."""
    role: Literal["user", "assistant", "system"]
    content: str


class SupervisorSessionRequest(BaseModel):
    """Request to interact with supervisor agent."""
    session_id: str = Field(
        ...,
        description="Unique session identifier for conversation continuity"
    )
    user_input: str = Field(
        ...,
        description="User's message to the supervisor"
    )


class SupervisorSessionState(BaseModel):
    """Current state of a supervisor session."""
    session_stage: str = Field(description="Current stage: init, collecting_cv, collecting_job, writer_session, complete")
    has_cv_data: bool = Field(description="Whether CV data has been collected")
    has_job_data: bool = Field(description="Whether job data has been collected")
    has_company_data: bool = Field(description="Whether company data has been collected")
    needs_clarification: bool = Field(description="Whether CV clarification is needed")
    ready_for_writer: bool = Field(description="Whether ready to start tailoring")
    current_agent: str = Field(description="Currently active agent")


class SupervisorSessionResponse(BaseModel):
    """Response from supervisor interaction."""
    success: bool
    assistant_message: str = Field(description="Supervisor's response to user")
    session_state: Optional[SupervisorSessionState] = None
    next_action: Optional[str] = Field(
        default=None,
        description="Suggested next action (wait_for_input, upload_cv, provide_job, etc.)"
    )
    message: str = Field(description="Status or error message")


class SupervisorSessionInitResponse(BaseModel):
    """Response when creating a new supervisor session."""
    success: bool
    session_id: str
    welcome_message: str
    message: str


# ============================================
# File Upload Models (for future multipart support)
# ============================================

class FileUploadResponse(BaseModel):
    """Response from file upload."""
    success: bool
    file_path: str
    filename: str
    message: str


# ============================================
# Generic Response Models
# ============================================

class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    agents_available: List[str]
    message: str


