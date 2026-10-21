# Plugin query service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from math import ceil

from app.models.plugin import Plugin, Skill, Command, Connector, PluginType, StabilityLevel


class PluginQueryService:
    """Service for querying plugin data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plugins(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        plugin_type: Optional[PluginType] = None,
    ) -> Dict[str, Any]:
        """List plugins with pagination and filtering."""
        stmt = select(Plugin).options(
            selectinload(Plugin.skills),
            selectinload(Plugin.commands),
            selectinload(Plugin.connectors),
        )

        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Plugin.name.ilike(search_term),
                    Plugin.slug.ilike(search_term),
                    Plugin.description.ilike(search_term),
                )
            )

        if plugin_type:
            stmt = stmt.where(Plugin.plugin_type == plugin_type)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Paginate
        stmt = stmt.order_by(Plugin.name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        plugins = result.scalars().all()

        return {
            "items": plugins,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if page_size > 0 else 0,
        }

    async def get_plugin(self, slug: str) -> Optional[Plugin]:
        """Get a plugin by slug with all relations."""
        stmt = select(Plugin).options(
            selectinload(Plugin.skills),
            selectinload(Plugin.commands),
            selectinload(Plugin.connectors),
        ).where(Plugin.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_skills(
        self,
        plugin_slug: Optional[str] = None,
        stability: Optional[StabilityLevel] = None,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List skills with filtering."""
        stmt = select(Skill).join(Plugin).options(selectinload(Skill.plugin))

        if plugin_slug:
            stmt = stmt.where(Plugin.slug == plugin_slug)

        if stability:
            stmt = stmt.where(Skill.stability == stability)

        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Skill.name.ilike(search_term),
                    Skill.slug.ilike(search_term),
                    Skill.description.ilike(search_term),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Skill.name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        skills = result.scalars().all()

        return {
            "items": skills,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if page_size > 0 else 0,
        }

    async def get_skill(self, plugin_slug: str, skill_slug: str) -> Optional[Skill]:
        """Get a skill by plugin and skill slug."""
        stmt = select(Skill).join(Plugin).where(
            Plugin.slug == plugin_slug,
            Skill.slug == skill_slug,
        ).options(selectinload(Skill.plugin))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_stability_counts(self, plugin_slug: Optional[str] = None) -> Dict[str, int]:
        """Get counts of skills by stability level."""
        stmt = select(Skill.stability, func.count(Skill.id)).join(Plugin)

        if plugin_slug:
            stmt = stmt.where(Plugin.slug == plugin_slug)

        stmt = stmt.group_by(Skill.stability)
        result = await self.db.execute(stmt)
        return {row[0].value: row[1] for row in result.all()}

    async def get_plugin_stats(self) -> Dict[str, Any]:
        """Get overall plugin statistics."""
        total_plugins = await self.db.scalar(select(func.count(Plugin.id))) or 0
        total_skills = await self.db.scalar(select(func.count(Skill.id))) or 0
        total_commands = await self.db.scalar(select(func.count(Command.id))) or 0
        total_connectors = await self.db.scalar(select(func.count(Connector.id))) or 0

        stability_counts = await self.get_stability_counts()

        return {
            "total_plugins": total_plugins,
            "total_skills": total_skills,
            "total_commands": total_commands,
            "total_connectors": total_connectors,
            "stability_distribution": stability_counts,
        }