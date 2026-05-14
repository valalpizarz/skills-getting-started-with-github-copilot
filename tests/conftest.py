"""
Pytest configuration and shared fixtures for FastAPI app tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """
    Provide a TestClient instance for testing the FastAPI application.
    
    Each test gets a fresh client to avoid state pollution from the
    in-memory activities dictionary.
    """
    return TestClient(app)
