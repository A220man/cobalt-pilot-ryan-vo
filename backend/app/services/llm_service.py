# LLM service - handles LLM explanation generation
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.models.llm import (
    LLMConfig,
    LLMProvider,
    LLMExplanationRequest,
    LLMExplanationResponse,
    LLMExplanationLog,
    create_llm_adapter,
)


class LLMService:
    """Service for generating LLM explanations of skills."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    def _get_config(self) -> LLMConfig:
        """Build LLM config from settings."""
        return LLMConfig(
            provider=LLMProvider(self.settings.llm_provider),
            model=self.settings.llm_model,
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            timeout_seconds=self.settings.llm_timeout_seconds,
        )

    async def generate_explanation(self, request: LLMExplanationRequest) -> LLMExplanationResponse:
        """Generate an LLM explanation for a skill."""
        config = self._get_config()
        adapter = create_llm_adapter(config)

        if not config.api_key and config.provider != LLMProvider.OLLAMA:
            # Return a helpful error response instead of failing
            return LLMExplanationResponse(
                explanation="LLM explanations require an API key. Please configure llm_api_key in settings.",
                provider=config.provider.value,
                model=config.model,
                advisory=True,
            )

        try:
            response = await adapter.generate_explanation(request)

            # Log the explanation request
            log_entry = LLMExplanationLog(
                skill_slug=request.skill_slug,
                plugin_slug=request.plugin_slug,
                provider=config.provider.value,
                model=config.model,
                question=request.question,
                response_preview=response.explanation[:200] if response.explanation else None,
            )
            self.db.add(log_entry)
            await self.db.commit()

            return response
        except Exception as e:
            # Return error as explanation (advisory) rather than raising
            return LLMExplanationResponse(
                explanation=f"Failed to generate explanation: {str(e)}",
                provider=config.provider.value,
                model=config.model,
                advisory=True,
            )

    async def get_explanation_logs(self, skill_slug: Optional[str] = None, limit: int = 50) -> list[LLMExplanationLog]:
        """Get explanation logs for audit."""
        query = select(LLMExplanationLog).order_by(LLMExplanationLog.created_at.desc()).limit(limit)
        if skill_slug:
            query = query.where(LLMExplanationLog.skill_slug == skill_slug)
        result = await self.db.execute(query)
        return list(result.scalars().all())
