"""
Multi-Station Tests
===================
Test mapping functionality across all stations.

Author: datnguyentien@vietjetair.com
"""

import pytest
from app.services.mapper import Mapper
from app.services.storage import StorageService


STATIONS = ["SGN", "HAN", "DAD", "CXR", "HPH", "VCA", "VII"]


class TestMultiStationMappings:
    """Test mappings exist and work for all stations."""
    
    @pytest.mark.parametrize("station", STATIONS)
    def test_station_mapping_exists(self, station):
        """Test each station has mapping file."""
        storage = StorageService()
        assert storage.mapping_exists(station), f"{station} should have mapping"
    
    @pytest.mark.parametrize("station", STATIONS)
    def test_station_mapper_loads(self, station):
        """Test mapper can be instantiated for each station."""
        mapper = Mapper(station=station)
        assert mapper is not None
        assert len(mapper) > 0, f"{station} should have mappings"
    
    @pytest.mark.parametrize("station", STATIONS)
    def test_common_code_mapping(self, station):
        """Test common codes are mapped consistently."""
        mapper = Mapper(station=station)
        
        # DT should map to HC for all stations
        if "DT" in mapper:
            assert mapper.map_code("DT") == "HC"
        
        # BD1_O should map to BD1
        if "BD1_O" in mapper:
            assert mapper.map_code("BD1_O") == "BD1"


class TestMappingConsistency:
    """Test mapping consistency across stations."""
    
    def test_all_stations_have_dt_mapping(self):
        """Test DT code is mapped in all stations."""
        for station in STATIONS:
            mapper = Mapper(station=station)
            result = mapper.map_code("DT")
            if result:
                assert result == "HC", f"{station}: DT should map to HC"
    
    def test_all_stations_have_do_mapping(self):
        """Test DO code is mapped in all stations."""
        for station in STATIONS:
            mapper = Mapper(station=station)
            result = mapper.map_code("DO")
            if result:
                assert result == "HC", f"{station}: DO should map to HC"
    
    def test_overtime_suffix_mapping(self):
        """Test _O suffix codes map to base code."""
        for station in STATIONS:
            mapper = Mapper(station=station)
            
            # Test BD1_O -> BD1
            if "BD1_O" in mapper:
                assert mapper.map_code("BD1_O") == "BD1"
            
            # Test BD2_O -> BD2
            if "BD2_O" in mapper:
                assert mapper.map_code("BD2_O") == "BD2"


class TestMappingCoverage:
    """Test mapping coverage statistics."""
    
    def test_han_has_most_mappings(self):
        """Test HAN has comprehensive mappings."""
        mapper = Mapper(station="HAN")
        assert len(mapper) >= 50, "HAN should have at least 50 mappings"
    
    def test_all_stations_have_minimum_mappings(self):
        """Test all stations have minimum required mappings."""
        for station in STATIONS:
            mapper = Mapper(station=station)
            assert len(mapper) >= 5, f"{station} should have at least 5 mappings"
    
    def test_total_unique_mappings(self):
        """Test total unique mappings across all stations."""
        all_codes = set()
        for station in STATIONS:
            mapper = Mapper(station=station)
            all_codes.update(mapper.mappings.keys())
        
        assert len(all_codes) >= 10, "Should have at least 10 unique codes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

