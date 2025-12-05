"""
Dashboard Query Tests
=====================
Test dashboard statistics and aggregation.

Author: datnguyentien@vietjetair.com
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage import StorageService


client = TestClient(app)


class TestDashboardStats:
    """Test dashboard statistics endpoints."""
    
    def test_get_stats(self):
        """Test getting overall stats."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_mappings" in data
        assert "active_stations" in data
        assert "total_stations" in data
        assert "stations" in data
        
        # Should have 7 stations
        assert data["total_stations"] == 7
    
    def test_station_stats(self):
        """Test getting station-specific stats."""
        response = client.get("/api/v1/dashboard/stats/station/HAN")
        assert response.status_code == 200
        
        data = response.json()
        assert data["station"] == "HAN"
        assert "mapping_count" in data
    
    def test_unknown_station_stats(self):
        """Test unknown station returns error."""
        response = client.get("/api/v1/dashboard/stats/station/UNKNOWN")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
    
    def test_action_stats(self):
        """Test action statistics."""
        response = client.get("/api/v1/dashboard/stats/actions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_timeline_stats(self):
        """Test timeline statistics."""
        response = client.get("/api/v1/dashboard/stats/timeline?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have entries for each day
        assert len(data) >= 7


class TestStorageService:
    """Test storage service functionality."""
    
    def test_mapping_exists(self):
        """Test checking if mapping exists."""
        storage = StorageService()
        
        # HAN should have mapping
        assert storage.mapping_exists("HAN") == True
    
    def test_load_mapping(self):
        """Test loading mapping."""
        storage = StorageService()
        
        mappings = storage.load_mapping("HAN")
        assert mappings is not None
        assert isinstance(mappings, dict)
    
    def test_list_versions(self):
        """Test listing mapping versions."""
        storage = StorageService()
        
        versions = storage.list_mapping_versions("HAN")
        assert isinstance(versions, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

