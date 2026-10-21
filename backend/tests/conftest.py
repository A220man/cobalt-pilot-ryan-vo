# Backend test configuration
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import Settings


# Test settings
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key-for-testing-only",
        debug=True,
        environment="test",
    )


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_plugin_data():
    return {
        "slug": "test-plugin",
        "repo_path": "test-plugin",
        "manifest": {
            "name": "Test Plugin",
            "description": "A test plugin",
            "license": "MIT",
        },
    }


@pytest.fixture
def sample_skill_data():
    return {
        "slug": "test-skill",
        "name": "Test Skill",
        "description": "A test skill",
        "stability": "stable",
        "markdown_content": "# Test Skill\n\nContent here.",
        "frontmatter": {"name": "Test Skill", "stability": "stable"},
        "file_path": "test-plugin/skills/test-skill/SKILL.md",
    }