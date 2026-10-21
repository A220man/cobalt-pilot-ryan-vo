# API schemas
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PluginType(str, Enum):
    OFFICIAL = "official"
    COMMUNITY = "community"


class StabilityLevel(str, Enum):
    EXPERIMENTAL = "experimental"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class SyncStatus(str, Enum):
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CommandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: Optional[str] = None
    markdown_content: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: Optional[str] = None
    stability: StabilityLevel
    markdown_content: Optional[str] = None
    frontmatter: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    plugin_slug: Optional[str] = None
    plugin_name: Optional[str] = None


class PluginListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: Optional[str] = None
    plugin_type: PluginType
    repo_path: Optional[str] = None
    readme_content: Optional[str] = None
    license: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    skills_count: int = 0
    commands_count: int = 0
    connectors_count: int = 0


class PluginDetailResponse(PluginListResponse):
    skills: List[SkillResponse] = []
    commands: List[CommandResponse] = []
    connectors: List[ConnectorResponse] = []


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: SyncStatus
    plugins_synced: int
    skills_synced: int
    commands_synced: int
    connectors_synced: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class PluginStatsResponse(BaseModel):
    total_plugins: int
    total_skills: int
    total_commands: int
    total_connectors: int
    stability_distribution: Dict[str, int]


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime