# LLM API endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.plugin import User, UserRole
from app.models.llm import LLMExplanationRequest, LLMExplanationResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/explain", response_model=LLMExplanationResponse)
async def generate_explanation(
    request: LLMExplanationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an LLM explanation for a skill."""
    service = LLMService(db)
    return await service.generate_explanation(request)


@router.get("/logs")
async def get_explanation_logs(
    skill_slug: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get LLM explanation logs (admin/operator only)."""
    require_role(current_user, UserRole.OPERATOR)
    service = LLMService(db)
    logs = await service.get_explanation_logs(skill_slug, limit)
    return [log.to_dict() for log in logs]


@router.get("/config")
async def get_llm_config(
    current_user: User = Depends(get_current_user),
):
    """Get LLM configuration (admin only)."""
    from app.core.config import get_settings
    settings = get_settings()

    require_role(current_user, UserRole.ADMIN)

    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "has_api_key": bool(settings.llm_api_key),
        "timeout_seconds": settings.llm_timeout_seconds,
    }
