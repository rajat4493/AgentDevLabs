from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Base, get_session
from backend.main import app

engine = create_engine("sqlite+pysqlite:///:memory:", future=True, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base.metadata.create_all(bind=engine)


def override_get_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


def test_create_trace_and_fetch() -> None:
    payload = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "input": "ping",
        "output": "pong",
        "tokens": 12,
        "latency_ms": 42,
        "framework": "unit-test",
        "source": "tests",
        "extra": {"foo": "bar"},
    }
    resp = client.post("/api/traces", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    trace_id = data["id"]
    assert data["provider"] == "openai"

    resp_get = client.get(f"/api/traces/{trace_id}")
    assert resp_get.status_code == 200
    fetched = resp_get.json()
    assert fetched["input"] == "ping"
    assert fetched["extra"]["foo"] == "bar"


def test_chat_endpoint_uses_stub_provider() -> None:
    payload = {
        "prompt": "Say hello",
        "provider": "stub",
        "model": "stub-echo-1",
        "framework": "tests",
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["provider"] == "stub"
    assert data["trace_id"]
    assert data["output"]

    traces_resp = client.get("/api/traces")
    assert traces_resp.status_code == 200
    traces = traces_resp.json()
    assert traces["total"] >= 1
