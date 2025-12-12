"""
Writer Agent API Endpoints

Provides endpoints for CV-job alignment analysis, tailored CV generation,
and cover letter generation.
"""

from fastapi import APIRouter, HTTPException, status
import json

from app.models.schemas import (
    CVJobAlignmentRequest,
    CVJobAlignmentResponse,
    GenerateTailoredCVRequest,
    GenerateTailoredCVResponse,
    GenerateCoverLetterRequest,
    GenerateCoverLetterResponse,
    CVTailoringPlan,
    CoverLetterContent,
    ResumeInfo,
    JobRequirements
)
from app.agents.writer_agent import (
    analyze_cv_job_alignment,
    generate_tailored_cv_html,
    generate_cover_letter_content,
    generate_cv_pdf,
    generate_cover_letter_pdf
)

router = APIRouter(prefix="/api/writer", tags=["Writer Agent"])


@router.post(
    "/analyze-alignment",
    response_model=CVJobAlignmentResponse,
    summary="Analyze CV-Job Alignment",
    description="Analyze how well a CV matches job requirements and create a tailoring plan."
)
async def analyze_alignment(request: CVJobAlignmentRequest):
    """
    Analyze CV-job alignment and create a tailoring plan.
    
    **Purpose:**
    This is the first step in the tailoring process. It performs gap analysis
    to identify which parts of the CV align with the job and how to optimize.
    
    **Workflow:**
    1. Compares CV skills/experience with job requirements
    2. Identifies matching experiences, skills, and projects
    3. Suggests keywords to incorporate
    4. Recommends section reordering and emphasis points
    
    **Parameters:**
    - `cv_data`: Resume data from CV agent (as dict)
    - `job_data`: Job requirements from job agent (as dict)
    
    **Returns:**
    - Tailoring plan with specific, actionable recommendations
    
    **Next Steps:**
    - Present plan to user for approval
    - Use plan in `/generate-cv` endpoint
    """
    try:
        # Validate CV data structure
        try:
            ResumeInfo(**request.cv_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CV data structure: {str(e)}"
            )
        
        # Validate job data structure
        try:
            JobRequirements(**request.job_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job data structure: {str(e)}"
            )
        
        # Convert to JSON strings for the tool
        cv_json = json.dumps(request.cv_data)
        job_json = json.dumps(request.job_data)
        
        # Analyze alignment
        tailoring_plan_json = analyze_cv_job_alignment.invoke({
            "cv_json": cv_json,
            "job_json": job_json
        })
        
        tailoring_plan_dict = json.loads(tailoring_plan_json)
        
        return CVJobAlignmentResponse(
            success=True,
            tailoring_plan=CVTailoringPlan(**tailoring_plan_dict),
            message="Alignment analysis completed successfully."
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse tailoring plan: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing alignment: {str(e)}"
        )


@router.post(
    "/generate-cv",
    response_model=GenerateTailoredCVResponse,
    summary="Generate Tailored CV",
    description="Generate a tailored CV PDF based on the original CV and tailoring plan."
)
async def generate_cv(request: GenerateTailoredCVRequest):
    """
    Generate tailored CV HTML and PDF.
    
    **Prerequisites:**
    - Must have run `/analyze-alignment` first to get tailoring plan
    - User should have approved the tailoring plan
    
    **Workflow:**
    1. Generates tailored HTML based on CV + tailoring plan
    2. Converts HTML to professional PDF with styling
    3. Saves PDF to backend/data/ directory
    
    **Parameters:**
    - `cv_data`: Original CV data from CV agent
    - `tailoring_plan`: Tailoring plan from alignment analysis
    - `output_filename`: Desired filename (e.g., "john_doe_cv.pdf")
    
    **Returns:**
    - Path to generated PDF file
    - HTML preview (for frontend display if needed)
    
    **Note:** PDF is saved to backend/data/ directory by default.
    """
    try:
        # Validate data structures
        try:
            ResumeInfo(**request.cv_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CV data: {str(e)}"
            )
        
        try:
            CVTailoringPlan(**request.tailoring_plan)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tailoring plan: {str(e)}"
            )
        
        # Validate filename
        if not request.output_filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Output filename must end with .pdf"
            )
        
        # Convert to JSON strings
        cv_json = json.dumps(request.cv_data)
        plan_json = json.dumps(request.tailoring_plan)
        
        # Generate HTML
        html_content = generate_tailored_cv_html.invoke({
            "cv_json": cv_json,
            "tailoring_plan_json": plan_json
        })
        
        # Generate PDF
        applicant_name = request.cv_data.get('name', 'Applicant')
        pdf_result = generate_cv_pdf.invoke({
            "html_content": html_content,
            "output_filename": request.output_filename,
            "applicant_name": applicant_name
        })
        
        # Check if PDF generation was successful
        if "Error" in pdf_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=pdf_result
            )
        
        # Extract path from result message
        pdf_path = pdf_result.split("at: ")[-1] if "at: " in pdf_result else None
        
        return GenerateTailoredCVResponse(
            success=True,
            pdf_path=pdf_path,
            html_preview=html_content[:500] + "..." if len(html_content) > 500 else html_content,
            message=pdf_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating CV: {str(e)}"
        )


@router.post(
    "/generate-cover-letter",
    response_model=GenerateCoverLetterResponse,
    summary="Generate Cover Letter",
    description="Generate a tailored cover letter PDF based on CV, job requirements, and optional company info."
)
async def generate_cover_letter(request: GenerateCoverLetterRequest):
    """
    Generate tailored cover letter.
    
    **Purpose:**
    Creates a compelling, personalized cover letter that:
    - Connects candidate's background to job requirements
    - Demonstrates understanding of company (if company data provided)
    - Maintains authentic, professional tone
    
    **Workflow:**
    1. Generates structured cover letter content (paragraphs)
    2. Formats into professional business letter
    3. Converts to PDF with appropriate styling
    4. Saves to backend/data/ directory
    
    **Parameters:**
    - `cv_data`: Resume data from CV agent
    - `job_data`: Job requirements from job agent
    - `company_data`: Optional company info from company research
    - `output_filename`: Desired filename (e.g., "john_doe_cover_letter.pdf")
    - `recipient_info`: Who to address (default: "Hiring Manager")
    
    **Returns:**
    - Path to generated PDF
    - Cover letter content (structured paragraphs)
    
    **Tip:** Include company_data for more personalized cover letters.
    """
    try:
        # Validate data structures
        try:
            ResumeInfo(**request.cv_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CV data: {str(e)}"
            )
        
        try:
            JobRequirements(**request.job_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job data: {str(e)}"
            )
        
        # Validate filename
        if not request.output_filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Output filename must end with .pdf"
            )
        
        # Convert to JSON strings
        cv_json = json.dumps(request.cv_data)
        job_json = json.dumps(request.job_data)
        company_json = json.dumps(request.company_data) if request.company_data else ""
        
        # Generate cover letter content
        content_json = generate_cover_letter_content.invoke({
            "cv_json": cv_json,
            "job_json": job_json,
            "company_json": company_json
        })
        
        content_dict = json.loads(content_json)
        
        # Get applicant info for PDF
        applicant_name = request.cv_data.get('name', 'Applicant')
        applicant_email = request.cv_data.get('email', '')
        applicant_phone = request.cv_data.get('phone', '')
        applicant_contact = f"{applicant_email} | {applicant_phone}"
        
        # Generate PDF
        pdf_result = generate_cover_letter_pdf.invoke({
            "content_json": content_json,
            "output_filename": request.output_filename,
            "applicant_name": applicant_name,
            "applicant_contact": applicant_contact,
            "recipient_info": request.recipient_info
        })
        
        # Check if PDF generation was successful
        if "Error" in pdf_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=pdf_result
            )
        
        # Extract path from result message
        pdf_path = pdf_result.split("at: ")[-1] if "at: " in pdf_result else None
        
        return GenerateCoverLetterResponse(
            success=True,
            pdf_path=pdf_path,
            content=CoverLetterContent(**content_dict),
            message=pdf_result
        )
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse cover letter content: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating cover letter: {str(e)}"
        )


@router.get(
    "/health",
    summary="Writer Agent Health Check",
    description="Check if writer agent tools are available."
)
async def writer_health():
    """
    Health check for writer agent.
    
    Returns status of available tools and dependencies.
    """
    available_tools = [
        "analyze_cv_job_alignment",
        "generate_tailored_cv_html",
        "generate_cover_letter_content",
        "generate_cv_pdf",
        "generate_cover_letter_pdf"
    ]
    
    return {
        "status": "healthy",
        "agent": "writer",
        "available_tools": available_tools,
        "message": "Writer agent is operational"
    }


