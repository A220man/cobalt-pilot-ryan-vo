# Plugin API tests
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugin import Plugin, Skill, Command, Connector, PluginType, StabilityLevel
from app.services.plugin_query import PluginQueryService


@pytest.mark.asyncio
async def test_list_plugins_empty(client_with_auth: AsyncClient):
    response = await client_with_auth.get("/api/plugins")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["total_pages"] == 0


@pytest.mark.asyncio
async def test_list_plugins_with_data(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(
        slug="bio-research",
        name="Bio Research",
        description="Bioinformatics and research tools",
        plugin_type=PluginType.OFFICIAL,
        repo_path="bio-research",
        license="Apache-2.0",
    )
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(
        slug="analyze-sequence",
        name="Analyze Sequence",
        description="Analyze DNA sequences",
        stability=StabilityLevel.STABLE,
        markdown_content="# Analyze Sequence\n\nContent",
        frontmatter={"name": "Analyze Sequence", "stability": "stable"},
        file_path="bio-research/skills/analyze-sequence/SKILL.md",
        plugin_id=plugin.id,
    )
    test_db.add(skill)
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "bio-research"
    assert data["items"][0]["skills_count"] == 1


@pytest.mark.asyncio
async def test_list_plugins_search(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin1 = Plugin(slug="bio-research", name="Bio Research", plugin_type=PluginType.OFFICIAL, repo_path="bio-research")
    plugin2 = Plugin(slug="data-analysis", name="Data Analysis", plugin_type=PluginType.COMMUNITY, repo_path="data-analysis")
    test_db.add_all([plugin1, plugin2])
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins?search=bio")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "bio-research"


@pytest.mark.asyncio
async def test_list_plugins_filter_by_type(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin1 = Plugin(slug="official-plugin", name="Official", plugin_type=PluginType.OFFICIAL, repo_path="official")
    plugin2 = Plugin(slug="community-plugin", name="Community", plugin_type=PluginType.COMMUNITY, repo_path="community")
    test_db.add_all([plugin1, plugin2])
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins?plugin_type=official")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["plugin_type"] == "official"


@pytest.mark.asyncio
async def test_list_plugins_pagination(client_with_auth: AsyncClient, test_db: AsyncSession):
    for i in range(5):
        plugin = Plugin(slug=f"plugin-{i}", name=f"Plugin {i}", plugin_type=PluginType.OFFICIAL, repo_path=f"plugin-{i}")
        test_db.add(plugin)
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_plugin_detail(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(
        slug="detail-plugin",
        name="Detail Plugin",
        description="A plugin for detail testing",
        plugin_type=PluginType.OFFICIAL,
        repo_path="detail-plugin",
        license="MIT",
    )
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(
        slug="test-skill",
        name="Test Skill",
        description="A test skill",
        stability=StabilityLevel.EXPERIMENTAL,
        markdown_content="# Test Skill\n\nContent",
        frontmatter={"name": "Test Skill", "stability": "experimental"},
        file_path="detail-plugin/skills/test-skill/SKILL.md",
        plugin_id=plugin.id,
    )
    test_db.add(skill)
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins/detail-plugin")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "detail-plugin"
    assert data["name"] == "Detail Plugin"
    assert len(data["skills"]) == 1
    assert data["skills"][0]["stability"] == "experimental"


@pytest.mark.asyncio
async def test_get_plugin_not_found(client_with_auth: AsyncClient):
    response = await client_with_auth.get("/api/plugins/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_plugin_stats(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    skill1 = Skill(slug="s1", name="S1", stability=StabilityLevel.STABLE, markdown_content="# S1", frontmatter={}, file_path="p1/skills/s1/SKILL.md", plugin_id=plugin.id)
    skill2 = Skill(slug="s2", name="S2", stability=StabilityLevel.EXPERIMENTAL, markdown_content="# S2", frontmatter={}, file_path="p1/skills/s2/SKILL.md", plugin_id=plugin.id)
    skill3 = Skill(slug="s3", name="S3", stability=StabilityLevel.DEPRECATED, markdown_content="# S3", frontmatter={}, file_path="p1/skills/s3/SKILL.md", plugin_id=plugin.id)
    test_db.add_all([skill1, skill2, skill3])
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_plugins"] == 1
    assert data["total_skills"] == 3
    assert data["stability_distribution"]["stable"] == 1
    assert data["stability_distribution"]["experimental"] == 1
    assert data["stability_distribution"]["deprecated"] == 1


@pytest.mark.asyncio
async def test_list_plugin_skills(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    skill1 = Skill(slug="skill1", name="Skill 1", stability=StabilityLevel.STABLE, markdown_content="# Skill 1", frontmatter={}, file_path="test/skills/skill1/SKILL.md", plugin_id=plugin.id)
    skill2 = Skill(slug="skill2", name="Skill 2", stability=StabilityLevel.EXPERIMENTAL, markdown_content="# Skill 2", frontmatter={}, file_path="test/skills/skill2/SKILL.md", plugin_id=plugin.id)
    test_db.add_all([skill1, skill2])
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins/test/skills")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_plugin_skills_filter_stability(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    skill1 = Skill(slug="skill1", name="Skill 1", stability=StabilityLevel.STABLE, markdown_content="# Skill 1", frontmatter={}, file_path="test/skills/skill1/SKILL.md", plugin_id=plugin.id)
    skill2 = Skill(slug="skill2", name="Skill 2", stability=StabilityLevel.EXPERIMENTAL, markdown_content="# Skill 2", frontmatter={}, file_path="test/skills/skill2/SKILL.md", plugin_id=plugin.id)
    test_db.add_all([skill1, skill2])
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins/test/skills?stability=stable")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["stability"] == "stable"


@pytest.mark.asyncio
async def test_get_skill_detail(client_with_auth: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(
        slug="test-skill",
        name="Test Skill",
        description="A test skill",
        stability=StabilityLevel.STABLE,
        markdown_content="# Test Skill\n\nContent here.",
        frontmatter={"name": "Test Skill", "stability": "stable"},
        file_path="test/skills/test-skill/SKILL.md",
        plugin_id=plugin.id,
    )
    test_db.add(skill)
    await test_db.commit()

    response = await client_with_auth.get("/api/plugins/test/skills/test-skill")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-skill"
    assert data["name"] == "Test Skill"
    assert data["stability"] == "stable"
    assert data["markdown_content"] == "# Test Skill\n\nContent here."
    assert data["frontmatter"]["stability"] == "stable"


# Role-based access tests
@pytest.mark.asyncio
async def test_role_based_access_viewer(client_with_auth: AsyncClient, client_with_operator_auth: AsyncClient, client_with_admin_auth: AsyncClient, test_db: AsyncSession, monkeypatch):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.commit()

    for client in [client_with_auth, client_with_operator_auth, client_with_admin_auth]:
        response = await client.get("/api/plugins")
        assert response.status_code == 200
        response = await client.get("/api/plugins/test")
        assert response.status_code == 200
        response = await client.get("/api/plugins/test/skills")
        assert response.status_code == 200
        response = await client.get("/api/plugins/stats")
        assert response.status_code == 200

    # Mock the sync service to avoid external API calls
    from app.services.plugin_sync import PluginSyncService
    from app.models.plugin import SyncLog
    from datetime import datetime, timezone
    
    async def mock_sync_all(self):
        log = SyncLog(
            status="success",
            plugins_synced=1,
            skills_synced=0,
            commands_synced=0,
            connectors_synced=0,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()
        return log
    
    monkeypatch.setattr(PluginSyncService, "sync_all", mock_sync_all)

    # Operator can sync
    response = await client_with_operator_auth.post("/api/plugins/sync")
    assert response.status_code != 403
    assert response.status_code == 202

    # Viewer cannot sync
    response = await client_with_auth.post("/api/plugins/sync")
    assert response.status_code == 403

    # Admin can sync (not 403)
    response = await client_with_admin_auth.post("/api/plugins/sync")
    assert response.status_code != 403
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    endpoints = [
        "/api/plugins",
        "/api/plugins/stats",
        "/api/plugins/test",
        "/api/plugins/test/skills",
        "/api/plugins/sync",
    ]
    for endpoint in endpoints:
        response = await client.get(endpoint) if endpoint != "/api/plugins/sync" else await client.post(endpoint)
        assert response.status_code == 401, f"Endpoint {endpoint} should require auth"
