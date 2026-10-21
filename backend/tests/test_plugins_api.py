# Plugin API tests
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugin import Plugin, Skill, Command, Connector, PluginType, StabilityLevel
from app.services.plugin_query import PluginQueryService


@pytest.mark.asyncio
async def test_list_plugins_empty(client: AsyncClient):
    response = await client.get("/api/plugins")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["total_pages"] == 0


@pytest.mark.asyncio
async def test_list_plugins_with_data(client: AsyncClient, test_db: AsyncSession):
    # Create test plugin
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
        plugin_id=plugin.id,
        slug="nextflow-development",
        name="Nextflow Development",
        description="Nextflow pipeline development",
        stability=StabilityLevel.STABLE,
    )
    test_db.add(skill)
    await test_db.flush()

    response = await client.get("/api/plugins")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["slug"] == "bio-research"
    assert data["items"][0]["skills_count"] == 1


@pytest.mark.asyncio
async def test_list_plugins_search(client: AsyncClient, test_db: AsyncSession):
    plugin1 = Plugin(slug="bio-research", name="Bio Research", plugin_type=PluginType.OFFICIAL, repo_path="bio-research")
    plugin2 = Plugin(slug="sales", name="Sales", plugin_type=PluginType.OFFICIAL, repo_path="sales")
    test_db.add_all([plugin1, plugin2])
    await test_db.flush()

    response = await client.get("/api/plugins?search=bio")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "bio-research"


@pytest.mark.asyncio
async def test_list_plugins_filter_by_type(client: AsyncClient, test_db: AsyncSession):
    plugin1 = Plugin(slug="official-plugin", name="Official", plugin_type=PluginType.OFFICIAL, repo_path="official")
    plugin2 = Plugin(slug="community-plugin", name="Community", plugin_type=PluginType.COMMUNITY, repo_path="community")
    test_db.add_all([plugin1, plugin2])
    await test_db.flush()

    response = await client.get("/api/plugins?plugin_type=official")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["plugin_type"] == "official"


@pytest.mark.asyncio
async def test_list_plugins_pagination(client: AsyncClient, test_db: AsyncSession):
    for i in range(5):
        plugin = Plugin(slug=f"plugin-{i}", name=f"Plugin {i}", plugin_type=PluginType.OFFICIAL, repo_path=f"plugin-{i}")
        test_db.add(plugin)
    await test_db.flush()

    response = await client.get("/api/plugins?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_get_plugin_detail(client: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(
        slug="test-plugin",
        name="Test Plugin",
        description="Description",
        plugin_type=PluginType.OFFICIAL,
        repo_path="test-plugin",
    )
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(
        plugin_id=plugin.id,
        slug="test-skill",
        name="Test Skill",
        stability=StabilityLevel.EXPERIMENTAL,
    )
    cmd = Command(plugin_id=plugin.id, slug="test-cmd", name="Test Command")
    conn = Connector(plugin_id=plugin.id, name="test-connector", type="mcp")
    test_db.add_all([skill, cmd, conn])
    await test_db.flush()

    response = await client.get("/api/plugins/test-plugin")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "test-plugin"
    assert data["name"] == "Test Plugin"
    assert len(data["skills"]) == 1
    assert len(data["commands"]) == 1
    assert len(data["connectors"]) == 1
    assert data["skills"][0]["stability"] == "experimental"


@pytest.mark.asyncio
async def test_get_plugin_not_found(client: AsyncClient):
    response = await client.get("/api/plugins/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_plugin_stats(client: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    for stability in [StabilityLevel.STABLE, StabilityLevel.EXPERIMENTAL, StabilityLevel.DEPRECATED]:
        skill = Skill(plugin_id=plugin.id, slug=f"skill-{stability.value}", name=f"Skill {stability.value}", stability=stability)
        test_db.add(skill)
    await test_db.flush()

    response = await client.get("/api/plugins/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_plugins"] == 1
    assert data["total_skills"] == 3
    assert data["stability_distribution"]["stable"] == 1
    assert data["stability_distribution"]["experimental"] == 1
    assert data["stability_distribution"]["deprecated"] == 1


@pytest.mark.asyncio
async def test_list_plugin_skills(client: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    for stab in [StabilityLevel.STABLE, StabilityLevel.EXPERIMENTAL]:
        skill = Skill(plugin_id=plugin.id, slug=f"skill-{stab.value}", name=f"Skill {stab.value}", stability=stab)
        test_db.add(skill)
    await test_db.flush()

    response = await client.get("/api/plugins/test/skills")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_plugin_skills_filter_stability(client: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    for stab in [StabilityLevel.STABLE, StabilityLevel.EXPERIMENTAL, StabilityLevel.DEPRECATED]:
        skill = Skill(plugin_id=plugin.id, slug=f"skill-{stab.value}", name=f"Skill {stab.value}", stability=stab)
        test_db.add(skill)
    await test_db.flush()

    response = await client.get("/api/plugins/test/skills?stability=stable")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["stability"] == "stable"


@pytest.mark.asyncio
async def test_get_skill_detail(client: AsyncClient, test_db: AsyncSession):
    plugin = Plugin(slug="test", name="Test", plugin_type=PluginType.OFFICIAL, repo_path="test")
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(
        plugin_id=plugin.id,
        slug="my-skill",
        name="My Skill",
        description="Skill description",
        stability=StabilityLevel.STABLE,
        markdown_content="# My Skill\n\nContent",
        frontmatter={"name": "My Skill", "stability": "stable"},
    )
    test_db.add(skill)
    await test_db.flush()

    response = await client.get("/api/plugins/test/skills/my-skill")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "my-skill"
    assert data["stability"] == "stable"
    assert data["markdown_content"] == "# My Skill\n\nContent"
    assert data["frontmatter"]["stability"] == "stable"