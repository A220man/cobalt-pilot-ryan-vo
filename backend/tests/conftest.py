# Backend test configuration
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import Settings
from app.core.security import create_access_token
from app.models.plugin import User


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


# Auth fixtures
@pytest.fixture
def auth_headers_viewer():
    """Headers for a viewer role user."""
    token = create_access_token({"sub": "test-viewer", "email": "viewer@test.com", "roles": ["viewer"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_operator():
    """Headers for an operator role user."""
    token = create_access_token({"sub": "test-operator", "email": "operator@test.com", "roles": ["viewer", "operator"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin():
    """Headers for an admin role user."""
    token = create_access_token({"sub": "test-admin", "email": "admin@test.com", "roles": ["viewer", "operator", "admin"]})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def test_user_viewer(test_db):
    """Create a viewer user in the database."""
    user = User(
        id="test-viewer",
        email="viewer@test.com",
        username="testviewer",
        full_name="Test Viewer",
        roles=["viewer"],
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    await test_db.commit()
    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_operator(test_db):
    """Create an operator user in the database."""
    user = User(
        id="test-operator",
        email="operator@test.com",
        username="testoperator",
        full_name="Test Operator",
        roles=["viewer", "operator"],
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    await test_db.commit()
    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_admin(test_db):
    """Create an admin user in the database."""
    user = User(
        id="test-admin",
        email="admin@test.com",
        username="testadmin",
        full_name="Test Admin",
        roles=["viewer", "operator", "admin"],
        is_active=True,
        is_superuser=True,
    )
    test_db.add(user)
    await test_db.commit()
    return user


@pytest_asyncio.fixture(scope="function")
async def client_with_auth(test_db, auth_headers_viewer, test_user_viewer):
    """Client with viewer auth headers."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=auth_headers_viewer) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client_with_operator_auth(test_db, auth_headers_operator, test_user_operator):
    """Client with operator auth headers."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=auth_headers_operator) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client_with_admin_auth(test_db, auth_headers_admin, test_user_admin):
    """Client with admin auth headers."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=auth_headers_admin) as ac:
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
