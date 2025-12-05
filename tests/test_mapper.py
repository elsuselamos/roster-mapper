"""
Mapper Unit Tests
=================
Tests for the Mapper service.

Tests:
- B1/B19 longest-key-first matching
- Multi-code cell handling
- DataFrame mapping

Author: datnguyentien@vietjetair.com
"""

import pytest
import pandas as pd

from app.services.mapper import Mapper


class TestMapperBasics:
    """Test basic mapping functionality."""
    
    def test_mapper_initialization(self, sample_mappings):
        """Test mapper initializes correctly with mappings."""
        mapper = Mapper(mappings=sample_mappings)
        
        assert len(mapper) == 6
        assert "B1" in mapper
        assert "B19" in mapper
    
    def test_single_code_mapping(self, sample_mappings):
        """Test mapping of single codes."""
        mapper = Mapper(mappings=sample_mappings)
        
        assert mapper.map_code("B1") == "Nghỉ phép"
        assert mapper.map_code("B19") == "Đào tạo chuyên sâu"
        assert mapper.map_code("OFF") == "Nghỉ"
    
    def test_unknown_code_returns_none(self, sample_mappings):
        """Test that unknown codes return None."""
        mapper = Mapper(mappings=sample_mappings)
        
        assert mapper.map_code("UNKNOWN") is None
        assert mapper.map_code("XYZ") is None
    
    def test_empty_input(self, sample_mappings):
        """Test handling of empty input."""
        mapper = Mapper(mappings=sample_mappings)
        
        assert mapper.map_code("") is None
        assert mapper.map_code(None) is None
        assert mapper.map_code("   ") is None


class TestLongestKeyFirst:
    """Test longest-key-first matching strategy."""
    
    def test_b19_before_b1(self, sample_mappings):
        """Test that B19 is matched before B1."""
        mapper = Mapper(mappings=sample_mappings)
        
        # B19 should get its own mapping, not be confused with B1
        assert mapper.map_code("B19") == "Đào tạo chuyên sâu"
        assert mapper.map_code("B1") == "Nghỉ phép"
    
    def test_sorted_keys_longest_first(self, sample_mappings):
        """Test that internal keys are sorted longest first."""
        mapper = Mapper(mappings=sample_mappings)
        
        # B19 (len=3) should come before B1 (len=2)
        b19_idx = mapper._sorted_keys.index("B19")
        b1_idx = mapper._sorted_keys.index("B1")
        
        assert b19_idx < b1_idx, "B19 should be before B1 in sorted keys"
    
    def test_case_insensitive_matching(self, sample_mappings):
        """Test case-insensitive code matching."""
        mapper = Mapper(mappings=sample_mappings)
        
        assert mapper.map_code("b1") == "Nghỉ phép"
        assert mapper.map_code("B1") == "Nghỉ phép"
        assert mapper.map_code("off") == "Nghỉ"


class TestMultiCodeCells:
    """Test multi-code cell handling."""
    
    def test_slash_separator(self, sample_mappings):
        """Test codes separated by slash."""
        mapper = Mapper(mappings=sample_mappings)
        
        result = mapper.map_cell("B1/B19")
        assert result == "Nghỉ phép/Đào tạo chuyên sâu"
    
    def test_comma_separator(self, sample_mappings):
        """Test codes separated by comma."""
        mapper = Mapper(mappings=sample_mappings)
        
        result = mapper.map_cell("B1, B2")
        # Mapper joins results with original separator (without extra space)
        assert result == "Nghỉ phép,Standby"
    
    def test_semicolon_separator(self, sample_mappings):
        """Test codes separated by semicolon."""
        mapper = Mapper(mappings=sample_mappings)
        
        result = mapper.map_cell("OFF;TR")
        assert result == "Nghỉ;Training"
    
    def test_space_separator(self, sample_mappings):
        """Test codes separated by space."""
        mapper = Mapper(mappings=sample_mappings)
        
        result = mapper.map_cell("B1 B2")
        assert result == "Nghỉ phép Standby"
    
    def test_mixed_known_unknown(self, sample_mappings):
        """Test cells with both known and unknown codes."""
        mapper = Mapper(mappings=sample_mappings)
        
        # Unknown code should remain unchanged
        result = mapper.map_cell("B1/UNKNOWN")
        assert result == "Nghỉ phép/UNKNOWN"


class TestMapCell:
    """Test map_cell method with various inputs."""
    
    def test_none_value(self, sample_mappings):
        """Test handling of None values."""
        mapper = Mapper(mappings=sample_mappings)
        
        assert mapper.map_cell(None) == ""
    
    def test_numeric_value(self, sample_mappings):
        """Test handling of numeric values."""
        mapper = Mapper(mappings=sample_mappings)
        
        # Numbers should be converted to string
        assert mapper.map_cell(123) == "123"
    
    def test_direct_match_priority(self, sample_mappings):
        """Test that direct match takes priority over splitting."""
        mapper = Mapper(mappings={"A/B": "Combined"})
        
        # Should match "A/B" directly, not split
        result = mapper.map_cell("A/B")
        assert result == "Combined"


class TestDataFrameMapping:
    """Test DataFrame mapping functionality."""
    
    def test_basic_dataframe_mapping(self, sample_mappings, sample_dataframe):
        """Test basic DataFrame mapping."""
        mapper = Mapper(mappings=sample_mappings)
        
        mapped_df, stats = mapper.map_dataframe(
            sample_dataframe,
            columns=["Code", "Activity"]
        )
        
        assert mapped_df["Code"].iloc[0] == "Nghỉ phép"
        assert mapped_df["Code"].iloc[1] == "Đào tạo chuyên sâu"
        assert stats["mapped_cells"] > 0
    
    def test_dataframe_preserves_original(self, sample_mappings, sample_dataframe):
        """Test that original DataFrame is not modified."""
        mapper = Mapper(mappings=sample_mappings)
        original_value = sample_dataframe["Code"].iloc[0]
        
        mapped_df, _ = mapper.map_dataframe(sample_dataframe, columns=["Code"])
        
        assert sample_dataframe["Code"].iloc[0] == original_value
        assert mapped_df["Code"].iloc[0] != original_value
    
    def test_dataframe_inplace_modification(self, sample_mappings, sample_dataframe):
        """Test inplace DataFrame modification."""
        mapper = Mapper(mappings=sample_mappings)
        df_copy = sample_dataframe.copy()
        
        mapper.map_dataframe(df_copy, columns=["Code"], inplace=True)
        
        assert df_copy["Code"].iloc[0] == "Nghỉ phép"
    
    def test_dataframe_stats(self, sample_mappings, sample_dataframe):
        """Test that mapping statistics are correct."""
        mapper = Mapper(mappings=sample_mappings)
        
        _, stats = mapper.map_dataframe(
            sample_dataframe,
            columns=["Code", "Activity"]
        )
        
        assert "total_cells" in stats
        assert "mapped_cells" in stats
        assert "unchanged_cells" in stats
        assert stats["total_cells"] == 6  # 3 rows * 2 columns


class TestMapperDynamicOperations:
    """Test dynamic mapping operations."""
    
    def test_add_mapping(self, sample_mappings):
        """Test adding a new mapping."""
        mapper = Mapper(mappings=sample_mappings)
        
        mapper.add_mapping("NEW", "New Description")
        
        assert mapper.map_code("NEW") == "New Description"
        assert len(mapper) == 7
    
    def test_remove_mapping(self, sample_mappings):
        """Test removing a mapping."""
        mapper = Mapper(mappings=sample_mappings)
        
        result = mapper.remove_mapping("B1")
        
        assert result is True
        assert mapper.map_code("B1") is None
        assert len(mapper) == 5
    
    def test_remove_nonexistent_mapping(self, sample_mappings):
        """Test removing a non-existent mapping."""
        mapper = Mapper(mappings=sample_mappings)
        
        result = mapper.remove_mapping("NONEXISTENT")
        
        assert result is False


class TestRegexPatterns:
    """Test regex pattern matching."""
    
    def test_wildcard_pattern(self):
        """Test wildcard pattern matching."""
        mappings = {
            "B*": "B-series code",
            "B1": "Specific B1"
        }
        mapper = Mapper(mappings=mappings)
        
        # Exact match should take priority
        assert mapper.map_code("B1") == "Specific B1"
    
    def test_regex_pattern(self):
        """Test regex pattern matching."""
        mappings = {
            "^TR\\d+$": "Training code",
            "TR": "Training"
        }
        mapper = Mapper(mappings=mappings)
        
        # Exact match
        assert mapper.map_code("TR") == "Training"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

