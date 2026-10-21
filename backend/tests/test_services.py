# Service layer tests
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.plugin_query import PluginQueryService
from app.services.plugin_sync import PluginSyncService
from app.models.plugin import Plugin, Skill, Command, Connector, PluginType, StabilityLevel


@pytest.mark.asyncio
async def test_plugin_query_service_list_plugins(test_db: AsyncSession):
    plugin1 = Plugin(slug="p1", name="Plugin One", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    plugin2 = Plugin(slug="p2", name="Plugin Two", plugin_type=PluginType.COMMUNITY, repo_path="p2")
    test_db.add_all([plugin1, plugin2])
    await test_db.flush()

    service = PluginQueryService(test_db)
    result = await service.list_plugins(page=1, page_size=10)

    assert result["total"] == 2
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_plugin_query_service_search(test_db: AsyncSession):
    plugin1 = Plugin(slug="bio-research", name="Bio Research", description="Bio tools", plugin_type=PluginType.OFFICIAL, repo_path="bio")
    plugin2 = Plugin(slug="sales", name="Sales", description="Sales tools", plugin_type=PluginType.OFFICIAL, repo_path="sales")
    test_db.add_all([plugin1, plugin2])
    await test_db.flush()

    service = PluginQueryService(test_db)
    result = await service.list_plugins(search="bio")

    assert result["total"] == 1
    assert result["items"][0].slug == "bio-research"


@pytest.mark.asyncio
async def test_plugin_query_service_get_plugin(test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(plugin_id=plugin.id, slug="s1", name="Skill 1", stability=StabilityLevel.STABLE)
    test_db.add(skill)
    await test_db.flush()

    service = PluginQueryService(test_db)
    result = await service.get_plugin("test")

    assert result is not None
    assert result.slug == "test"
    assert len(result.skills) == 1


@pytest.mark.asyncio
async def test_plugin_query_service_get_plugin_not_found(test_db: AsyncSession):
    service = PluginQueryService(test_db)
    result = await service.get_plugin("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_plugin_query_service_list_skills_with_stability_filter(test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    for stab in StabilityLevel:
        skill = Skill(plugin_id=plugin.id, slug=f"skill-{stab.value}", name=f"Skill {stab.value}", stability=stab)
        test_db.add(skill)
    await test_db.flush()

    service = PluginQueryService(test_db)
    result = await service.list_skills(plugin_slug="test", stability=StabilityLevel.STABLE)

    assert result["total"] == 1
    assert result["items"][0].stability == StabilityLevel.STABLE


@pytest.mark.asyncio
async def test_plugin_query_service_get_stability_counts(test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    for stab in [StabilityLevel.STABLE, StabilityLevel.STABLE, StabilityLevel.EXPERIMENTAL]:
        skill = Skill(plugin_id=plugin.id, slug=f"skill-{stab.value}", name=f"Skill {stab.value}", stability=stab)
        test_db.add(skill)
    await test_db.flush()

    service = PluginQueryService(test_db)
    counts = await service.get_stability_counts(plugin_slug="test")

    assert counts["stable"] == 2
    assert counts["experimental"] == 1
    assert "deprecated" not in counts


@pytest.mark.asyncio
async def test_plugin_query_service_get_plugin_stats(test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(plugin_id=plugin.id, slug="s1", name="S1", stability=StabilityLevel.STABLE)
    cmd = Command(plugin_id=plugin.id, slug="c1", name="C1")
    conn = Connector(plugin_id=plugin.id, name="conn1", type="mcp")
    test_db.add_all([skill, cmd, conn])
    await test_db.flush()

    service = PluginQueryService(test_db)
    stats = await service.get_plugin_stats()

    assert stats["total_plugins"] == 1
    assert stats["total_skills"] == 1
    assert stats["total_commands"] == 1
    assert stats["total_connectors"] == 1


# Sync service tests (mocked HTTP)
@pytest.mark.asyncio
async def test_plugin_sync_service_parse_frontmatter():
    service = PluginSyncService(MagicMock())
    
    # With frontmatter
    md = "---\nname: Test Skill\nstability: stable\n---\n\n# Content"
    frontmatter, content = service._parse_markdown_frontmatter(md)
    assert frontmatter["name"] == "Test Skill"
    assert frontmatter["stability"] == "stable"
    assert content == "# Content"

    # Without frontmatter
    md2 = "# Just Content"
    frontmatter2, content2 = service._parse_markdown_frontmatter(md2)
    assert frontmatter2 == {}
    assert content2 == "# Just Content"

    # Malformed frontmatter
    md3 = "---\ninvalid: [\n---\nContent"
    frontmatter3, content3 = service._parse_markdown_frontmatter(md3)
    assert frontmatter3 == {}
    assert content3 == md3


@pytest.mark.asyncio
async def test_plugin_sync_service_fetch_plugins_mock():
    mock_db = AsyncMock()
    service = PluginSyncService(mock_db)
    
    # Mock the HTTP client
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"name": "bio-research", "type": "dir"},
            {"name": "sales", "type": "dir"},
            {"name": ".github", "type": "dir"},  # Should be filtered
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock _fetch_file for plugin.json
        with patch.object(service, "_fetch_file") as mock_fetch:
            mock_fetch.side_effect = [
                {"name": "Bio Research", "description": "Bio tools"},  # bio-research
                {"name": "Sales", "description": "Sales tools"},       # sales
            ]
            
            plugins = await service._fetch_plugins()
            
            assert len(plugins) == 2
            assert plugins[0]["slug"] == "bio-research"
            assert plugins[1]["slug"] == "sales"


@pytest.mark.asyncio
async def test_plugin_sync_service_upsert_plugin(test_db: AsyncSession):
    service = PluginSyncService(test_db)
    
    plugin_data = {
        "slug": "test",
        "repo_path": "test",
        "manifest": {"name": "Test Plugin", "description": "Desc", "license": "MIT"},
    }
    
    plugin = await service._upsert_plugin(plugin_data)
    
    assert plugin.slug == "test"
    assert plugin.name == "Test Plugin"
    assert plugin.repo_path == "test"
    assert plugin.license == "MIT"
    
    # Test update
    plugin_data["manifest"]["name"] = "Updated Name"
    plugin2 = await service._upsert_plugin(plugin_data)
    assert plugin2.id == plugin.id
    assert plugin2.name == "Updated Name"