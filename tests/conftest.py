"""
Pytest Configuration
====================
Fixtures and configuration for tests.

Author: datnguyentien@vietjetair.com
"""

import pytest
from typing import Dict

import pandas as pd


@pytest.fixture
def sample_mappings() -> Dict[str, str]:
    """Sample mappings for testing."""
    return {
        "B1": "Nghỉ phép",
        "B2": "Standby",
        "B19": "Đào tạo chuyên sâu",
        "OFF": "Nghỉ",
        "AL": "Annual Leave",
        "TR": "Training"
    }


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        "Name": ["Nguyễn Văn A", "Trần Thị B", "Lê Văn C"],
        "Code": ["B1", "B19", "B1/B2"],
        "Activity": ["OFF", "TR", "AL"]
    })


@pytest.fixture
def multi_code_test_cases() -> list:
    """Test cases for multi-code cells."""
    return [
        ("B1/B19", "Nghỉ phép/Đào tạo chuyên sâu"),
        ("B1, B2", "Nghỉ phép, Standby"),
        ("OFF;TR", "Nghỉ;Training"),
        ("B1 B2", "Nghỉ phép Standby"),
    ]

