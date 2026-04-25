import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_db, Base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_read_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_create_participant():
    response = client.post(
        "/api/participants",
        json={"first_name": "John", "last_name": "Doe"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert "id" in data

def test_create_duplicate_participant():
    client.post("/api/participants", json={"first_name": "John", "last_name": "Doe"})
    response = client.post("/api/participants", json={"first_name": "John", "last_name": "Smith"})
    assert response.status_code == 400
    assert response.json()["detail"] == "First name must be unique"

def test_get_next_round_robin():
    # Add participants
    client.post("/api/participants", json={"first_name": "Alice", "last_name": "A"})
    client.post("/api/participants", json={"first_name": "Bob", "last_name": "B"})
    
    # Check who's next (should be Alice because of alphabetical tie-breaker)
    response = client.get("/api/next")
    assert response.status_code == 200
    data = response.json()
    assert data["participant"]["first_name"] == "Alice"
    
    # Record a release for Alice
    client.post("/api/releases", json={
        "participant_id": data["participant"]["id"],
        "version": "v1.0.0"
    })
    
    # Now Bob should be next (Alice has 1 release, Bob has 0)
    response = client.get("/api/next")
    assert response.status_code == 200
    data = response.json()
    assert data["participant"]["first_name"] == "Bob"
    
    # Record a release for Bob
    client.post("/api/releases", json={
        "participant_id": data["participant"]["id"],
        "version": "v1.1.0"
    })
    
    # Both have 1 release. Alice's release is older than Bob's, so Alice is next
    response = client.get("/api/next")
    assert response.status_code == 200
    data = response.json()
    assert data["participant"]["first_name"] == "Alice"
