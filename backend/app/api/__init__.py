"""
API Routes

This module exports all API routers for registration in the main application.
"""

from app.api.cv import router as cv_router
from app.api.job import router as job_router
from app.api.writer import router as writer_router
from app.api.supervisor import router as supervisor_router

__all__ = [
    "cv_router",
    "job_router",
    "writer_router",
    "supervisor_router"
]

