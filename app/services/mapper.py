"""
Mapper Service
==============
Core mapping logic for roster code translation.

Implements:
- Longest-key-first matching (B19 matches before B1)
- Regex pattern support
- Multi-code cell handling (e.g., "B1/B19" -> "Rest/Training")

Author: datnguyentien@vietjetair.com
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage import StorageService

logger = get_logger(__name__)


class Mapper:
    """
    Roster code mapper with support for exact matches, patterns, and multi-codes.
    
    The mapper uses a longest-key-first strategy to ensure that longer codes
    (like 'B19') are matched before shorter ones (like 'B1') when the shorter
    code is a prefix of the longer one.
    
    Example:
        >>> mapper = Mapper("SGN")
        >>> mapper.map_cell("B1")
        'Rest'
        >>> mapper.map_cell("B19")
        'Training'
        >>> mapper.map_cell("B1/B19")
        'Rest/Training'
    """
    
    # Default separators for multi-code cells
    DEFAULT_SEPARATORS = ["/", ",", ";", " "]
    
    def __init__(
        self,
        station: str = "global",
        mappings: Optional[Dict[str, str]] = None,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the mapper.
        
        Args:
            station: Station code for loading station-specific mappings.
            mappings: Optional pre-loaded mapping dictionary.
            separators: Optional list of separators for multi-code cells.
        """
        self.station = station
        self.separators = separators or self.DEFAULT_SEPARATORS
        
        # Load mappings
        if mappings is not None:
            self._mappings = mappings
        else:
            self._mappings = self._load_mappings()
        
        # Build sorted keys for longest-first matching
        self._sorted_keys = self._build_sorted_keys()
        
        # Compile regex patterns
        self._patterns = self._compile_patterns()
        
        logger.info(
            "Mapper initialized",
            station=station,
            mapping_count=len(self._mappings)
        )
    
    def _load_mappings(self) -> Dict[str, str]:
        """
        Load mappings from storage.
        
        Tries station-specific mappings first, then falls back to global.
        
        Returns:
            Dictionary of code -> description mappings.
        """
        storage = StorageService()
        
        # Try station-specific mappings
        mappings = storage.load_mapping(self.station)
        
        if mappings:
            return mappings
        
        # Fall back to global mappings
        if self.station != "global":
            logger.warning(
                "Station mappings not found, using global",
                station=self.station
            )
            global_mappings = storage.load_mapping("global")
            if global_mappings:
                return global_mappings
        
        logger.warning("No mappings found", station=self.station)
        return {}
    
    def _build_sorted_keys(self) -> List[str]:
        """
        Build a list of mapping keys sorted by length (longest first).
        
        This ensures that 'B19' is matched before 'B1' when both exist.
        
        Returns:
            List of keys sorted by length descending.
        """
        return sorted(self._mappings.keys(), key=len, reverse=True)
    
    def _compile_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """
        Compile regex patterns from mappings.
        
        Keys starting with '^' or ending with '$' are treated as regex patterns.
        
        Returns:
            List of (compiled_pattern, description) tuples.
        """
        patterns = []
        
        for key, description in self._mappings.items():
            if key.startswith("^") or key.endswith("$") or "*" in key:
                try:
                    # Convert wildcard to regex if needed
                    pattern_str = key.replace("*", ".*")
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    patterns.append((pattern, description))
                except re.error as e:
                    logger.warning(
                        "Invalid regex pattern",
                        pattern=key,
                        error=str(e)
                    )
        
        return patterns
    
    def map_code(self, code: str) -> Optional[str]:
        """
        Map a single code to its description.
        
        Uses longest-key-first matching, then falls back to regex patterns.
        
        Args:
            code: The roster code to map.
            
        Returns:
            The description if found, None otherwise.
        """
        if not code or not code.strip():
            return None
        
        code_clean = code.strip()
        
        # Exact match (longest-first)
        for key in self._sorted_keys:
            if code_clean == key or code_clean.upper() == key.upper():
                return self._mappings[key]
        
        # Regex pattern match
        for pattern, description in self._patterns:
            if pattern.match(code_clean):
                return description
        
        return None
    
    def map_cell(self, cell_value: Any) -> str:
        """
        Map a cell value that may contain multiple codes.
        
        Handles multi-code cells by splitting on separators and mapping each code.
        
        Args:
            cell_value: The cell value (may be string, number, or None).
            
        Returns:
            The mapped value(s) or original value if no mapping found.
            
        Example:
            >>> mapper.map_cell("B1/B19")
            'Rest/Training'
            >>> mapper.map_cell("B1, B2")
            'Rest, Standby'
        """
        if cell_value is None or pd.isna(cell_value):
            return ""
        
        # Convert to string
        cell_str = str(cell_value).strip()
        
        if not cell_str:
            return ""
        
        # Try direct mapping first
        # Note: map_code returns None if not found, "" if mapped to empty
        direct_map = self.map_code(cell_str)
        if direct_map is not None:  # Explicitly check None to allow empty string mapping
            return direct_map
        
        # Try multi-code mapping
        for separator in self.separators:
            if separator in cell_str:
                parts = cell_str.split(separator)
                mapped_parts = []
                
                for part in parts:
                    part = part.strip()
                    mapped = self.map_code(part)
                    # If mapped is None (not found), keep original part
                    # If mapped is "" (explicitly mapped to empty), use empty string
                    if mapped is not None:
                        mapped_parts.append(mapped)
                    else:
                        mapped_parts.append(part)
                
                # Use same separator in output
                return separator.join(mapped_parts)
        
        # Return original if no mapping found
        return cell_str
    
    def map_dataframe(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        inplace: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Map codes in a DataFrame.
        
        Args:
            df: The input DataFrame.
            columns: List of column names to map. If None, maps all columns.
            inplace: If True, modifies the original DataFrame.
            
        Returns:
            Tuple of (mapped_dataframe, statistics_dict).
            
        Example:
            >>> mapped_df, stats = mapper.map_dataframe(df, columns=["Code", "Activity"])
            >>> print(stats)
            {'mapped_cells': 150, 'unchanged_cells': 50, 'empty_cells': 10}
        """
        if not inplace:
            df = df.copy()
        
        # Determine columns to process
        target_columns = columns if columns else list(df.columns)
        
        # Filter to existing columns
        target_columns = [c for c in target_columns if c in df.columns]
        
        # Statistics
        stats = {
            "total_cells": 0,
            "mapped_cells": 0,
            "unchanged_cells": 0,
            "empty_cells": 0,
            "columns_processed": target_columns
        }
        
        for col in target_columns:
            for idx in df.index:
                original = df.at[idx, col]
                stats["total_cells"] += 1
                
                if pd.isna(original) or str(original).strip() == "":
                    stats["empty_cells"] += 1
                    continue
                
                mapped = self.map_cell(original)
                
                if mapped != str(original):
                    df.at[idx, col] = mapped
                    stats["mapped_cells"] += 1
                else:
                    stats["unchanged_cells"] += 1
        
        logger.info(
            "DataFrame mapping completed",
            station=self.station,
            **stats
        )
        
        return df, stats
    
    def add_mapping(self, code: str, description: str) -> None:
        """
        Add a new mapping at runtime.
        
        Args:
            code: The roster code.
            description: The description/translation.
        """
        self._mappings[code] = description
        self._sorted_keys = self._build_sorted_keys()
        
        # Update patterns if it's a regex
        if code.startswith("^") or code.endswith("$") or "*" in code:
            self._patterns = self._compile_patterns()
    
    def remove_mapping(self, code: str) -> bool:
        """
        Remove a mapping at runtime.
        
        Args:
            code: The roster code to remove.
            
        Returns:
            True if removed, False if not found.
        """
        if code in self._mappings:
            del self._mappings[code]
            self._sorted_keys = self._build_sorted_keys()
            self._patterns = self._compile_patterns()
            return True
        return False
    
    @property
    def mappings(self) -> Dict[str, str]:
        """Get the current mappings dictionary."""
        return self._mappings.copy()
    
    def __len__(self) -> int:
        """Return the number of mappings."""
        return len(self._mappings)
    
    def __contains__(self, code: str) -> bool:
        """Check if a code exists in mappings."""
        return code in self._mappings

