"""Shared test fixtures for BhuDrishti 3D backend tests."""
import sys
from pathlib import Path
import pytest
import httpx
from httpx import ASGITransport

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class MockQuery:
    def all(self): return []
    def filter(self, *args, **kwargs): return self
    def filter_by(self, **kwargs): return self
    def first(self): return None
    def offset(self, n): return self
    def limit(self, n): return self

class MockSession:
    def query(self, model): return MockQuery()
    def add(self, obj): pass
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *args): pass

@pytest.fixture
async def client():
    from app.main import app
    from app.dependencies import get_db

    def override_get_db():
        yield MockSession()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

DEMO_ULPIN = "7A4B9C2D8E1F6G"
DEMO_VERTICAL_ID = "7A4B9C2D8E1F6G-F04-U401-R01"
DEMO_SHA256 = "a" * 64
