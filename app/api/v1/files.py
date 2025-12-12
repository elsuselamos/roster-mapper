"""
Ephemeral File Management API
==============================
Handles upload → mapping → download with automatic file deletion.

Files are stored temporarily in /tmp and deleted after download or TTL expiry.
Designed for Cloud Run ephemeral storage.

Author: datnguyentien@vietjetair.com
"""

import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import quote

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Request,
    Query
)
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import async_session_maker
from app.db.models import (
    UploadMeta,
    ProcessedFile,
    ProcessedFileStatus,
    UploadStatus,
    AuditLog,
    AuditAction
)
from app.services.mapper import Mapper
from app.services.excel_processor import ExcelProcessor
from app.services.storage import StorageService

router = APIRouter()
logger = get_logger(__name__)

# Directories (ephemeral on Cloud Run)
UPLOAD_DIR = Path(settings.STORAGE_DIR)  # e.g. /tmp/uploads
OUTPUT_DIR = Path(settings.OUTPUT_DIR)  # e.g. /tmp/output
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
FILE_TTL_HOURS = 1  # Files expire after 1 hour
CLEANUP_INTERVAL_SECONDS = 10 * 60  # Run cleanup every 10 minutes


def secure_filename(name: str) -> str:
    """
    Sanitize filename to prevent path traversal and injection.
    
    Args:
        name: Original filename
        
    Returns:
        Sanitized filename
    """
    if not name:
        return "file"
    # Keep alphanumeric, spaces, dots, underscores, hyphens
    safe = "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()
    # Limit length
    if len(safe) > 200:
        safe = safe[:200]
    return safe or "file"


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    if request.client:
        return request.client.host
    return "unknown"


async def log_audit(
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    station: Optional[str] = None,
    user: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None
) -> None:
    """Log audit event to database."""
    try:
        async with async_session_maker() as session:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                station=station,
                user=user,
                ip_address=ip_address,
                details=details or {}
            )
            session.add(audit)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to log audit: {e}", exc_info=True)


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    station: Optional[str] = Form(None)
) -> JSONResponse:
    """
    Upload a roster file for processing.
    
    Files are stored temporarily in /tmp/uploads with UUID prefix.
    Returns upload_id for subsequent mapping request.
    
    Args:
        file: Excel file (.xlsx or .xls)
        station: Station code (optional, can be auto-detected)
        
    Returns:
        JSON with upload_id, filename, and preview info
    """
    client_ip = get_client_ip(request)
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    allowed_extensions = {".xlsx", ".xls"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # Generate upload ID and save file
    upload_id = str(uuid.uuid4())
    orig_name = secure_filename(file.filename)
    saved_name = f"{upload_id}_{orig_name}"
    saved_path = UPLOAD_DIR / saved_name
    
    try:
        saved_path.write_bytes(content)
        logger.info(
            "upload_complete",
            extra={
                "upload_id": upload_id,
                "filename": orig_name,
                "size": file_size,
                "path": str(saved_path)
            }
        )
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Get sheet names for preview
    processor = ExcelProcessor()
    try:
        sheets = processor.get_sheet_names(saved_path)
    except Exception as e:
        logger.warning(f"Failed to read sheets: {e}")
        sheets = []
    
    # Save metadata to database
    expires_at = datetime.utcnow() + timedelta(hours=FILE_TTL_HOURS)
    try:
        async with async_session_maker() as session:
            upload_meta = UploadMeta(
                file_id=upload_id,
                original_filename=orig_name,
                file_size=file_size,
                content_type=file.content_type,
                station=station,
                sheet_names=sheets,
                status=UploadStatus.UPLOADED,
                uploaded_at=datetime.utcnow(),
                expires_at=expires_at
            )
            session.add(upload_meta)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save upload metadata: {e}", exc_info=True)
        # Continue even if DB save fails
    
    # Log audit
    await log_audit(
        action=AuditAction.FILE_UPLOADED,
        entity_type="upload",
        entity_id=upload_id,
        station=station,
        ip_address=client_ip,
        details={"filename": orig_name, "size": file_size}
    )
    
    # Generate preview (first 10 rows of first sheet)
    preview = {"sheets": sheets, "rows_sample": []}
    if sheets:
        try:
            preview_data = processor.preview_sheet(saved_path, sheets[0], max_rows=10)
            preview["rows_sample"] = preview_data.get("rows", [])[:10]
            preview["headers"] = preview_data.get("headers", [])
        except Exception as e:
            logger.warning(f"Failed to generate preview: {e}")
    
    return JSONResponse(content={
        "success": True,
        "upload_id": upload_id,
        "filename": orig_name,
        "file_size": file_size,
        "sheets": sheets,
        "preview": preview,
        "expires_at": expires_at.isoformat()
    })


@router.post("/map")
async def map_file(
    request: Request,
    upload_id: str = Form(...),
    station: str = Form(...),
    download_mode: str = Form("styled")
) -> JSONResponse:
    """
    Process an uploaded file with roster mapping.
    
    Creates mapped output file(s) in /tmp/output.
    Returns file_id for download.
    
    Args:
        upload_id: Upload ID from /upload endpoint
        station: Station code for mapping
        download_mode: "styled" (preserve formatting) or "plain" (text only)
        
    Returns:
        JSON with file_id and download_url
    """
    client_ip = get_client_ip(request)
    
    # Validate download_mode
    if download_mode not in ("styled", "plain"):
        raise HTTPException(status_code=400, detail="download_mode must be 'styled' or 'plain'")
    
    # Find uploaded file
    matches = list(UPLOAD_DIR.glob(f"{upload_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Upload not found or expired")
    
    uploaded_path = matches[0]
    
    if not uploaded_path.exists():
        raise HTTPException(status_code=404, detail="Upload file not found")
    
    # Check if upload metadata exists
    async with async_session_maker() as session:
        result = await session.execute(
            select(UploadMeta).where(UploadMeta.file_id == upload_id)
        )
        upload_meta = result.scalar_one_or_none()
        
        if not upload_meta:
            raise HTTPException(status_code=404, detail="Upload metadata not found")
        
        # Update status to processing
        await session.execute(
            update(UploadMeta)
            .where(UploadMeta.file_id == upload_id)
            .values(status=UploadStatus.PROCESSING)
        )
        await session.commit()
    
    logger.info(
        "mapping_start",
        extra={
            "upload_id": upload_id,
            "file": str(uploaded_path),
            "station": station,
            "mode": download_mode
        }
    )
    
    # Generate file_id for output
    file_id = str(uuid.uuid4())
    
    # Process file based on mode
    processor = ExcelProcessor()
    mapper = Mapper(station=station)
    
    try:
        # Get selected sheets (for now, use all sheets)
        # In future, can add sheet selection parameter
        sheets = processor.get_sheet_names(uploaded_path)
        if not sheets:
            raise HTTPException(status_code=400, detail="No sheets found in file")
        
        if download_mode == "styled":
            # Preserve formatting
            output_filename = f"{file_id}_mapped.xlsx"
            output_path = OUTPUT_DIR / output_filename
            
            # Copy uploaded file to output location first
            shutil.copy2(uploaded_path, output_path)
            
            # Map workbook preserving styles
            stats = processor.map_workbook_preserve_style(
                source_path=uploaded_path,
                dest_path=output_path,
                mapper_func=mapper.map_cell,
                sheet_names=sheets
            )
            
            output_path_plain = None
            
        else:  # plain mode
            # Text-only output
            # Read and map as DataFrame
            mapped_sheets = {}
            for sheet in sheets:
                try:
                    df = processor.read_workbook(uploaded_path, sheet)
                    mapped_df, _ = mapper.map_dataframe(df)
                    mapped_sheets[sheet] = mapped_df
                except Exception as e:
                    logger.error(f"Error processing sheet {sheet}: {e}")
            
            if not mapped_sheets:
                raise HTTPException(status_code=500, detail="Failed to process any sheets")
            
            # Save multi-sheet file (plain format)
            storage = StorageService()
            output_path = storage.save_processed_file_multi_sheet(
                file_id,
                mapped_sheets,
                format_type="plain"
            )
            output_path_plain = str(output_path)
        
        # Get file size
        file_size = output_path.stat().st_size if output_path.exists() else 0
        
        logger.info(
            "mapping_complete",
            extra={
                "file_id": file_id,
                "upload_id": upload_id,
                "output": str(output_path),
                "size": file_size,
                "mode": download_mode
            }
        )
        
    except Exception as e:
        logger.error(f"mapping_error: {e}", exc_info=True)
        
        # Update status to failed
        async with async_session_maker() as session:
            await session.execute(
                update(UploadMeta)
                .where(UploadMeta.file_id == upload_id)
                .values(status=UploadStatus.FAILED)
            )
            await session.commit()
        
        raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")
    
    # Save processed file metadata
    expires_at = datetime.utcnow() + timedelta(hours=FILE_TTL_HOURS)
    try:
        async with async_session_maker() as session:
            processed_file = ProcessedFile(
                file_id=file_id,
                upload_id=upload_id,
                upload_path=str(uploaded_path),
                output_path=str(output_path),
                output_path_plain=output_path_plain,
                station=station,
                format_type=download_mode,
                status=ProcessedFileStatus.READY,
                file_size=file_size,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            session.add(processed_file)
            
            # Update upload status
            await session.execute(
                update(UploadMeta)
                .where(UploadMeta.file_id == upload_id)
                .values(
                    status=UploadStatus.COMPLETED,
                    processed_at=datetime.utcnow()
                )
            )
            
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save processed file metadata: {e}", exc_info=True)
    
    # Log audit
    await log_audit(
        action=AuditAction.FILE_PROCESSED,
        entity_type="processed_file",
        entity_id=file_id,
        station=station,
        ip_address=client_ip,
        details={"upload_id": upload_id, "mode": download_mode, "size": file_size}
    )
    
    download_url = f"/api/v1/files/download/{file_id}"
    if download_mode == "styled":
        download_url_plain = f"/api/v1/files/download/{file_id}?format=plain"
    else:
        download_url_plain = None
    
    return JSONResponse(content={
        "success": True,
        "file_id": file_id,
        "upload_id": upload_id,
        "download_url": download_url,
        "download_url_plain": download_url_plain,
        "file_size": file_size,
        "expires_at": expires_at.isoformat()
    })


def delete_file_safely(path: str, reason: str = "after_download") -> None:
    """
    Safely delete a file and log the action.
    
    Args:
        path: File path to delete
        reason: Reason for deletion (for logging)
    """
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(
                "file_deleted",
                extra={"path": path, "reason": reason}
            )
        else:
            logger.debug(f"File already deleted: {path}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(
            "delete_file_error",
            extra={"path": path, "reason": reason, "error": str(e)}
        )


@router.get("/download/{file_id}")
async def download_file(
    request: Request,
    file_id: str,
    format: str = Query("styled", description="Format: 'styled' or 'plain'"),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> FileResponse:
    """
    Download a processed file.
    
    After the file is sent to the client, both the output file
    and the original upload file are deleted via background task.
    
    Args:
        file_id: File ID from /map endpoint
        format: "styled" (default) or "plain"
        
    Returns:
        FileResponse with the mapped Excel file
    """
    client_ip = get_client_ip(request)
    
    # Get processed file metadata
    async with async_session_maker() as session:
        result = await session.execute(
            select(ProcessedFile).where(ProcessedFile.file_id == file_id)
        )
        processed_file = result.scalar_one_or_none()
        
        if not processed_file:
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        if processed_file.status == ProcessedFileStatus.DELETED:
            raise HTTPException(status_code=404, detail="File has been deleted")
        
        # Determine which file to serve
        if format == "plain" and processed_file.output_path_plain:
            output_path = Path(processed_file.output_path_plain)
        else:
            output_path = Path(processed_file.output_path)
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found on disk")
        
        # Mark as downloading (prevent concurrent downloads if needed)
        await session.execute(
            update(ProcessedFile)
            .where(ProcessedFile.file_id == file_id)
            .values(
                status=ProcessedFileStatus.DOWNLOADING,
                downloaded_at=datetime.utcnow()
            )
        )
        await session.commit()
    
    logger.info(
        "download_start",
        extra={
            "file_id": file_id,
            "format": format,
            "path": str(output_path),
            "ip": client_ip
        }
    )
    
    # Schedule deletion after response is sent
    upload_path = Path(processed_file.upload_path)
    background_tasks.add_task(
        delete_file_safely,
        str(output_path),
        "after_download"
    )
    background_tasks.add_task(
        delete_file_safely,
        str(upload_path),
        "after_download"
    )
    
    # Mark as deleted in DB (after response)
    async def mark_deleted():
        async with async_session_maker() as session:
            await session.execute(
                update(ProcessedFile)
                .where(ProcessedFile.file_id == file_id)
                .values(
                    status=ProcessedFileStatus.DELETED,
                    deleted_at=datetime.utcnow()
                )
            )
            await session.commit()
    
    background_tasks.add_task(mark_deleted)
    
    # Log audit
    await log_audit(
        action=AuditAction.FILE_DOWNLOADED,
        entity_type="processed_file",
        entity_id=file_id,
        station=processed_file.station,
        ip_address=client_ip,
        details={"format": format, "size": output_path.stat().st_size}
    )
    
    # Return file with security headers
    filename = output_path.name
    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Content-Disposition": f'attachment; filename="{quote(filename)}"'
        },
        background=background_tasks
    )


@router.get("/status/{file_id}")
async def get_file_status(file_id: str) -> JSONResponse:
    """
    Get processing status for a file.
    
    Args:
        file_id: File ID from /map endpoint
        
    Returns:
        JSON with status, file info, and download URL if ready
    """
    async with async_session_maker() as session:
        result = await session.execute(
            select(ProcessedFile).where(ProcessedFile.file_id == file_id)
        )
        processed_file = result.scalar_one_or_none()
        
        if not processed_file:
            return JSONResponse(content={
                "status": "not_found",
                "file_id": file_id,
                "message": "File not found or expired"
            })
        
        # Check if file still exists on disk
        output_path = Path(processed_file.output_path)
        file_exists = output_path.exists()
        
        return JSONResponse(content={
            "status": processed_file.status,
            "file_id": file_id,
            "upload_id": processed_file.upload_id,
            "station": processed_file.station,
            "format_type": processed_file.format_type,
            "file_size": processed_file.file_size,
            "file_exists": file_exists,
            "created_at": processed_file.created_at.isoformat(),
            "downloaded_at": processed_file.downloaded_at.isoformat() if processed_file.downloaded_at else None,
            "expires_at": processed_file.expires_at.isoformat() if processed_file.expires_at else None,
            "download_url": f"/api/v1/files/download/{file_id}" if file_exists else None
        })


async def cleanup_expired_files() -> None:
    """
    Background task to delete expired files.
    
    Runs periodically to clean up files that exceeded TTL.
    """
    logger.info("cleanup_start", extra={"upload_dir": str(UPLOAD_DIR), "output_dir": str(OUTPUT_DIR)})
    
    now = datetime.utcnow()
    deleted_count = 0
    
    # Clean up expired files from database
    async with async_session_maker() as session:
        # Find expired processed files
        result = await session.execute(
            select(ProcessedFile).where(
                ProcessedFile.expires_at < now,
                ProcessedFile.status != ProcessedFileStatus.DELETED
            )
        )
        expired_files = result.scalars().all()
        
        for pf in expired_files:
            # Delete files from disk
            if pf.output_path:
                delete_file_safely(pf.output_path, "ttl_cleanup")
            if pf.output_path_plain:
                delete_file_safely(pf.output_path_plain, "ttl_cleanup")
            if pf.upload_path:
                delete_file_safely(pf.upload_path, "ttl_cleanup")
            
            # Mark as deleted
            pf.status = ProcessedFileStatus.DELETED
            pf.deleted_at = now
            deleted_count += 1
        
        await session.commit()
    
    # Clean up orphaned files on disk (not in DB)
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for file_path in directory.glob("*"):
            if file_path.is_file():
                try:
                    file_age = datetime.utcnow().timestamp() - file_path.stat().st_mtime
                    if file_age > FILE_TTL_HOURS * 3600:
                        delete_file_safely(str(file_path), "ttl_cleanup_orphan")
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error checking file age: {e}")
    
    logger.info("cleanup_complete", extra={"deleted_count": deleted_count})


# Export cleanup function for use in main.py
__all__ = ["router", "cleanup_expired_files"]

