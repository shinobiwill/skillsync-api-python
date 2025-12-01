import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.db import get_db, Base
from app.models.models import User
import io

SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    echo=False,
    future=True
)

async_session_maker_test = async_sessionmaker(
    engine_test,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_db():
    async with async_session_maker_test() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

def test_criar_curriculo_sem_autenticacao(client):
    response = client.post(
        "/api/trpc/resumes.create",
        files={"file": ("test.pdf", io.BytesIO(b"test content"), "application/pdf")},
        data={
            "resume_title": "Meu Currículo",
            "summary": "Desenvolvedor Python",
            "is_public": False
        }
    )
    assert response.status_code == 403

def test_listar_curriculos_sem_autenticacao(client):
    response = client.get("/api/trpc/resumes.listByUser")
    assert response.status_code == 403

def test_criar_vaga_sem_autenticacao(client):
    response = client.post(
        "/api/trpc/jobs.create",
        json={
            "title": "Desenvolvedor Python",
            "company": "Tech Corp",
            "description": "Vaga para desenvolvedor Python sênior",
            "stack": ["Python", "FastAPI", "PostgreSQL"],
            "level": "senior"
        }
    )
    assert response.status_code == 403

def test_listar_vagas_publico(client):
    response = client.get("/api/trpc/jobs.list")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "SkillSync API"
    assert data["status"] == "running"
