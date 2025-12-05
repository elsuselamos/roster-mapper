"""
UI Routes Tests
===============
Test web interface endpoints.

Author: datnguyentien@vietjetair.com
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestUIRoutes:
    """Test UI route responses."""
    
    def test_upload_page(self):
        """Test upload page returns 200."""
        response = client.get("/upload")
        assert response.status_code == 200
        assert "Upload" in response.text or "upload" in response.text.lower()
    
    def test_admin_page(self):
        """Test admin page returns 200."""
        response = client.get("/admin")
        assert response.status_code == 200
        assert "Admin" in response.text or "admin" in response.text.lower()
    
    def test_dashboard_page(self):
        """Test dashboard page returns 200."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "Dashboard" in response.text or "dashboard" in response.text.lower()
    
    def test_home_page(self):
        """Test home page renders successfully."""
        response = client.get("/", follow_redirects=False)
        # Home page renders upload directly (200) or redirects (302)
        assert response.status_code in [200, 302]
    
    def test_preview_page_accessible(self):
        """Test preview page is accessible (redirects if no session, 200 if session exists)."""
        response = client.get("/preview", follow_redirects=False)
        # 302 = no session (redirect to upload), 200 = has session data
        assert response.status_code in [200, 302]
    
    def test_results_page_accessible(self):
        """Test results page is accessible (redirects if no session, 200 if session exists)."""
        response = client.get("/results", follow_redirects=False)
        # 302 = no session (redirect to upload), 200 = has session data
        assert response.status_code in [200, 302]


class TestAPIEndpoints:
    """Test API endpoints return correct status."""
    
    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_stations_list(self):
        """Test stations list endpoint."""
        response = client.get("/api/v1/stations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_dashboard_stats(self):
        """Test dashboard stats endpoint."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_mappings" in data
        assert "stations" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

