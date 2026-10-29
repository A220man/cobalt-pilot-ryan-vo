# Plugin models
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any

from app.core.database import Base


class PluginType(str, PyEnum):
    OFFICIAL = "official"
    COMMUNITY = "community"


class StabilityLevel(str, PyEnum):
    EXPERIMENTAL = "experimental"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    plugin_type = Column(SQLEnum(PluginType), default=PluginType.OFFICIAL, nullable=False)
    repo_path = Column(String(500), nullable=True)  # e.g., "bio-research"
    readme_content = Column(Text, nullable=True)
    license = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    skills = relationship("Skill", back_populates="plugin", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="plugin", cascade="all, delete-orphan")
    connectors = relationship("Connector", back_populates="plugin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_plugins_slug_type", "slug", "plugin_type"),
    )


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    stability = Column(SQLEnum(StabilityLevel), default=StabilityLevel.EXPERIMENTAL, nullable=False)
    category = Column(String(100), nullable=True)
    readme_content = Column(Text, nullable=True)
    frontmatter = Column(JSON, nullable=True)
    markdown_content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    plugin = relationship("Plugin", back_populates="skills")

    __table_args__ = (
        Index("ix_skills_plugin_stability", "plugin_id", "stability"),
        Index("ix_skills_name", "name"),
        Index("ix_skills_plugin_slug", "plugin_id", "slug", unique=True),
    )


class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    usage = Column(Text, nullable=True)
    markdown_content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    plugin = relationship("Plugin", back_populates="commands")

    __table_args__ = (
        Index("ix_commands_plugin", "plugin_id"),
        Index("ix_commands_name", "name"),
        Index("ix_commands_plugin_slug", "plugin_id", "slug", unique=True),
    )


class Connector(Base):
    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(200), nullable=False, index=True, default="")
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    plugin = relationship("Plugin", back_populates="connectors")

    __table_args__ = (
        Index("ix_connectors_plugin", "plugin_id"),
        Index("ix_connectors_name", "name"),
        Index("ix_connectors_plugin_slug", "plugin_id", "slug", unique=True),
    )


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), nullable=False)  # success, failed, partial
    plugins_synced = Column(Integer, default=0)
    skills_synced = Column(Integer, default=0)
    commands_synced = Column(Integer, default=0)
    connectors_synced = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)  # Keycloak sub
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(200), nullable=True)
    roles = Column(JSON, default=list, nullable=False)  # List of roles from Keycloak
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
