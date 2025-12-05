"""
Storage Service
===============
Local storage adapter for files and mappings.

Author: datnguyentien@vietjetair.com
"""

import json
import shutil
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import aiofiles
from fastapi import UploadFile
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    Storage service for managing files and mappings.
    
    Handles:
    - Uploaded file storage
    - Processed file storage
    - Mapping file management with versioning
    - Audit logging
    
    Example:
        >>> storage = StorageService()
        >>> file_id, path = await storage.save_uploaded_file(upload)
        >>> mappings = storage.load_mapping("SGN")
    """
    
    def __init__(
        self,
        mapping_dir: Optional[Path] = None,
        storage_dir: Optional[Path] = None,
        temp_dir: Optional[Path] = None
    ):
        """
        Initialize storage service.
        
        Args:
            mapping_dir: Directory for mapping files.
            storage_dir: Directory for uploaded files.
            temp_dir: Directory for temporary files.
        """
        self.mapping_dir = mapping_dir or settings.MAPPING_DIR
        self.storage_dir = storage_dir or settings.STORAGE_DIR
        self.temp_dir = temp_dir or settings.TEMP_DIR
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.mapping_dir, self.storage_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    # ========== File Upload Methods ==========
    
    async def save_uploaded_file(
        self,
        file: UploadFile,
        file_id: Optional[str] = None
    ) -> Tuple[str, Path]:
        """
        Save an uploaded file to storage.
        
        Args:
            file: The uploaded file.
            file_id: Optional custom file ID.
            
        Returns:
            Tuple of (file_id, saved_path).
        """
        file_id = file_id or str(uuid.uuid4())
        
        # Preserve original extension
        ext = Path(file.filename or "").suffix or ".xlsx"
        filename = f"{file_id}{ext}"
        save_path = self.storage_dir / "uploads" / filename
        
        # Ensure upload directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        async with aiofiles.open(save_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(
            "File saved",
            file_id=file_id,
            path=str(save_path),
            size=len(content)
        )
        
        return file_id, save_path
    
    def get_uploaded_file_path(self, file_id: str) -> Path:
        """
        Get the path to an uploaded file.
        
        Args:
            file_id: The file identifier.
            
        Returns:
            Path to the uploaded file.
        """
        upload_dir = self.storage_dir / "uploads"
        
        # Try common extensions
        for ext in [".xlsx", ".xls"]:
            path = upload_dir / f"{file_id}{ext}"
            if path.exists():
                return path
        
        # Return default path (may not exist)
        return upload_dir / f"{file_id}.xlsx"
    
    def get_processed_file_path(self, file_id: str, format_type: str = "styled") -> Path:
        """
        Get the path to a processed file.
        
        Args:
            file_id: The file identifier.
            format_type: "styled" (preserve formatting) or "plain" (text only).
            
        Returns:
            Path to the processed file.
        """
        if format_type == "plain":
            return self.storage_dir / "processed" / f"{file_id}_mapped_plain.xlsx"
        return self.storage_dir / "processed" / f"{file_id}_mapped.xlsx"
    
    def save_processed_file(
        self,
        file_id: str,
        df: pd.DataFrame
    ) -> Path:
        """
        Save a processed DataFrame as an Excel file.
        
        Args:
            file_id: The original file identifier.
            df: The processed DataFrame.
            
        Returns:
            Path to the saved file.
        """
        output_path = self.get_processed_file_path(file_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_excel(output_path, index=False, engine="openpyxl")
        
        logger.info("Processed file saved", file_id=file_id, path=str(output_path))
        
        return output_path
    
    def save_processed_file_multi_sheet(
        self,
        file_id: str,
        sheets_data: Dict[str, pd.DataFrame]
    ) -> Path:
        """
        Save multiple processed DataFrames to separate sheets in one Excel file.
        
        NOTE: This method does NOT preserve formatting from original file.
        Use copy_file_for_processing() + ExcelProcessor.map_workbook_preserve_style()
        for style preservation.
        
        Args:
            file_id: The original file identifier.
            sheets_data: Dictionary of sheet_name -> DataFrame.
            
        Returns:
            Path to the saved file.
        """
        output_path = self.get_processed_file_path(file_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets_data.items():
                # Excel sheet name limit is 31 characters
                safe_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
                df.to_excel(writer, sheet_name=safe_name, index=False)
        
        logger.info(
            "Multi-sheet processed file saved", 
            file_id=file_id, 
            path=str(output_path),
            sheets=list(sheets_data.keys())
        )
        
        return output_path
    
    def copy_file_for_processing(self, file_id: str, format_type: str = "styled") -> Path:
        """
        Copy uploaded file to processed directory for in-place mapping.
        
        This is used for style-preserving mapping where we modify the 
        Excel file directly instead of creating a new one.
        
        Args:
            file_id: The file identifier.
            format_type: "styled" or "plain".
            
        Returns:
            Path to the copied file in processed directory.
        """
        source_path = self.get_uploaded_file_path(file_id)
        dest_path = self.get_processed_file_path(file_id, format_type)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        logger.info(
            "File copied for processing",
            file_id=file_id,
            format_type=format_type,
            source=str(source_path),
            dest=str(dest_path)
        )
        
        return dest_path
    
    def delete_uploaded_file(self, file_id: str) -> bool:
        """
        Delete an uploaded file.
        
        Args:
            file_id: The file identifier.
            
        Returns:
            True if deleted, False if not found.
        """
        path = self.get_uploaded_file_path(file_id)
        
        if path.exists():
            path.unlink()
            logger.info("Uploaded file deleted", file_id=file_id)
            return True
        
        return False
    
    # ========== Mapping Methods ==========
    
    def save_mapping(
        self,
        station: str,
        mappings: Dict[str, str],
        replace: bool = False,
        created_by: Optional[str] = None
    ) -> str:
        """
        Save mappings for a station.
        
        Creates a new version and updates the 'latest' pointer.
        
        Args:
            station: Station code (e.g., 'SGN', 'HAN').
            mappings: Dictionary of code -> description.
            replace: If True, replace existing mappings entirely.
            created_by: Optional user identifier.
            
        Returns:
            Version string (timestamp-based).
        """
        station_dir = self.mapping_dir / station
        station_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate version
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load existing if not replacing
        if not replace:
            existing = self.load_mapping(station)
            if existing:
                existing.update(mappings)
                mappings = existing
        
        # Prepare mapping data with metadata
        mapping_data = {
            "_meta": {
                "version": version,
                "station": station,
                "created_at": datetime.now().isoformat(),
                "created_by": created_by,
                "entry_count": len(mappings)
            },
            "mappings": mappings
        }
        
        # Save versioned file
        version_path = station_dir / f"{version}.json"
        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        # Update latest pointer
        latest_path = station_dir / "latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        logger.info(
            "Mapping saved",
            station=station,
            version=version,
            count=len(mappings)
        )
        
        # Log to audit
        self._log_audit(
            action="mapping_saved",
            station=station,
            details={
                "version": version,
                "entry_count": len(mappings),
                "replace": replace
            },
            user=created_by
        )
        
        return version
    
    def load_mapping(
        self,
        station: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Load mappings for a station.
        
        Args:
            station: Station code.
            version: Specific version (default: latest).
            
        Returns:
            Dictionary of code -> description, or None if not found.
        """
        station_dir = self.mapping_dir / station
        
        if version:
            mapping_path = station_dir / f"{version}.json"
        else:
            mapping_path = station_dir / "latest.json"
        
        if not mapping_path.exists():
            return None
        
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Handle both formats (with/without metadata)
            if "mappings" in data:
                return data["mappings"]
            elif "_meta" not in data:
                # Old format: direct mapping dict
                return data
            
            return None
            
        except json.JSONDecodeError:
            logger.error("Invalid mapping file", path=str(mapping_path))
            return None
    
    def list_mapping_versions(self, station: str) -> List[Dict[str, Any]]:
        """
        List all mapping versions for a station.
        
        Args:
            station: Station code.
            
        Returns:
            List of version info dictionaries.
        """
        station_dir = self.mapping_dir / station
        
        if not station_dir.exists():
            return []
        
        versions = []
        
        for path in station_dir.glob("*.json"):
            if path.name == "latest.json":
                continue
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                meta = data.get("_meta", {})
                versions.append({
                    "version": meta.get("version", path.stem),
                    "created_at": datetime.fromisoformat(meta["created_at"]) if meta.get("created_at") else datetime.fromtimestamp(path.stat().st_mtime),
                    "entry_count": meta.get("entry_count", len(data.get("mappings", data))),
                    "created_by": meta.get("created_by")
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by creation time descending
        versions.sort(key=lambda v: v["created_at"], reverse=True)
        
        return versions
    
    def delete_mapping(
        self,
        station: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Delete mappings for a station.
        
        Args:
            station: Station code.
            version: Specific version to delete (all if None).
            
        Returns:
            True if deleted, False if not found.
        """
        station_dir = self.mapping_dir / station
        
        if not station_dir.exists():
            return False
        
        if version:
            version_path = station_dir / f"{version}.json"
            if version_path.exists():
                version_path.unlink()
                logger.info("Mapping version deleted", station=station, version=version)
                return True
            return False
        else:
            # Delete all mappings for station
            shutil.rmtree(station_dir)
            logger.warning("All mappings deleted", station=station)
            return True
    
    def mapping_exists(self, station: str) -> bool:
        """
        Check if mappings exist for a station.
        
        Args:
            station: Station code.
            
        Returns:
            True if mappings exist.
        """
        latest_path = self.mapping_dir / station / "latest.json"
        return latest_path.exists()
    
    # ========== Audit Log Methods ==========
    
    def _log_audit(
        self,
        action: str,
        station: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None
    ) -> None:
        """
        Log an action to the audit log.
        
        Args:
            action: Action type (e.g., 'mapping_saved', 'file_uploaded').
            station: Related station code.
            details: Additional details.
            user: User who performed the action.
        """
        audit_path = self.storage_dir / "audit_log.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "station": station,
            "user": user,
            "details": details or {}
        }
        
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_audit_log(
        self,
        station: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            station: Filter by station.
            action: Filter by action type.
            limit: Maximum entries to return.
            
        Returns:
            List of audit log entries.
        """
        audit_path = self.storage_dir / "audit_log.jsonl"
        
        if not audit_path.exists():
            return []
        
        entries = []
        
        with open(audit_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    # Apply filters
                    if station and entry.get("station") != station:
                        continue
                    if action and entry.get("action") != action:
                        continue
                    
                    # Parse timestamp
                    entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                    entries.append(entry)
                    
                except json.JSONDecodeError:
                    continue
        
        # Sort by timestamp descending and limit
        entries.sort(key=lambda e: e["timestamp"], reverse=True)
        
        return entries[:limit]

