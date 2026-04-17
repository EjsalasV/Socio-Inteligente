"""
Pytest configuration and fixtures for all tests
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set environment variables BEFORE importing the app
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-0123456789-abcdef")

from backend.utils.database import init_db
from backend.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database for all tests"""
    init_db()
    yield
    # Cleanup could go here if needed


@pytest.fixture
def client():
    """Create a test client with the app"""
    return TestClient(app)
