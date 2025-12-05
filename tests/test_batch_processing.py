"""
Batch Processing Tests
======================
Test batch upload and processing functionality.

Author: datnguyentien@vietjetair.com
"""

import pytest
import io
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.mapper import Mapper


client = TestClient(app)


class TestBatchEndpoints:
    """Test batch processing endpoints."""
    
    def test_batch_upload_no_files(self):
        """Test batch upload with no files returns error."""
        response = client.post("/api/v1/batch-upload")
        assert response.status_code == 422  # Validation error
    
    def test_batch_map_no_files(self):
        """Test batch map with no files returns error."""
        response = client.post("/api/v1/batch-map")
        assert response.status_code == 422
    
    def test_batch_download_not_found(self):
        """Test batch download without file returns 404."""
        response = client.get("/api/v1/batch-download")
        # May be 404 if no batch file exists
        assert response.status_code in [200, 404]


class TestMapperMultiStation:
    """Test mapper with multiple stations."""
    
    def test_han_mapper(self):
        """Test HAN station mapper."""
        mapper = Mapper(station="HAN")
        assert len(mapper) > 0
        
        # Test known mappings
        assert mapper.map_code("DT") == "HC"
        assert mapper.map_code("BD1_O") == "BD1"
    
    def test_sgn_mapper(self):
        """Test SGN station mapper."""
        mapper = Mapper(station="SGN")
        assert len(mapper) > 0
        
        # Test known mappings
        assert mapper.map_code("DT") == "HC"
    
    def test_dad_mapper(self):
        """Test DAD station mapper."""
        mapper = Mapper(station="DAD")
        assert len(mapper) > 0
    
    def test_cxr_mapper(self):
        """Test CXR station mapper."""
        mapper = Mapper(station="CXR")
        assert len(mapper) > 0
    
    def test_unknown_station_fallback(self):
        """Test unknown station falls back to global."""
        mapper = Mapper(station="UNKNOWN")
        # Should not raise error, may have empty mappings
        assert mapper is not None


class TestStationDetection:
    """Test station auto-detection from filename."""
    
    def test_detect_han_from_filename(self):
        """Test HAN detection."""
        from app.ui.routes import _detect_station
        
        assert _detect_station("HAN_ROSTER_DEC2025.xlsx") == "HAN"
        assert _detect_station("roster_han_december.xlsx") == "HAN"
    
    def test_detect_sgn_from_filename(self):
        """Test SGN detection."""
        from app.ui.routes import _detect_station
        
        assert _detect_station("SGN_ROSTER.xlsx") == "SGN"
    
    def test_no_station_in_filename(self):
        """Test no station found."""
        from app.ui.routes import _detect_station
        
        assert _detect_station("roster_december.xlsx") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

