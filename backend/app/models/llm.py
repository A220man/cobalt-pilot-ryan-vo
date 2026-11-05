from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


from app.core.database import Base

class LLMProvider(str, PyEnum):
    OPENAI_COMPATIBLE = "openai-compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"

class LLMExplanationRequest(BaseModel):
    """Request for LLM explanation of a skill."""
    skill_slug: str
    plugin_slug: str
    question: Optional[str] = None
    context: Optional[str] = None


class LLMExplanationResponse(BaseModel):
    """Response from LLM explanation."""
    explanation: str
    provider: str
    model: str
    advisory: bool = True
    disclaimer: str = "This explanation is AI-generated and advisory only. Verify against official documentation."


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: LLMProvider = LLMProvider.OPENAI_COMPATIBLE
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    temperature: float = 0.3
    max_tokens: int = 1000


class LLMAdapterBase:
    """Base class for LLM adapters."""

    def __init__(self, config: LLMConfig):
        self.config = config

    async def generate_explanation(self, request: LLMExplanationRequest) -> LLMExplanationResponse:
        raise NotImplementedError

    def _build_prompt(self, request: LLMExplanationRequest) -> str:
        skill_info = f"Skill: {request.skill_slug} (Plugin: {request.plugin_slug})"
        if request.context:
            skill_info += f"\nContext: {request.context}"
        if request.question:
            skill_info += f"\nQuestion: {request.question}"

        return f"""You are a helpful assistant explaining a skill from the Cobalt Pilot plugin ecosystem.

{skill_info}

Provide a clear, concise explanation of this skill, its purpose, and how it might be used. Keep it practical and focused on what a developer would need to know. Do not make up functionality that isn't described."""

    def _build_advisory_response(self, content: str) -> LLMExplanationResponse:
        return LLMExplanationResponse(
            explanation=content,
            provider=self.config.provider.value,
            model=self.config.model,
            advisory=True,
        )


class OpenAICompatibleAdapter(LLMAdapterBase):
    """OpenAI-compatible API adapter (OpenAI, Azure OpenAI, local servers like vLLM)."""

    async def generate_explanation(self, request: LLMExplanationRequest) -> LLMExplanationResponse:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful technical assistant explaining plugin skills."},
                {"role": "user", "content": self._build_prompt(request)},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        base_url = self.config.base_url or "https://api.openai.com/v1"
        url = f"{base_url.rstrip('/')}/chat/completions"

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return self._build_advisory_response(content)


class AnthropicAdapter(LLMAdapterBase):
    """Anthropic Claude API adapter."""

    async def generate_explanation(self, request: LLMExplanationRequest) -> LLMExplanationResponse:
        import httpx

        headers = {
            "x-api-key": self.config.api_key or "",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "user", "content": self._build_prompt(request)},
            ],
        }

        base_url = self.config.base_url or "https://api.anthropic.com/v1"
        url = f"{base_url.rstrip('/')}/messages"

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["content"][0]["text"]
        return self._build_advisory_response(content)


class GeminiAdapter(LLMAdapterBase):
    """Google Gemini API adapter."""

    async def generate_explanation(self, request: LLMExplanationRequest) -> LLMExplanationResponse:
        import httpx

        payload = {
            "contents": [
                {"parts": [{"text": self._build_prompt(request)}]}
            ],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
        }

        base_url = self.config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        api_key = self.config.api_key
        url = f"{base_url.rstrip('/')}/models/{self.config.model}:generateContent?key={api_key}"

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._build_advisory_response(content)


class OllamaAdapter(LLMAdapterBase):
    """Ollama local LLM adapter."""

    async def generate_explanation(self, request: LLMExplanationRequest) -> LLMExplanationResponse:
        import httpx

        payload = {
            "model": self.config.model,
            "prompt": self._build_prompt(request),
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        base_url = self.config.base_url or "http://localhost:11434"
        url = f"{base_url.rstrip('/')}/api/generate"

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("response", "")
        return self._build_advisory_response(content)


def create_llm_adapter(config: LLMConfig) -> LLMAdapterBase:
    """Factory function to create the appropriate LLM adapter."""
    adapters = {
        LLMProvider.OPENAI_COMPATIBLE: OpenAICompatibleAdapter,
        LLMProvider.ANTHROPIC: AnthropicAdapter,
        LLMProvider.GEMINI: GeminiAdapter,
        LLMProvider.OLLAMA: OllamaAdapter,
    }
    adapter_class = adapters.get(config.provider)
    if not adapter_class:
        raise ValueError(f"Unknown LLM provider: {config.provider}")
    return adapter_class(config)


class LLMExplanationLog(Base):
    """Log of LLM explanation requests for audit trail."""
    __tablename__ = "llm_explanation_logs"

    id = Column(Integer, primary_key=True, index=True)
    skill_slug = Column(String, index=True, nullable=False)
    plugin_slug = Column(String, index=True, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    question = Column(Text, nullable=True)
    response_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "skill_slug": self.skill_slug,
            "plugin_slug": self.plugin_slug,
            "provider": self.provider,
            "model": self.model,
            "question": self.question,
            "response_preview": self.response_preview,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
