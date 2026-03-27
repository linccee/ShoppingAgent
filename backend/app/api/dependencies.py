"""Dependency providers for FastAPI routes."""
from functools import lru_cache

from backend.app.services.agent_service import AgentService
from backend.app.services.session_service import SessionService


@lru_cache(maxsize=1)
def get_session_service() -> SessionService:
    """Return the shared session service."""
    return SessionService()


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    """Return the shared agent service."""
    return AgentService(get_session_service())
