"""
Supervisor Agent API Endpoints

Provides the main orchestration API for the multi-agent workflow.
The supervisor manages the conversation and routes to specialized agents.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import json

from app.models.schemas import (
    SupervisorSessionRequest,
    SupervisorSessionResponse,
    SupervisorSessionInitResponse,
    SupervisorSessionState
)
from app.services.session_manager import SessionManager, get_session_manager
from app.agents.supervisor_agent import create_supervisor_graph

router = APIRouter(prefix="/api/supervisor", tags=["Supervisor Agent"])

# Create supervisor graph instance (with memory)
supervisor_app = create_supervisor_graph()


@router.post(
    "/session/start",
    response_model=SupervisorSessionInitResponse,
    summary="Start New Supervisor Session",
    description="Create a new conversation session with the supervisor agent."
)
async def start_session(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Start a new supervisor session.
    
    **Purpose:**
    Creates a new conversation context for the full job application workflow.
    
    **Workflow:**
    1. Creates unique session ID
    2. Initializes conversation state
    3. Returns welcome message
    
    **Returns:**
    - `session_id`: Use this ID for all subsequent requests
    - `welcome_message`: Initial greeting and instructions
    
    **Next Steps:**
    Send user messages to `/session/message` with the session_id.
    
    **Example Usage:**
    ```python
    # 1. Start session
    response = requests.post("/api/supervisor/session/start")
    session_id = response.json()["session_id"]
    
    # 2. Send messages
    requests.post("/api/supervisor/session/message", json={
        "session_id": session_id,
        "user_input": "I want to tailor my CV"
    })
    ```
    """
    try:
        # Create new session
        session_id = session_manager.create_session()
        
        welcome_message = """Hi there! I'm your Job Application Assistant!

I'm here to help you create tailored CVs and cover letters that perfectly match job opportunities.

Here's how I can help:
1. Extract and analyze your CV
2. Analyze job postings and research companies
3. Tailor your CV to highlight relevant experience
4. Write compelling, personalized cover letters

To get started, just share your CV file path with me!"""
        
        return SupervisorSessionInitResponse(
            success=True,
            session_id=session_id,
            welcome_message=welcome_message,
            message="Session created successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )


@router.post(
    "/session/message",
    response_model=SupervisorSessionResponse,
    summary="Send Message to Supervisor",
    description="Send a user message to the supervisor agent and get a response."
)
async def send_message(
    request: SupervisorSessionRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Send a message to the supervisor and continue the conversation.
    
    **Purpose:**
    Main endpoint for interacting with the supervisor agent. The supervisor
    will route your request to the appropriate specialized agent (CV, Job, Writer).
    
    **Workflow:**
    1. Retrieves session state
    2. Processes user input through supervisor graph
    3. Updates session state
    4. Returns assistant's response
    
    **Parameters:**
    - `session_id`: Session identifier from `/session/start`
    - `user_input`: User's message/request
    
    **Returns:**
    - `assistant_message`: Supervisor's response
    - `session_state`: Current state of the workflow
    - `next_action`: Suggested next step
    
    **The supervisor can handle:**
    - CV file paths: Triggers CV extraction
    - Job URLs: Triggers job extraction from URL
    - Job text: Triggers job extraction from pasted text
    - Company names: Triggers company research
    - Clarification answers: Updates CV data
    - Tailoring requests: Hands off to Writer agent
    - General questions: Provides help and guidance
    
    **State Tracking:**
    The session maintains state across messages, tracking:
    - CV data (if provided)
    - Job data (if provided)
    - Company data (if researched)
    - Current stage in the workflow
    - Which agent is currently active
    """
    try:
        # Retrieve session
        session = session_manager.get_session(request.session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired. Please start a new session."
            )
        
        # Update session with user input
        session["user_input"] = request.user_input
        session["conversation_count"] += 1
        
        # Prepare config for graph (for checkpointing)
        config = {"configurable": {"thread_id": request.session_id}}
        
        # Invoke supervisor graph
        try:
            result = supervisor_app.invoke(session, config)
            
            # Update session with result
            session_manager.update_session(request.session_id, result)
            
            # Extract response
            assistant_message = result.get("supervisor_response", "I'm not sure how to respond to that.")
            
            # Build session state response
            session_state = SupervisorSessionState(
                session_stage=result.get("session_stage", "init"),
                has_cv_data=result.get("cv_data") is not None,
                has_job_data=result.get("job_data") is not None,
                has_company_data=result.get("company_data") is not None,
                needs_clarification=result.get("needs_clarification", False),
                ready_for_writer=result.get("ready_for_writer", False),
                current_agent=result.get("current_agent", "supervisor")
            )
            
            return SupervisorSessionResponse(
                success=True,
                assistant_message=assistant_message,
                session_state=session_state,
                next_action=result.get("next_action"),
                message="Message processed successfully"
            )
            
        except Exception as e:
            # Handle errors in graph execution
            error_message = f"I encountered an error: {str(e)}\n\nPlease try rephrasing your request or type 'help' for guidance."
            
            return SupervisorSessionResponse(
                success=False,
                assistant_message=error_message,
                session_state=None,
                next_action="wait_for_input",
                message=f"Error in supervisor processing: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.get(
    "/session/{session_id}/state",
    summary="Get Session State",
    description="Retrieve the current state of a supervisor session."
)
async def get_session_state(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get current session state without sending a message.
    
    **Purpose:**
    Check the status of a conversation session, useful for:
    - Reconnecting after disconnect
    - Checking what data has been collected
    - Understanding current workflow stage
    
    **Returns:**
    Session metadata and current state information.
    """
    try:
        session_info = session_manager.get_session_info(session_id)
        
        if session_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        return {
            "success": True,
            "session_info": session_info,
            "message": "Session state retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session state: {str(e)}"
        )


@router.delete(
    "/session/{session_id}",
    summary="Delete Session",
    description="End and delete a supervisor session."
)
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Delete a session and clean up resources.
    
    **Use this when:**
    - User is done with the conversation
    - Starting fresh with a new application
    - Cleaning up after errors
    
    **Note:** Deleted sessions cannot be recovered.
    """
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting session: {str(e)}"
        )


@router.get(
    "/health",
    summary="Supervisor Agent Health Check"
)
async def supervisor_health(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Health check for supervisor agent.
    
    Returns status and active session count.
    """
    return {
        "status": "healthy",
        "agent": "supervisor",
        "active_sessions": session_manager.get_session_count(),
        "available_agents": ["cv_agent", "job_agent", "writer_agent"],
        "message": "Supervisor agent is operational"
    }


@router.post(
    "/cleanup-sessions",
    summary="Cleanup Expired Sessions",
    description="Manually trigger cleanup of expired sessions (admin endpoint)."
)
async def cleanup_sessions(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Cleanup expired sessions.
    
    This is typically called by a background task, but can be
    manually triggered for testing or maintenance.
    """
    try:
        cleaned = session_manager.cleanup_expired_sessions()
        
        return {
            "success": True,
            "cleaned_sessions": cleaned,
            "remaining_sessions": session_manager.get_session_count(),
            "message": f"Cleaned up {cleaned} expired sessions"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up sessions: {str(e)}"
        )


