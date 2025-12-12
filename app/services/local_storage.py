"""
Local Storage Service
=====================
Ephemeral local filesystem storage adapter for Cloud Run deployment.

Uses /tmp directory for temporary file storage (Cloud Run ephemeral disk).
Files are automatically cleaned up when container restarts.

Author: Vietjet AMO - IT Department
"""

import os
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LocalStorage:
    """
    Local filesystem storage adapter.
    
    Designed for ephemeral storage on Cloud Run (/tmp).
    Provides upload, output, and cleanup functionality.
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        retention_seconds: int = 3600  # 1 hour default
    ):
        """
        Initialize local storage.
        
        Args:
            storage_dir: Directory for uploaded files
            output_dir: Directory for processed output files
            retention_seconds: How long to keep files before cleanup
        """
        self.storage_dir = storage_dir or settings.STORAGE_DIR
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.retention_seconds = retention_seconds
        
        # Ensure directories exist
        self._ensure_directories()
        
        logger.info(
            "LocalStorage initialized",
            storage_dir=str(self.storage_dir),
            output_dir=str(self.output_dir),
            retention_seconds=retention_seconds
        )
    
    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        for directory in [self.storage_dir, self.output_dir]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, original_filename: str, prefix: str = "") -> str:
        """
        Generate a unique filename with timestamp.
        
        Args:
            original_filename: Original file name
            prefix: Optional prefix (e.g., "mapped_")
            
        Returns:
            Unique filename with timestamp
        """
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        name, ext = os.path.splitext(original_filename)
        return f"{prefix}{ts}_{name}{ext}"
    
    def save_upload(self, filename: str, data: bytes) -> Path:
        """
        Save uploaded file to storage directory.
        
        Args:
            filename: Original filename
            data: File content as bytes
            
        Returns:
            Path to saved file
        """
        unique_name = self._generate_filename(filename)
        file_path = self.storage_dir / unique_name
        
        with open(file_path, "wb") as f:
            f.write(data)
        
        logger.info(
            "File uploaded",
            original_filename=filename,
            saved_path=str(file_path),
            size_bytes=len(data)
        )
        
        return file_path
    
    def save_output(self, filename: str, data: bytes) -> Path:
        """
        Save processed output file.
        
        Args:
            filename: Output filename
            data: File content as bytes
            
        Returns:
            Path to saved file
        """
        file_path = self.output_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(data)
        
        logger.info(
            "Output file saved",
            filename=filename,
            path=str(file_path),
            size_bytes=len(data)
        )
        
        return file_path
    
    def copy_to_output(self, source_path: Path, output_filename: str) -> Path:
        """
        Copy a file to output directory.
        
        Args:
            source_path: Source file path
            output_filename: Desired output filename
            
        Returns:
            Path to copied file
        """
        dest_path = self.output_dir / output_filename
        shutil.copy2(source_path, dest_path)
        
        logger.info(
            "File copied to output",
            source=str(source_path),
            destination=str(dest_path)
        )
        
        return dest_path
    
    def get_file(self, filename: str, directory: str = "storage") -> Optional[Path]:
        """
        Get file path if exists.
        
        Args:
            filename: Filename to find
            directory: "storage" or "output"
            
        Returns:
            Path if file exists, None otherwise
        """
        base_dir = self.storage_dir if directory == "storage" else self.output_dir
        file_path = base_dir / filename
        
        if file_path.exists():
            return file_path
        return None
    
    def read_file(self, file_path: Path) -> bytes:
        """
        Read file content as bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as bytes
        """
        with open(file_path, "rb") as f:
            return f.read()
    
    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("File deleted", path=str(file_path))
                return True
        except Exception as e:
            logger.warning("Failed to delete file", path=str(file_path), error=str(e))
        return False
    
    def cleanup_old_files(self, older_than_seconds: Optional[int] = None) -> Dict[str, int]:
        """
        Clean up files older than specified seconds.
        
        Args:
            older_than_seconds: Age threshold (uses retention_seconds if not provided)
            
        Returns:
            Dict with counts of deleted files per directory
        """
        threshold = older_than_seconds or self.retention_seconds
        cutoff_time = time.time() - threshold
        deleted = {"storage": 0, "output": 0}
        
        for dir_name, directory in [("storage", self.storage_dir), ("output", self.output_dir)]:
            try:
                for file_path in Path(directory).iterdir():
                    if file_path.is_file():
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            deleted[dir_name] += 1
            except Exception as e:
                logger.warning(f"Cleanup error in {dir_name}", error=str(e))
        
        if deleted["storage"] > 0 or deleted["output"] > 0:
            logger.info(
                "Cleanup completed",
                deleted_storage=deleted["storage"],
                deleted_output=deleted["output"],
                threshold_seconds=threshold
            )
        
        return deleted
    
    def list_files(self, directory: str = "storage") -> List[Dict[str, Any]]:
        """
        List files in a directory.
        
        Args:
            directory: "storage" or "output"
            
        Returns:
            List of file info dicts
        """
        base_dir = self.storage_dir if directory == "storage" else self.output_dir
        files = []
        
        try:
            for file_path in Path(base_dir).iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(file_path)
                    })
        except Exception as e:
            logger.warning(f"Error listing {directory}", error=str(e))
        
        return files
    
    def check_write_permission(self) -> bool:
        """
        Check if storage directories are writable.
        
        Returns:
            True if writable, False otherwise
        """
        try:
            test_file = self.storage_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dict with storage stats
        """
        storage_files = self.list_files("storage")
        output_files = self.list_files("output")
        
        return {
            "storage_dir": str(self.storage_dir),
            "output_dir": str(self.output_dir),
            "storage_files_count": len(storage_files),
            "output_files_count": len(output_files),
            "storage_total_bytes": sum(f["size"] for f in storage_files),
            "output_total_bytes": sum(f["size"] for f in output_files),
            "writable": self.check_write_permission()
        }


# Global instance for easy import
local_storage = LocalStorage()


