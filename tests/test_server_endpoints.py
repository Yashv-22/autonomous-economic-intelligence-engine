"""
Unit and regression tests for Server dashboard and favicon assets.
Ensures /favicon.ico, /favicon.svg, /site.webmanifest, and the dashboard
are served with appropriate status codes and content types.
"""

import pytest
from fastapi.testclient import TestClient
from src.server.app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_dashboard_endpoint(client):
    """Test dashboard serving with favicon link declarations."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "/static/favicon.svg" in response.text
    assert "/favicon.ico" in response.text
    assert "/static/site.webmanifest" in response.text


def test_favicon_ico_endpoint(client):
    """Test standard browser /favicon.ico route."""
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert "image/x-icon" in response.headers.get("content-type", "")
    assert len(response.content) > 0


def test_favicon_svg_endpoint(client):
    """Test scalable vector /favicon.svg route."""
    response = client.get("/favicon.svg")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers.get("content-type", "")
    assert b"<svg" in response.content


def test_site_manifest_endpoint(client):
    """Test PWA / web application manifest."""
    response = client.get("/site.webmanifest")
    assert response.status_code == 200
    assert "application/manifest+json" in response.headers.get("content-type", "")
    data = response.json()
    assert "Autonomous Economic Intelligence" in data["name"]
