# LLM API endpoint tests
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm import LLMExplanationResponse, LLMExplanationLog
from app.models.plugin import User, UserRole
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_generate_explanation_success(client_with_auth: AsyncClient, test_db: AsyncSession):
    """Test successful explanation generation via API."""
    with patch('app.services.llm_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "ollama"
        mock_settings.llm_model = "llama3"
        mock_settings.llm_base_url = "http://localhost:11434"
        mock_settings.llm_api_key = None
        mock_settings.llm_timeout_seconds = 30
        mock_get_settings.return_value = mock_settings

        with patch('app.services.llm_service.create_llm_adapter') as mock_create:
            mock_adapter = AsyncMock()
            mock_response = LLMExplanationResponse(
                explanation="This skill processes data using machine learning.",
                provider="ollama",
                model="llama3",
                advisory=True,
            )
            mock_adapter.generate_explanation.return_value = mock_response
            mock_create.return_value = mock_adapter

            response = await client_with_auth.post(
                "/llm/explain",
                json={
                    "skill_slug": "test-skill",
                    "plugin_slug": "test-plugin",
                    "question": "How does this work?",
                    "context": "Skill description: A data processing skill",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["explanation"] == "This skill processes data using machine learning."
            assert data["provider"] == "ollama"
            assert data["model"] == "llama3"
            assert data["advisory"] is True
            mock_adapter.generate_explanation.assert_called_once()


@pytest.mark.asyncio
async def test_generate_explanation_no_api_key(client_with_auth: AsyncClient, test_db: AsyncSession):
    """Test explanation generation when no API key is configured."""
    with patch('app.services.llm_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "openai-compatible"
        mock_settings.llm_model = "gpt-4o-mini"
        mock_settings.llm_base_url = None
        mock_settings.llm_api_key = None
        mock_settings.llm_timeout_seconds = 30
        mock_get_settings.return_value = mock_settings

        response = await client_with_auth.post(
            "/llm/explain",
            json={
                "skill_slug": "test-skill",
                "plugin_slug": "test-plugin",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["advisory"] is True
        assert "API key" in data["explanation"]
        assert data["provider"] == "openai-compatible"
        assert data["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_generate_explanation_unauthorized(client: AsyncClient):
    """Test that explanation generation requires authentication."""
    response = await client.post(
        "/llm/explain",
        json={
            "skill_slug": "test-skill",
            "plugin_slug": "test-plugin",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_explanation_logs_operator(client_with_operator_auth: AsyncClient, test_db: AsyncSession):
    """Test getting explanation logs as operator."""
    # Create some log entries
    log1 = LLMExplanationLog(
        skill_slug="skill1",
        plugin_slug="plugin1",
        provider="ollama",
        model="llama3",
        question="How does this work?",
        response_preview="This skill processes...",
    )
    log2 = LLMExplanationLog(
        skill_slug="skill2",
        plugin_slug="plugin1",
        provider="openai-compatible",
        model="gpt-4o-mini",
        question=None,
        response_preview="This skill analyzes...",
    )
    test_db.add_all([log1, log2])
    await test_db.commit()

    response = await client_with_operator_auth.get("/llm/logs?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["skill_slug"] == "skill2"  # Ordered by created_at desc
    assert data[1]["skill_slug"] == "skill1"
    assert data[0]["provider"] == "openai-compatible"
    assert data[1]["provider"] == "ollama"


@pytest.mark.asyncio
async def test_get_explanation_logs_viewer_forbidden(client_with_auth: AsyncClient):
    """Test that viewers cannot access explanation logs."""
    response = await client_with_auth.get("/llm/logs")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_explanation_logs_unauthorized(client: AsyncClient):
    """Test that explanation logs require authentication."""
    response = await client.get("/llm/logs")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_explanation_logs_filter_by_skill(client_with_operator_auth: AsyncClient, test_db: AsyncSession):
    """Test filtering explanation logs by skill slug."""
    log1 = LLMExplanationLog(
        skill_slug="skill1",
        plugin_slug="plugin1",
        provider="ollama",
        model="llama3",
        question="How does this work?",
        response_preview="This skill processes...",
    )
    log2 = LLMExplanationLog(
        skill_slug="skill2",
        plugin_slug="plugin1",
        provider="openai-compatible",
        model="gpt-4o-mini",
        question=None,
        response_preview="This skill analyzes...",
    )
    test_db.add_all([log1, log2])
    await test_db.commit()

    response = await client_with_operator_auth.get("/llm/logs?skill_slug=skill1&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["skill_slug"] == "skill1"


@pytest.mark.asyncio
async def test_get_llm_config_admin(client_with_admin_auth: AsyncClient):
    """Test getting LLM config as admin."""
    with patch('app.core.config.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_model = "claude-3-opus"
        mock_settings.llm_base_url = "https://api.anthropic.com"
        mock_settings.llm_api_key = "sk-test-key"
        mock_settings.llm_timeout_seconds = 60
        mock_get_settings.return_value = mock_settings

        response = await client_with_admin_auth.get("/llm/config")

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3-opus"
        assert data["base_url"] == "https://api.anthropic.com"
        assert data["has_api_key"] is True
        assert data["timeout_seconds"] == 60


@pytest.mark.asyncio
async def test_get_llm_config_operator_forbidden(client_with_operator_auth: AsyncClient):
    """Test that operators cannot access LLM config."""
    response = await client_with_operator_auth.get("/llm/config")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_llm_config_viewer_forbidden(client_with_auth: AsyncClient):
    """Test that viewers cannot access LLM config."""
    response = await client_with_auth.get("/llm/config")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_llm_config_unauthorized(client: AsyncClient):
    """Test that LLM config requires authentication."""
    response = await client.get("/llm/config")

    assert response.status_code == 401

