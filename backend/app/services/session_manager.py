"""
Session Manager for Supervisor Agent

Manages conversation state across multiple API requests.
In production, this would use Redis or a database for persistence.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
from collections import defaultdict


class SessionManager:
    """
    In-memory session storage for supervisor conversations.
    
    Each session maintains:
    - Conversation history
    - Collected data (CV, job, company)
    - Current state and stage
    - Metadata (created, last active)
    """
    
    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize session manager.
        
        Args:
            ttl_minutes: Time-to-live for sessions in minutes (default: 60)
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
    
    def create_session(self) -> str:
        """
        Create a new session.
        
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        self._sessions[session_id] = {
            # Metadata
            "created_at": datetime.now(),
            "last_active": datetime.now(),
            
            # Conversation
            "messages": [],
            "conversation_count": 0,
            "user_input": "",  # Current user message
            "supervisor_response": "",  # Current supervisor response
            
            # State
            "current_agent": "supervisor",
            "session_stage": "init",
            "next_action": "wait_for_input",
            "intent": "",
            
            # Data
            "cv_data": None,
            "cv_file_path": None,
            "job_data": None,
            "company_data": None,
            
            # Clarification management
            "pending_questions": None,
            "clarifications": None,
            "needs_clarification": False,
            
            # Flags
            "ready_for_writer": False
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        # Check if session has expired
        if datetime.now() - session["last_active"] > self._ttl:
            del self._sessions[session_id]
            return None
        
        # Update last active timestamp
        session["last_active"] = datetime.now()
        
        return session
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update (can include new fields)
            
        Returns:
            True if successful, False if session not found
            
        Note:
            This method allows adding new fields to the session, not just updating
            existing ones. This is necessary because the supervisor agent may return
            fields that weren't in the initial session template.
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        # Update fields (allow adding new fields, not just updating existing ones)
        for key, value in updates.items():
            # Skip internal metadata fields that shouldn't be updated from external sources
            if key in ["created_at", "last_active"]:
                continue
            
            # Special handling for messages (append instead of replace)
            if key == "messages" and isinstance(value, list):
                if key in session:
                    session["messages"].extend(value)
                else:
                    session["messages"] = value
            else:
                # Allow updating existing fields or adding new ones
                # For critical data fields (cv_data, job_data), only update if value is not None
                # This prevents accidentally clearing data that should persist
                if key in ["cv_data", "job_data", "company_data"] and value is None and key in session:
                    # Don't overwrite existing data with None
                    continue
                session[key] = value
        
        session["last_active"] = datetime.now()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """
        Remove expired sessions.
        
        Should be called periodically (e.g., via background task).
        """
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session["last_active"] > self._ttl
        ]
        
        for sid in expired:
            del self._sessions[sid]
        
        return len(expired)
    
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self._sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata and state (without full conversation history).
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session info or None if not found
        """
        session = self.get_session(session_id)
        if session is None:
            return None
        
        return {
            "session_id": session_id,
            "created_at": session["created_at"].isoformat(),
            "last_active": session["last_active"].isoformat(),
            "session_stage": session["session_stage"],
            "current_agent": session["current_agent"],
            "has_cv_data": session["cv_data"] is not None,
            "has_job_data": session["job_data"] is not None,
            "has_company_data": session["company_data"] is not None,
            "needs_clarification": session["needs_clarification"],
            "ready_for_writer": session["ready_for_writer"],
            "message_count": len(session["messages"])
        }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.
    
    Uses dependency injection pattern for FastAPI.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(ttl_minutes=60)
    return _session_manager


def reset_session_manager():
    """Reset the session manager (useful for testing)."""
    global _session_manager
    _session_manager = None


