"""
Database Models
===============
SQLAlchemy models for Roster Mapper.

Author: datnguyentien@vietjetair.com
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    JSON,
    Index,
    ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class MappingVersion(Base):
    """
    Stores mapping versions for each station.
    
    Each station can have multiple mapping versions,
    with one marked as the current active version.
    """
    
    __tablename__ = "mapping_versions"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    station: str = Column(String(10), nullable=False, index=True)
    version: str = Column(String(50), nullable=False)
    mappings: dict = Column(JSON, nullable=False)
    entry_count: int = Column(Integer, nullable=False, default=0)
    is_active: bool = Column(Boolean, nullable=False, default=True)
    created_by: Optional[str] = Column(String(255), nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes: Optional[str] = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("ix_mapping_station_version", "station", "version", unique=True),
        Index("ix_mapping_station_active", "station", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<MappingVersion(station={self.station}, version={self.version}, entries={self.entry_count})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "station": self.station,
            "version": self.version,
            "entry_count": self.entry_count,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes
        }


class AuditLog(Base):
    """
    Audit log for tracking all system actions.
    
    Records uploads, mapping changes, and administrative actions.
    """
    
    __tablename__ = "audit_logs"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    timestamp: datetime = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    action: str = Column(String(50), nullable=False, index=True)
    entity_type: Optional[str] = Column(String(50), nullable=True)
    entity_id: Optional[str] = Column(String(255), nullable=True)
    station: Optional[str] = Column(String(10), nullable=True, index=True)
    user: Optional[str] = Column(String(255), nullable=True)
    ip_address: Optional[str] = Column(String(45), nullable=True)
    details: Optional[dict] = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("ix_audit_timestamp_action", "timestamp", "action"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, timestamp={self.timestamp})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "station": self.station,
            "user": self.user,
            "ip_address": self.ip_address,
            "details": self.details
        }


class UploadMeta(Base):
    """
    Metadata for uploaded files.
    
    Tracks uploaded files and their processing status.
    """
    
    __tablename__ = "upload_meta"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    file_id: str = Column(String(36), nullable=False, unique=True, index=True)
    original_filename: str = Column(String(255), nullable=False)
    file_size: int = Column(Integer, nullable=False)
    content_type: Optional[str] = Column(String(100), nullable=True)
    station: Optional[str] = Column(String(10), nullable=True)
    sheet_names: Optional[list] = Column(JSON, nullable=True)
    status: str = Column(String(20), nullable=False, default="uploaded")
    processed_at: Optional[datetime] = Column(DateTime, nullable=True)
    uploaded_by: Optional[str] = Column(String(255), nullable=True)
    uploaded_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Optional[datetime] = Column(DateTime, nullable=True)
    processing_stats: Optional[dict] = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("ix_upload_status", "status"),
        Index("ix_upload_station", "station"),
    )
    
    def __repr__(self) -> str:
        return f"<UploadMeta(file_id={self.file_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "station": self.station,
            "sheet_names": self.sheet_names,
            "status": self.status,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "processing_stats": self.processing_stats
        }


# Status constants for UploadMeta
class UploadStatus:
    """Constants for upload status values."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


# Action constants for AuditLog
class AuditAction:
    """Constants for audit action types."""
    FILE_UPLOADED = "file_uploaded"
    FILE_PROCESSED = "file_processed"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"
    MAPPING_CREATED = "mapping_created"
    MAPPING_UPDATED = "mapping_updated"
    MAPPING_DELETED = "mapping_deleted"
    MAPPING_IMPORTED = "mapping_imported"


class ProcessedFile(Base):
    """
    Metadata for processed/mapped files.
    
    Tracks output files and their lifecycle for ephemeral storage.
    Links to UploadMeta via upload_id (file_id from upload).
    """
    
    __tablename__ = "processed_files"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    file_id: str = Column(String(36), nullable=False, unique=True, index=True)
    upload_id: str = Column(String(36), nullable=False, index=True)  # Links to UploadMeta.file_id
    upload_path: str = Column(String(512), nullable=False)  # Full path to uploaded file
    output_path: str = Column(String(512), nullable=False)  # Full path to processed file
    output_path_plain: Optional[str] = Column(String(512), nullable=True)  # Plain format path if exists
    station: str = Column(String(10), nullable=False)
    format_type: str = Column(String(20), nullable=False, default="styled")  # "styled" or "plain"
    status: str = Column(String(20), nullable=False, default="ready")  # "ready", "downloading", "deleted"
    file_size: int = Column(Integer, nullable=False, default=0)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    downloaded_at: Optional[datetime] = Column(DateTime, nullable=True)
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)
    expires_at: Optional[datetime] = Column(DateTime, nullable=True, index=True)
    
    __table_args__ = (
        Index("ix_processed_status", "status"),
        Index("ix_processed_expires", "expires_at"),
        Index("ix_processed_upload", "upload_id"),
    )
    
    def __repr__(self) -> str:
        return f"<ProcessedFile(file_id={self.file_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "upload_id": self.upload_id,
            "upload_path": self.upload_path,
            "output_path": self.output_path,
            "output_path_plain": self.output_path_plain,
            "station": self.station,
            "format_type": self.format_type,
            "status": self.status,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# Status constants for ProcessedFile
class ProcessedFileStatus:
    """Constants for processed file status values."""
    READY = "ready"
    DOWNLOADING = "downloading"
    DELETED = "deleted"
    EXPIRED = "expired"
