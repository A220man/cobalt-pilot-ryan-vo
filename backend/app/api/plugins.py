# Plugin API routes
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.services.plugin_query import PluginQueryService
from app.services.plugin_sync import PluginSyncService
from app.api.schemas import (
    PluginListResponse,
    PluginDetailResponse,
    SkillResponse,
    PaginatedResponse,
    SyncLogResponse,
    PluginStatsResponse,
    StabilityLevel,
    PluginType,
)

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("/health", response_model=dict)
async def health_check():
    return {"status": "ok", "service": "plugins"}


@router.get("", response_model=PaginatedResponse)
async def list_plugins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    plugin_type: Optional[PluginType] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List plugins with pagination and filtering."""
    service = PluginQueryService(db)
    result = await service.list_plugins(page=page, page_size=page_size, search=search, plugin_type=plugin_type)

    # Convert to list response with counts
    items = []
    for plugin in result["items"]:
        items.append(PluginListResponse(
            id=plugin.id,
            slug=plugin.slug,
            name=plugin.name,
            description=plugin.description,
            plugin_type=plugin.plugin_type,
            repo_path=plugin.repo_path,
            readme_content=plugin.readme_content,
            license=plugin.license,
            created_at=plugin.created_at,
            updated_at=plugin.updated_at,
            skills_count=len(plugin.skills),
            commands_count=len(plugin.commands),
            connectors_count=len(plugin.connectors),
        ))

    return PaginatedResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/stats", response_model=PluginStatsResponse)
async def get_plugin_stats(db: AsyncSession = Depends(get_db)):
    """Get overall plugin statistics."""
    service = PluginQueryService(db)
    stats = await service.get_plugin_stats()
    return PluginStatsResponse(**stats)


@router.post("/sync", response_model=SyncLogResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_plugins(db: AsyncSession = Depends(get_db)):
    """Trigger a sync from the reference repository."""
    service = PluginSyncService(db)
    log = await service.sync_all()
    return SyncLogResponse(
        id=log.id,
        status=log.status,
        plugins_synced=log.plugins_synced,
        skills_synced=log.skills_synced,
        commands_synced=log.commands_synced,
        connectors_synced=log.connectors_synced,
        error_message=log.error_message,
        started_at=log.started_at,
        completed_at=log.completed_at,
    )


@router.get("/{slug}", response_model=PluginDetailResponse)
async def get_plugin(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a plugin by slug with all skills, commands, and connectors."""
    service = PluginQueryService(db)
    plugin = await service.get_plugin(slug)

    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    skills = [
        SkillResponse(
            id=s.id,
            slug=s.slug,
            name=s.name,
            description=s.description,
            stability=s.stability,
            markdown_content=s.markdown_content,
            frontmatter=s.frontmatter,
            file_path=s.file_path,
            created_at=s.created_at,
            updated_at=s.updated_at,
            plugin_slug=plugin.slug,
            plugin_name=plugin.name,
        )
        for s in plugin.skills
    ]

    commands = [
        {
            "id": c.id,
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "markdown_content": c.markdown_content,
            "file_path": c.file_path,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in plugin.commands
    ]

    connectors = [
        {
            "id": c.id,
            "name": c.name,
            "type": c.type,
            "config": c.config,
            "description": c.description,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in plugin.connectors
    ]

    return PluginDetailResponse(
        id=plugin.id,
        slug=plugin.slug,
        name=plugin.name,
        description=plugin.description,
        plugin_type=plugin.plugin_type,
        repo_path=plugin.repo_path,
        readme_content=plugin.readme_content,
        license=plugin.license,
        created_at=plugin.created_at,
        updated_at=plugin.updated_at,
        skills_count=len(plugin.skills),
        commands_count=len(plugin.commands),
        connectors_count=len(plugin.connectors),
        skills=skills,
        commands=commands,
        connectors=connectors,
    )


@router.get("/{plugin_slug}/skills", response_model=PaginatedResponse)
async def list_plugin_skills(
    plugin_slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    stability: Optional[StabilityLevel] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List skills for a plugin with filtering."""
    service = PluginQueryService(db)
    result = await service.list_skills(
        plugin_slug=plugin_slug,
        stability=stability,
        page=page,
        page_size=page_size,
        search=search,
    )

    items = [
        SkillResponse(
            id=s.id,
            slug=s.slug,
            name=s.name,
            description=s.description,
            stability=s.stability,
            markdown_content=s.markdown_content,
            frontmatter=s.frontmatter,
            file_path=s.file_path,
            created_at=s.created_at,
            updated_at=s.updated_at,
            plugin_slug=plugin_slug,
            plugin_name=s.plugin.name if s.plugin else None,
        )
        for s in result["items"]
    ]

    return PaginatedResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/{plugin_slug}/skills/{skill_slug}", response_model=SkillResponse)
async def get_skill(plugin_slug: str, skill_slug: str, db: AsyncSession = Depends(get_db)):
    """Get a specific skill."""
    service = PluginQueryService(db)
    skill = await service.get_skill(plugin_slug, skill_slug)

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return SkillResponse(
        id=skill.id,
        slug=skill.slug,
        name=skill.name,
        description=skill.description,
        stability=skill.stability,
        markdown_content=skill.markdown_content,
        frontmatter=skill.frontmatter,
        file_path=skill.file_path,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        plugin_slug=plugin_slug,
        plugin_name=skill.plugin.name if skill.plugin else None,
    )