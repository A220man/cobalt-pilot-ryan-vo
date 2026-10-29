# Plugin sync service - fetches and parses plugin data from reference repo
import httpx
import yaml
import markdown
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.plugin import (
    Plugin,
    Skill,
    Command,
    Connector,
    SyncLog,
    PluginType,
    StabilityLevel,
)


settings = get_settings()


class PluginSyncService:
    """Service to sync plugin data from the reference GitHub repository."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_url = f"https://api.github.com/repos/anthropics/knowledge-work-plugins/contents"
        self.raw_base = f"https://raw.githubusercontent.com/anthropics/knowledge-work-plugins/{settings.reference_repo_branch}"

    async def sync_all(self) -> SyncLog:
        """Sync all plugins from reference repo."""
        log = SyncLog(
            status="started",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        await self.db.flush()

        try:
            plugins_data = await self._fetch_plugins()
            plugins_synced = 0
            skills_synced = 0
            commands_synced = 0
            connectors_synced = 0

            for plugin_data in plugins_data:
                plugin = await self._upsert_plugin(plugin_data)
                plugins_synced += 1

                # Sync skills
                skills = await self._fetch_skills(plugin.repo_path)
                for skill_data in skills:
                    await self._upsert_skill(plugin.id, skill_data)
                    skills_synced += 1

                # Sync commands
                commands = await self._fetch_commands(plugin.repo_path)
                for cmd_data in commands:
                    await self._upsert_command(plugin.id, cmd_data)
                    commands_synced += 1

                # Sync connectors
                connectors = await self._fetch_connectors(plugin.repo_path)
                for conn_data in connectors:
                    await self._upsert_connector(plugin.id, conn_data)
                    connectors_synced += 1

            log.status = "success"
            log.plugins_synced = plugins_synced
            log.skills_synced = skills_synced
            log.commands_synced = commands_synced
            log.connectors_synced = connectors_synced
            log.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.now(timezone.utc)
            raise

        finally:
            await self.db.flush()

        return log

    async def _fetch_plugins(self) -> List[Dict[str, Any]]:
        """Fetch plugin directories from reference repo."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(self.base_url)
            resp.raise_for_status()
            contents = resp.json()

        plugins = []
        for item in contents:
            if item["type"] == "dir" and not item["name"].startswith("."):
                # Check if it's a plugin directory (has .claude-plugin/plugin.json)
                plugin_json = await self._fetch_file(f"{item['name']}/.claude-plugin/plugin.json")
                if plugin_json:
                    plugins.append({
                        "slug": item["name"],
                        "repo_path": item["name"],
                        "manifest": plugin_json,
                    })

        return plugins

    async def _fetch_file(self, path: str) -> Optional[Dict[str, Any]]:
        """Fetch a file from the reference repo."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.raw_base}/{path}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            if path.endswith(".json"):
                return resp.json()
            elif path.endswith(".yaml") or path.endswith(".yml"):
                return yaml.safe_load(resp.text)
            return resp.text

    async def _upsert_plugin(self, plugin_data: Dict[str, Any]) -> Plugin:
        """Insert or update a plugin."""
        manifest = plugin_data["manifest"]
        slug = plugin_data["slug"]

        stmt = select(Plugin).where(Plugin.slug == slug)
        result = await self.db.execute(stmt)
        plugin = result.scalar_one_or_none()

        if not plugin:
            plugin = Plugin(slug=slug)
            self.db.add(plugin)

        plugin.name = manifest.get("name", slug.replace("-", " ").title())
        plugin.description = manifest.get("description")
        plugin.repo_path = plugin_data["repo_path"]
        plugin.license = manifest.get("license", "Apache-2.0")
        plugin.updated_at = datetime.now(timezone.utc)

        # Fetch README
        readme = await self._fetch_file(f"{plugin_data['repo_path']}/README.md")
        if readme:
            plugin.readme_content = readme

        await self.db.flush()
        return plugin

    async def _fetch_skills(self, repo_path: str) -> List[Dict[str, Any]]:
        """Fetch skills for a plugin."""
        skills_dir = f"{repo_path}/skills"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/{skills_dir}")
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            contents = resp.json()

        skills = []
        for item in contents:
            if item["type"] == "dir" and not item["name"].startswith("."):
                skill_md = await self._fetch_file(f"{skills_dir}/{item['name']}/SKILL.md")
                if skill_md:
                    frontmatter, content = self._parse_markdown_frontmatter(skill_md)
                    skills.append({
                        "slug": item["name"],
                        "name": frontmatter.get("name", item["name"].replace("-", " ").title()),
                        "description": frontmatter.get("description"),
                        "stability": frontmatter.get("stability", "experimental"),
                        "markdown_content": content,
                        "frontmatter": frontmatter,
                        "file_path": f"{skills_dir}/{item['name']}/SKILL.md",
                    })

        return skills

    async def _fetch_commands(self, repo_path: str) -> List[Dict[str, Any]]:
        """Fetch commands for a plugin."""
        commands_dir = f"{repo_path}/commands"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/{commands_dir}")
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            contents = resp.json()

        commands = []
        for item in contents:
            if item["type"] == "file" and item["name"].endswith(".md"):
                slug = item["name"][:-3]
                cmd_md = await self._fetch_file(f"{commands_dir}/{item['name']}")
                if cmd_md:
                    frontmatter, content = self._parse_markdown_frontmatter(cmd_md)
                    commands.append({
                        "slug": slug,
                        "name": frontmatter.get("name", slug.replace("-", " ").title()),
                        "description": frontmatter.get("description"),
                        "markdown_content": content,
                        "file_path": f"{commands_dir}/{item['name']}",
                    })

        return commands

    async def _fetch_connectors(self, repo_path: str) -> List[Dict[str, Any]]:
        """Fetch connectors for a plugin (from .mcp.json)."""
        mcp_json = await self._fetch_file(f"{repo_path}/.mcp.json")
        if not mcp_json:
            return []

        connectors = []
        for name, config in mcp_json.get("mcpServers", {}).items():
            connectors.append({
                "slug": name.lower().replace(" ", "-"),
                "name": name,
                "type": "mcp",
                "config": config,
                "description": config.get("description", f"MCP server: {name}"),
            })

        return connectors

    async def _upsert_skill(self, plugin_id: int, skill_data: Dict[str, Any]) -> Skill:
        """Insert or update a skill."""
        stmt = select(Skill).where(Skill.plugin_id == plugin_id, Skill.slug == skill_data["slug"])
        result = await self.db.execute(stmt)
        skill = result.scalar_one_or_none()

        if not skill:
            skill = Skill(plugin_id=plugin_id, slug=skill_data["slug"])
            self.db.add(skill)

        skill.name = skill_data["name"]
        skill.description = skill_data["description"]
        skill.stability = StabilityLevel(skill_data["stability"])
        skill.markdown_content = skill_data["markdown_content"]
        skill.frontmatter = skill_data["frontmatter"]
        skill.file_path = skill_data["file_path"]
        skill.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return skill

    async def _upsert_command(self, plugin_id: int, cmd_data: Dict[str, Any]) -> Command:
        """Insert or update a command."""
        stmt = select(Command).where(Command.plugin_id == plugin_id, Command.slug == cmd_data["slug"])
        result = await self.db.execute(stmt)
        cmd = result.scalar_one_or_none()

        if not cmd:
            cmd = Command(plugin_id=plugin_id, slug=cmd_data["slug"])
            self.db.add(cmd)

        cmd.name = cmd_data["name"]
        cmd.description = cmd_data["description"]
        cmd.markdown_content = cmd_data["markdown_content"]
        cmd.file_path = cmd_data["file_path"]
        cmd.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return cmd

    async def _upsert_connector(self, plugin_id: int, conn_data: Dict[str, Any]) -> Connector:
        """Insert or update a connector."""
        stmt = select(Connector).where(Connector.plugin_id == plugin_id, Connector.slug == conn_data["slug"])
        result = await self.db.execute(stmt)
        conn = result.scalar_one_or_none()

        if not conn:
            conn = Connector(plugin_id=plugin_id, slug=conn_data["slug"])
            self.db.add(conn)

        conn.name = conn_data["name"]
        conn.type = conn_data["type"]
        conn.config = conn_data["config"]
        conn.description = conn_data["description"]
        conn.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return conn

    def _parse_markdown_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return {}, content

        try:
            parts = content.split("---", 2)
            if len(parts) < 3:
                return {}, content
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return frontmatter, body
        except Exception:
            return {}, content