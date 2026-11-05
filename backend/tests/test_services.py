# Service layer tests
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.plugin import Plugin, Skill, Command, Connector, PluginType, StabilityLevel
from app.services.plugin_query import PluginQueryService
from app.services.plugin_sync import PluginSyncService


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
    plugin2 = Plugin(slug="sales-tools", name="Sales Tools", description="Sales CRM", plugin_type=PluginType.COMMUNITY, repo_path="sales")
    test_db.add_all([plugin1, plugin2])
    await test_db.flush()

    service = PluginQueryService(test_db)
    result = await service.list_plugins(search="bio", page=1, page_size=10)

    assert result["total"] == 1
    assert result["items"][0].slug == "bio-research"


@pytest.mark.asyncio
async def test_plugin_query_service_get_plugin(test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    skill = Skill(plugin=plugin, slug="skill1", name="Skill 1", description="Desc")
    test_db.add_all([plugin, skill])
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
    skill1 = Skill(plugin=plugin, slug="skill1", name="Skill 1", stability=StabilityLevel.STABLE)
    skill2 = Skill(plugin=plugin, slug="skill2", name="Skill 2", stability=StabilityLevel.EXPERIMENTAL)
    skill3 = Skill(plugin=plugin, slug="skill3", name="Skill 3", stability=StabilityLevel.DEPRECATED)
    test_db.add_all([plugin, skill1, skill2, skill3])
    await test_db.flush()

    service = PluginQueryService(test_db)
    result = await service.list_skills("test", stability=StabilityLevel.STABLE)

    assert result["total"] == 1
    assert result["items"][0].stability == StabilityLevel.STABLE


@pytest.mark.asyncio
async def test_plugin_query_service_get_stability_counts(test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    skill1 = Skill(plugin=plugin, slug="skill1", name="Skill 1", stability=StabilityLevel.STABLE)
    skill2 = Skill(plugin=plugin, slug="skill2", name="Skill 2", stability=StabilityLevel.STABLE)
    skill3 = Skill(plugin=plugin, slug="skill3", name="Skill 3", stability=StabilityLevel.EXPERIMENTAL)
    test_db.add_all([plugin, skill1, skill2, skill3])
    await test_db.flush()

    service = PluginQueryService(test_db)
    counts = await service.get_stability_counts("test")

    assert counts["stable"] == 2
    assert counts["experimental"] == 1
    assert "deprecated" not in counts


@pytest.mark.asyncio
async def test_plugin_query_service_get_plugin_stats(test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    skill = Skill(plugin=plugin, slug="s1", name="S1")
    cmd = Command(plugin=plugin, slug="c1", name="C1")
    conn = Connector(plugin=plugin, slug="conn1", name="Conn1")
    test_db.add_all([plugin, skill, cmd, conn])
    await test_db.flush()

    service = PluginQueryService(test_db)
    stats = await service.get_plugin_stats()

    assert stats["total_skills"] == 1
    assert stats["total_commands"] == 1
    assert stats["total_connectors"] == 1


# Sync service tests (mocked HTTP)
@pytest.mark.asyncio
async def test_plugin_sync_service_parse_frontmatter():
    service = PluginSyncService(MagicMock())
    
    md1 = """---
name: Test Skill
description: A test skill
stability: stable
---
# Content"""
    frontmatter, content = service._parse_markdown_frontmatter(md1)
    assert frontmatter["name"] == "Test Skill"
    assert frontmatter["stability"] == "stable"
    assert content == "# Content"

    md2 = "# No frontmatter"
    frontmatter2, content2 = service._parse_markdown_frontmatter(md2)
    assert frontmatter2 == {}
    assert content2 == md2

    md3 = """---
name: Test
---
# Content
---
not frontmatter"""
    frontmatter3, content3 = service._parse_markdown_frontmatter(md3)
    assert frontmatter3["name"] == "Test"
    assert content3 == """# Content
---
not frontmatter"""


@pytest.mark.asyncio
async def test_plugin_sync_service_upsert_plugin(test_db: AsyncSession):
    service = PluginSyncService(test_db)
    
    plugin_data = {
        "manifest": {"name": "Test Plugin", "version": "1.0.0"},
        "slug": "test-plugin",
        "name": "Test Plugin",
        "plugin_type": "official",
        "repo_path": "test-plugin",
        "description": "A test plugin",
    }
    
    plugin = await service._upsert_plugin(plugin_data)
    assert plugin.slug == "test-plugin"
    assert plugin.name == "Test Plugin"
    
    # Update
    plugin_data["manifest"]["name"] = "Updated Name"
    plugin2 = await service._upsert_plugin(plugin_data)
    assert plugin2.id == plugin.id
    assert plugin2.name == "Updated Name"
