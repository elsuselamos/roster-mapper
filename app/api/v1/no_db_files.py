"""
No-DB File Lifecycle API
=========================
Ephemeral file management without database - uses JSON metadata files.

Designed for Cloud Run with ephemeral /tmp storage.
Files and metadata are stored locally and deleted after download or TTL expiry.

Author: datnguyentien@vietjetair.com
"""

import os
import uuid
import json
import time
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Request
)
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger
from app.services.mapper import Mapper
from app.services.excel_processor import ExcelProcessor

router = APIRouter(prefix="/api/v1/no-db-files", tags=["no-db-files"])
logger = get_logger(__name__)

# Directories (ephemeral on Cloud Run)
UPLOAD_DIR = Path(getattr(settings, "STORAGE_DIR", "/tmp/uploads"))
OUTPUT_DIR = Path(getattr(settings, "OUTPUT_DIR", "/tmp/output"))
META_DIR = Path(getattr(settings, "META_DIR", "/tmp/meta"))

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
MAX_UPLOAD_SIZE = int(getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024))  # 50MB
FILE_TTL_SECONDS = int(getattr(settings, "FILE_TTL_SECONDS", 60 * 60))  # 1 hour
CLEANUP_INTERVAL_SECONDS = 10 * 60  # Run cleanup every 10 minutes

# In-memory cache for quick lookup (non-persistent, helps performance)
_meta_cache: Dict[str, Dict[str, Any]] = {}


def _now_ts() -> int:
    """Get current timestamp."""
    return int(time.time())


def _iso_now() -> str:
    """Get current ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def secure_filename(name: str) -> str:
    """
    Sanitize filename to prevent path traversal.
    
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


def clean_for_json(value: Any) -> Any:
    """
    Clean value for JSON serialization.
    Converts datetime, NaN, and other non-serializable types to JSON-compatible types.
    
    Args:
        value: Value to clean
        
    Returns:
        JSON-serializable value
    """
    if value is None:
        return ""
    elif pd.isna(value):
        return ""
    elif isinstance(value, (pd.Timestamp, datetime)):
        try:
            if isinstance(value, pd.Timestamp):
                return value.isoformat() if pd.notna(value) else ""
            else:
                return value.isoformat() if value else ""
        except Exception:
            return ""
    elif isinstance(value, (int, float)):
        if pd.isna(value) or str(value).lower() == 'nan':
            return ""
        return value
    elif isinstance(value, dict):
        return {k: clean_for_json(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [clean_for_json(item) for item in value]
    else:
        return value


def _meta_path(file_id: str) -> Path:
    """Get path to metadata file."""
    return META_DIR / f"{file_id}.json"


def save_meta(file_id: str, meta: Dict[str, Any]) -> None:
    """
    Save metadata to JSON file.
    
    Args:
        file_id: Unique file identifier
        meta: Metadata dictionary
    """
    p = _meta_path(file_id)
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        _meta_cache[file_id] = meta
        logger.debug(f"Saved metadata for {file_id}")
    except Exception as e:
        logger.error(f"Failed to save metadata {p}: {e}", exc_info=True)
        raise


def load_meta(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Load metadata from JSON file.
    
    Args:
        file_id: Unique file identifier
        
    Returns:
        Metadata dictionary or None if not found
    """
    # Check cache first
    if file_id in _meta_cache:
        return _meta_cache[file_id]
    
    p = _meta_path(file_id)
    if not p.exists():
        return None
    
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        _meta_cache[file_id] = data
        return data
    except Exception as e:
        logger.error(f"Failed to load metadata {p}: {e}", exc_info=True)
        return None


def delete_meta_and_files(file_id: str) -> None:
    """
    Delete metadata and associated files.
    
    Args:
        file_id: Unique file identifier
    """
    meta = load_meta(file_id)
    if not meta:
        # Try to delete metadata file anyway
        p = _meta_path(file_id)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        return
    
    # Delete files
    upload_path = meta.get("upload_path")
    output_path = meta.get("output_path")
    
    for path_str in (upload_path, output_path):
        if not path_str:
            continue
        try:
            path = Path(path_str)
            if path.exists():
                if path.is_file():
                    path.unlink()
                    logger.debug(f"Deleted file: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    logger.debug(f"Deleted directory: {path}")
        except Exception as e:
            logger.warning(f"Failed to delete {path_str}: {e}")
    
    # Delete metadata file
    p = _meta_path(file_id)
    if p.exists():
        try:
            p.unlink()
            logger.debug(f"Deleted metadata: {p}")
        except Exception as e:
            logger.warning(f"Failed to delete metadata {p}: {e}")
    
    # Remove from cache
    _meta_cache.pop(file_id, None)


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    station: Optional[str] = Form(None)
) -> JSONResponse:
    """
    Upload a roster file.
    
    Returns upload_id and preview placeholder.
    Client should call /map with upload_id to run mapping.
    
    Args:
        file: Excel file to upload
        station: Optional station code
        
    Returns:
        JSON with upload_id, filename, and preview
    """
    upload_id = None
    saved_path = None
    
    try:
        # Read file content
        content = await file.read()
        size = len(content)
        
        if size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB)"
            )
        
        # Sanitize filename
        orig_name = secure_filename(file.filename or "upload")
        
        # Generate upload_id
        upload_id = str(uuid.uuid4())
        
        # Save file
        saved_name = f"{upload_id}_{orig_name}"
        saved_path = UPLOAD_DIR / saved_name
        
        try:
            with saved_path.open("wb") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to save upload: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed saving upload: {e}")
        
        # Get sheet names for preview
        processor = ExcelProcessor()
        sheets = []
        try:
            sheets = processor.get_sheet_names(saved_path)
        except Exception as e:
            logger.warning(f"Failed to read sheets: {e}", exc_info=True)
            sheets = []
        
        # Create metadata
        created_at = _iso_now()
        expires_at = _now_ts() + FILE_TTL_SECONDS
        
        meta = {
            "upload_id": upload_id,
            "filename": orig_name,
            "upload_path": str(saved_path),
            "station": station,
            "created_at": created_at,
            "expires_at": expires_at,
            "status": "uploaded",
            "sheets": sheets,
            "file_size": size
        }
        
        try:
            save_meta(upload_id, meta)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}", exc_info=True)
            # Continue anyway, metadata is not critical for upload
        
        logger.info(
            "file_uploaded",
            extra={
                "upload_id": upload_id,
                "filename": orig_name,
                "station": station,
                "size": size
            }
        )
        
        # Generate preview (first 10 rows of first sheet)
        preview = {"sheets": sheets, "note": "Preview not implemented in this endpoint"}
        if sheets:
            try:
                df = processor.read_workbook(saved_path, sheets[0])
                # Convert to dict and clean all values for JSON serialization
                rows_dict = df.head(10).to_dict(orient="records")
                # Clean up all values (NaN, datetime, etc.)
                cleaned_rows = []
                for row in rows_dict:
                    cleaned_row = {k: clean_for_json(v) for k, v in row.items()}
                    cleaned_rows.append(cleaned_row)
                preview["rows_sample"] = cleaned_rows
                preview["headers"] = [str(h) for h in df.columns]  # Ensure headers are strings
            except Exception as e:
                logger.warning(f"Failed to generate preview: {e}", exc_info=True)
                # Preview is optional, continue without it
        
        # Prepare response
        response_data = {
            "success": True,
            "upload_id": upload_id,
            "filename": orig_name,
            "file_size": size,
            "sheets": sheets,
            "preview": preview,
            "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
        }
        
        # Final check - ensure all data is JSON serializable
        try:
            json.dumps(response_data)  # Test serialization
        except Exception as e:
            logger.error(f"Response data not JSON serializable: {e}", exc_info=True)
            # Remove preview if it causes issues
            response_data["preview"] = {"sheets": sheets, "note": "Preview unavailable"}
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_file: {e}", exc_info=True)
        # Clean up on error
        if saved_path and saved_path.exists():
            try:
                saved_path.unlink()
            except Exception:
                pass
        if upload_id:
            try:
                delete_meta_and_files(upload_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/map")
def map_file(
    request: Request,
    upload_id: str = Form(...),
    station: str = Form(...),
    download_mode: str = Form("styled")
) -> JSONResponse:
    """
    Run mapping on a previously uploaded file.
    
    Returns file_id and download_url.
    
    Note: For large files, this may take several minutes. Please be patient.
    
    Args:
        upload_id: Upload ID from /upload endpoint
        station: Station code (required)
        download_mode: "styled" or "plain" (default: "styled")
        
    Returns:
        JSON with file_id and download_url
    """
    import time
    start_time = time.time()
    
    logger.info(f"Mapping started for upload_id={upload_id}, station={station}, mode={download_mode}")
    
    # Load metadata
    meta = load_meta(upload_id)
    if not meta:
        raise HTTPException(status_code=404, detail="upload_id not found")
    
    upload_path = meta.get("upload_path")
    if not upload_path or not os.path.exists(upload_path):
        raise HTTPException(status_code=404, detail="upload file not found on server")
    
    # Prepare input path (convert xls -> xlsx if needed)
    input_path = upload_path
    suffix = Path(upload_path).suffix.lower()
    
    if suffix == ".xls":
        try:
            from app.utils.xls_converter import convert_xls_to_xlsx
            input_path = convert_xls_to_xlsx(upload_path)
        except Exception as e:
            logger.error(f"xls conversion failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"xls -> xlsx conversion failed: {e}")
    
    # Create unique file_id and output filename
    file_id = str(uuid.uuid4())
    out_basename = f"{file_id}_mapped.xlsx"
    output_path = OUTPUT_DIR / out_basename
    
    # Update meta status
    meta.update({
        "status": "mapping",
        "file_id": file_id,
        "output_path": str(output_path),
        "mapping_started_at": _iso_now(),
        "station": station,
        "download_mode": download_mode
    })
    save_meta(upload_id, meta)
    
    # Process file
    processor = ExcelProcessor()
    mapper = Mapper(station=station)
    
    try:
        sheets = meta.get("sheets", [])
        if not sheets:
            sheets = processor.get_sheet_names(upload_path)
            if not sheets:
                raise HTTPException(status_code=400, detail="No sheets found in file")
        
        if download_mode == "styled":
            # Preserve formatting
            output_filename = f"{file_id}_mapped.xlsx"
            output_path = OUTPUT_DIR / output_filename
            
            # Copy uploaded file to output location first
            shutil.copy2(upload_path, output_path)
            
            # Map workbook preserving styles
            stats = processor.map_workbook_preserve_style(
                source_path=upload_path,
                dest_path=output_path,
                mapper_func=mapper.map_cell,
                sheet_names=sheets
            )
            
            logger.info(
                "mapping_complete",
                extra={
                    "file_id": file_id,
                    "upload_id": upload_id,
                    "output": str(output_path),
                    "stats": stats,
                    "mode": "styled"
                }
            )
            
        else:
            # Plain mode (text only)
            output_filename = f"{file_id}_plain_mapped.xlsx"
            output_path = OUTPUT_DIR / output_filename
            
            # Read all sheets and map
            all_data = {}
            for sheet_name in sheets:
                df = processor.read_workbook(upload_path, sheet_name)
                # Map all cells
                for col in df.columns:
                    df[col] = df[col].apply(lambda x: mapper.map_cell(str(x)) if pd.notna(x) else x)
                all_data[sheet_name] = df
            
            # Write to output
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in all_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            stats = {"sheets_processed": len(sheets), "mode": "plain"}
            logger.info(
                "mapping_complete",
                extra={
                    "file_id": file_id,
                    "upload_id": upload_id,
                    "output": str(output_path),
                    "stats": stats,
                    "mode": "plain"
                }
            )
        
        # Update metadata
        meta.update({
            "status": "ready",
            "mapping_finished_at": _iso_now(),
            "output_path": str(output_path),
            "expires_at": _now_ts() + FILE_TTL_SECONDS
        })
        save_meta(upload_id, meta)
        
        # Also save metadata keyed by file_id for easier download lookup
        file_meta = {
            "file_id": file_id,
            "upload_id": upload_id,
            "upload_path": meta.get("upload_path"),
            "output_path": str(output_path),
            "station": station,
            "created_at": meta.get("created_at"),
            "mapped_at": meta.get("mapping_finished_at"),
            "expires_at": meta.get("expires_at"),
            "status": "ready",
            "download_mode": download_mode
        }
        save_meta(file_id, file_meta)
        
        download_url = f"/api/v1/no-db-files/download/{file_id}"
        
        elapsed_time = time.time() - start_time
        logger.info(f"Mapping completed in {elapsed_time:.2f} seconds for file_id={file_id}")
        
        return JSONResponse(content={
            "success": True,
            "file_id": file_id,
            "download_url": download_url,
            "output_filename": output_filename,
            "expires_at": datetime.fromtimestamp(
                meta.get("expires_at", _now_ts() + FILE_TTL_SECONDS),
                tz=timezone.utc
            ).isoformat(),
            "processing_time_seconds": round(elapsed_time, 2)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mapping failed: {e}", exc_info=True)
        meta.update({
            "status": "error",
            "error": str(e),
            "mapping_finished_at": _iso_now()
        })
        save_meta(upload_id, meta)
        raise HTTPException(status_code=500, detail=f"Mapping failed: {e}")


@router.get("/download/{file_id}")
def download_file(
    file_id: str,
    background_tasks: BackgroundTasks
) -> FileResponse:
    """
    Stream mapped output and delete upload+output+meta after response completes.
    
    Args:
        file_id: File ID from /map endpoint
        background_tasks: FastAPI background tasks
        
    Returns:
        FileResponse with file stream
    """
    meta = load_meta(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="file_id not found")
    
    output_path = meta.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    # Add deletion background task - runs after response finishes sending
    background_tasks.add_task(delete_meta_and_files, file_id)
    
    # Also delete upload_id metadata if different
    upload_id = meta.get("upload_id")
    if upload_id and upload_id != file_id:
        background_tasks.add_task(delete_meta_and_files, upload_id)
    
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache"
    }
    
    logger.info(
        "file_download_started",
        extra={
            "file_id": file_id,
            "upload_id": upload_id
        }
    )
    
    return FileResponse(
        path=output_path,
        filename=os.path.basename(output_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=background_tasks,
        headers=headers
    )


@router.get("/status/{file_id}")
def status(file_id: str) -> JSONResponse:
    """
    Return metadata/status for a given file_id or upload_id.
    
    Args:
        file_id: File ID or upload ID
        
    Returns:
        JSON with metadata
    """
    meta = load_meta(file_id)
    if meta:
        return JSONResponse(content=meta)
    
    raise HTTPException(status_code=404, detail="not found")


# Periodic cleanup background task
_cleanup_task_started = False
_cleanup_task = None


async def _cleanup_loop():
    """Periodic cleanup loop to remove expired files."""
    global _cleanup_task_started
    
    while True:
        try:
            now = _now_ts()
            deleted_count = 0
            
            # Check all metadata files
            for meta_file in META_DIR.glob("*.json"):
                try:
                    with meta_file.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    expires = data.get("expires_at", 0)
                    if expires and expires < now:
                        # Delete associated files
                        fid = data.get("file_id") or data.get("upload_id")
                        if fid:
                            delete_meta_and_files(fid)
                            deleted_count += 1
                            logger.info(f"Cleaned up expired file: {fid}")
                except Exception as e:
                    logger.warning(f"Error processing metadata file {meta_file}: {e}")
                    # Try to remove malformed metadata
                    try:
                        meta_file.unlink()
                    except Exception:
                        pass
            
            if deleted_count > 0:
                logger.info(f"Cleanup completed: deleted {deleted_count} expired files")
            
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}", exc_info=True)
        
        # Sleep interval
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


def start_cleanup_task():
    """Start the periodic cleanup task."""
    global _cleanup_task_started, _cleanup_task
    
    if _cleanup_task_started:
        return
    
    _cleanup_task_started = True
    try:
        loop = asyncio.get_event_loop()
        _cleanup_task = loop.create_task(_cleanup_loop())
        logger.info("Started no-DB cleanup task")
    except Exception as e:
        logger.error(f"Failed to start cleanup task: {e}", exc_info=True)
        _cleanup_task_started = False

