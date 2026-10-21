# Model tests
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.plugin import Plugin, Skill, Command, Connector, SyncLog, PluginType, StabilityLevel


@pytest.mark.asyncio
async def test_plugin_model(test_db: AsyncSession):
    plugin = Plugin(
        slug="test-plugin",
        name="Test Plugin",
        description="A test plugin",
        plugin_type=PluginType.OFFICIAL,
        repo_path="test-plugin",
        license="MIT",
    )
    test_db.add(plugin)
    await test_db.flush()

    assert plugin.id is not None
    assert plugin.slug == "test-plugin"
    assert plugin.plugin_type == PluginType.OFFICIAL
    assert plugin.created_at is not None
    assert plugin.updated_at is not None


@pytest.mark.asyncio
async def test_skill_model_with_stability(test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    for stability in StabilityLevel:
        skill = Skill(
            plugin_id=plugin.id,
            slug=f"skill-{stability.value}",
            name=f"Skill {stability.value}",
            stability=stability,
        )
        test_db.add(skill)
    await test_db.flush()

    # Query and verify
    result = await test_db.execute(select(Skill).where(Skill.plugin_id == plugin.id))
    skills = result.scalars().all()
    assert len(skills) == 3
    stabilities = {s.stability for s in skills}
    assert stabilities == {StabilityLevel.STABLE, StabilityLevel.EXPERIMENTAL, StabilityLevel.DEPRECATED}


@pytest.mark.asyncio
async def test_command_model(test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    cmd = Command(
        plugin_id=plugin.id,
        slug="my-command",
        name="My Command",
        description="Command description",
        markdown_content="# Command\n\nUsage",
    )
    test_db.add(cmd)
    await test_db.flush()

    assert cmd.id is not None
    assert cmd.slug == "my-command"
    assert cmd.markdown_content == "# Command\n\nUsage"


@pytest.mark.asyncio
async def test_connector_model(test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    conn = Connector(
        plugin_id=plugin.id,
        name="github",
        type="mcp",
        config={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
        description="GitHub MCP server",
    )
    test_db.add(conn)
    await test_db.flush()

    assert conn.id is not None
    assert conn.config["command"] == "npx"
    assert conn.type == "mcp"


@pytest.mark.asyncio
async def test_sync_log_model(test_db: AsyncSession):
    log = SyncLog(
        status="success",
        plugins_synced=11,
        skills_synced=100,
        commands_synced=50,
        connectors_synced=30,
    )
    test_db.add(log)
    await test_db.flush()

    assert log.id is not None
    assert log.status == "success"
    assert log.plugins_synced == 11
    assert log.started_at is not None


@pytest.mark.asyncio
async def test_cascade_delete_skills(test_db: AsyncSession):
    plugin = Plugin(slug="p1", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    test_db.add(plugin)
    await test_db.flush()

    skill = Skill(plugin_id=plugin.id, slug="s1", name="S1", stability=StabilityLevel.STABLE)
    test_db.add(skill)
    await test_db.flush()

    skill_id = skill.id
    await test_db.delete(plugin)
    await test_db.flush()

    result = await test_db.execute(select(Skill).where(Skill.id == skill_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_unique_plugin_slug(test_db: AsyncSession):
    plugin1 = Plugin(slug="duplicate", name="P1", plugin_type=PluginType.OFFICIAL, repo_path="p1")
    plugin2 = Plugin(slug="duplicate", name="P2", plugin_type=PluginType.OFFICIAL, repo_path="p2")
    test_db.add_all([plugin1, plugin2])

    with pytest.raises(Exception):  # IntegrityError
        await test_db.flush()