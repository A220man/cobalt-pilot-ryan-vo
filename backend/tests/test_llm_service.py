# LLM Service tests
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm import LLMConfig, LLMProvider, LLMExplanationRequest, LLMExplanationResponse, LLMExplanationLog
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_generate_explanation_no_api_key(test_db: AsyncSession):
    """Test LLM service returns helpful message when no API key configured."""
    # Patch get_settings before creating service
    with patch('app.services.llm_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "openai-compatible"
        mock_settings.llm_model = "gpt-4o-mini"
        mock_settings.llm_base_url = None
        mock_settings.llm_api_key = None
        mock_settings.llm_timeout_seconds = 30
        mock_get_settings.return_value = mock_settings
        
        service = LLMService(test_db)
        request = LLMExplanationRequest(
            skill_slug="test-skill",
            plugin_slug="test-plugin",
            question="How does this work?",
        )
        
        response = await service.generate_explanation(request)
        
        assert response.advisory is True
        assert "API key" in response.explanation
        assert response.provider == "openai-compatible"
        assert response.model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_llm_service_generate_explanation_with_ollama_no_key(test_db: AsyncSession):
    """Test LLM service works with Ollama (no API key required)."""
    with patch('app.services.llm_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "ollama"
        mock_settings.llm_model = "llama3"
        mock_settings.llm_base_url = "http://localhost:11434"
        mock_settings.llm_api_key = None
        mock_settings.llm_timeout_seconds = 30
        mock_get_settings.return_value = mock_settings
        
        service = LLMService(test_db)
        request = LLMExplanationRequest(
            skill_slug="test-skill",
            plugin_slug="test-plugin",
            question="How does this work?",
        )
        
        # Mock the adapter
        with patch('app.services.llm_service.create_llm_adapter') as mock_create:
            mock_adapter = AsyncMock()
            mock_adapter.generate_explanation = AsyncMock(return_value=LLMExplanationResponse(
                explanation="Test explanation from Ollama",
                provider="ollama",
                model="llama3",
                advisory=True,
            ))
            mock_create.return_value = mock_adapter
            
            response = await service.generate_explanation(request)
            
            assert response.explanation == "Test explanation from Ollama"
            assert response.provider == "ollama"
            assert response.advisory is True
            mock_adapter.generate_explanation.assert_called_once()


@pytest.mark.asyncio
async def test_llm_service_generate_explanation_logs_request(test_db: AsyncSession):
    """Test that explanation requests are logged."""
    with patch('app.services.llm_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "ollama"
        mock_settings.llm_model = "llama3"
        mock_settings.llm_base_url = "http://localhost:11434"
        mock_settings.llm_api_key = None
        mock_settings.llm_timeout_seconds = 30
        mock_get_settings.return_value = mock_settings
        
        service = LLMService(test_db)
        request = LLMExplanationRequest(
            skill_slug="test-skill",
            plugin_slug="test-plugin",
            question="How does this work?",
        )
        
        with patch('app.services.llm_service.create_llm_adapter') as mock_create:
            mock_adapter = AsyncMock()
            mock_adapter.generate_explanation = AsyncMock(return_value=LLMExplanationResponse(
                explanation="Test explanation from Ollama",
                provider="ollama",
                model="llama3",
                advisory=True,
            ))
            mock_create.return_value = mock_adapter
            
            response = await service.generate_explanation(request)
            
            # Check log was created
            logs = await service.get_explanation_logs(skill_slug="test-skill")
            assert len(logs) == 1
            assert logs[0].skill_slug == "test-skill"
            assert logs[0].plugin_slug == "test-plugin"
            assert logs[0].provider == "ollama"
            assert logs[0].model == "llama3"


@pytest.mark.asyncio
async def test_llm_service_get_explanation_logs(test_db: AsyncSession):
    """Test getting explanation logs."""
    with patch('app.services.llm_service.get_settings') as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.llm_provider = "ollama"
        mock_settings.llm_model = "llama3"
        mock_settings.llm_base_url = "http://localhost:11434"
        mock_settings.llm_api_key = None
        mock_settings.llm_timeout_seconds = 30
        mock_get_settings.return_value = mock_settings
        
        service = LLMService(test_db)
        
        # Add some logs
        log1 = LLMExplanationLog(
            skill_slug="skill1",
            plugin_slug="plugin1",
            provider="ollama",
            model="llama3",
            question="Question 1",
            response_preview="Response 1",
        )
        log2 = LLMExplanationLog(
            skill_slug="skill2",
            plugin_slug="plugin1",
            provider="openai-compatible",
            model="gpt-4o-mini",
            question="Question 2",
            response_preview="Response 2",
        )
        test_db.add_all([log1, log2])
        await test_db.commit()
        
        logs = await service.get_explanation_logs(limit=10)
        assert len(logs) == 2
        
        # Filter by skill
        logs = await service.get_explanation_logs(skill_slug="skill1", limit=10)
        assert len(logs) == 1
        assert logs[0].skill_slug == "skill1"
