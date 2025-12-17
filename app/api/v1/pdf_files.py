"""
PDF Files API
=============
API endpoints for PDF upload, conversion, and mapping.

This module provides a separate API for PDF processing to avoid
interfering with existing Excel processing functionality.

Author: datnguyentien@vietjetair.com
"""

import os
import uuid
import json
import time
import shutil
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

from app.core.config import settings
from app.core.logging import get_logger
from app.services.mapper import Mapper
from app.services.excel_processor import ExcelProcessor
from app.services.compdf_service import ComPDFService

router = APIRouter(prefix="/api/v1/pdf", tags=["pdf"])
logger = get_logger(__name__)

# Log router initialization with all routes
def _log_routes():
    routes_info = []
    for route in router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else []
            })
    logger.info("PDF router initialized", prefix=router.prefix, routes=routes_info, route_count=len(routes_info))

# Log routes when module is imported
_log_routes()

# Directories
UPLOAD_DIR = settings.STORAGE_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
META_DIR = settings.META_DIR

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
MAX_UPLOAD_SIZE = int(getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024))  # 50MB
FILE_TTL_SECONDS = int(getattr(settings, "FILE_TTL_SECONDS", 60 * 60))  # 1 hour


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
    p = _meta_path(file_id)
    if not p.exists():
        return None
    
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to load metadata {p}: {e}", exc_info=True)
        return None


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    station: Optional[str] = Form(None)
) -> JSONResponse:
    """
    Upload a PDF file.
    
    Args:
        file: PDF file to upload
        station: Optional station code
        
    Returns:
        JSON with upload_id, filename, and page count
    """
    # Log immediately when endpoint is called
    logger.info("=" * 80)
    logger.info("PDF UPLOAD ENDPOINT CALLED - THIS SHOULD APPEAR IN LOGS")
    logger.info(
        "PDF upload endpoint called",
        filename=file.filename if file else None,
        station=station,
        content_type=file.content_type if file else None,
        endpoint_path="/api/v1/pdf/upload"
    )
    logger.info("=" * 80)
    upload_id = None
    saved_path = None
    
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
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
        orig_name = secure_filename(file.filename or "upload.pdf")
        
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
        
        # Get page count using pdfplumber
        page_count = 0
        try:
            import pdfplumber
            with pdfplumber.open(saved_path) as pdf:
                page_count = len(pdf.pages)
        except Exception as e:
            logger.warning(f"Failed to get page count: {e}", exc_info=True)
        
        # Create metadata
        created_at = _iso_now()
        expires_at = _now_ts() + FILE_TTL_SECONDS
        
        meta = {
            "file_id": upload_id,
            "upload_id": upload_id,
            "upload_path": str(saved_path),
            "filename": orig_name,
            "file_type": "pdf",
            "size": size,
            "page_count": page_count,
            "station": station or "HAN",
            "created_at": created_at,
            "expires_at": expires_at,
            "status": "uploaded"
        }
        
        save_meta(upload_id, meta)
        
        logger.info(
            "PDF uploaded successfully",
            upload_id=upload_id,
            filename=orig_name,
            size=size,
            pages=page_count,
            station=station or "HAN"
        )
        
        response_data = {
            "upload_id": upload_id,
            "filename": orig_name,
            "file_type": "pdf",
            "size": size,
            "page_count": page_count,
            "station": station or "HAN",
            "status": "uploaded"
        }
        
        logger.debug("Returning upload response", response_data=response_data)
        
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        # Cleanup on error
        if saved_path and saved_path.exists():
            try:
                saved_path.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/convert")
async def convert_pdf_to_excel(
    upload_id: str = Form(...),
    sheet_name: str = Form("Sheet1"),
    merge_pages: str = Form("true")
) -> JSONResponse:
    """
    Convert PDF to Excel.
    
    Args:
        upload_id: Upload ID from /upload endpoint
        sheet_name: Name for Excel sheet
        merge_pages: If True, merge all pages into single sheet
        
    Returns:
        JSON with converted Excel file info
    """
    try:
        # Load metadata
        meta = load_meta(upload_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        pdf_path = Path(meta["upload_path"])
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Generate output path
        excel_file_id = str(uuid.uuid4())
        excel_path = OUTPUT_DIR / f"{excel_file_id}_converted.xlsx"
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert merge_pages string to boolean
        merge_pages_bool = merge_pages.lower() in ("true", "1", "yes", "on")
        
        # Use ComPDF API to convert PDF to Excel (only method)
        compdf_service = ComPDFService()
        
        # Determine worksheet option based on merge_pages
        # e_ForDocument: One worksheet for entire document (merge all pages)
        # e_ForPage: One worksheet per PDF page
        excel_worksheet_option = "e_ForDocument" if merge_pages_bool else "e_ForPage"
        
        logger.info(
            "Converting PDF to Excel using ComPDF API",
            pdf_path=str(pdf_path),
            excel_path=str(excel_path),
            merge_pages=merge_pages_bool,
            worksheet_option=excel_worksheet_option
        )
        
        # Perform conversion using ComPDF API
        conversion_result = compdf_service.convert_pdf_to_excel(
            pdf_path=pdf_path,
            output_path=excel_path,
            enable_ai_layout=True,
            is_contain_img=True,
            is_contain_annot=True,
            enable_ocr=False,
            ocr_language="AUTO",
            page_ranges=None,  # Convert all pages
            excel_all_content=True,
            excel_worksheet_option=excel_worksheet_option
        )
        
        # Create stats compatible with old format
        stats = {
            "pages_processed": meta.get("page_count", 0),
            "tables_found": 0,  # Not available from API
            "total_rows": 0,  # Will be determined after loading Excel
            "total_cols": 0,  # Will be determined after loading Excel
            "excel_path": str(excel_path),
            "task_id": conversion_result.get("task_id"),
            "task_cost": conversion_result.get("task_cost", 0),
            "task_time": conversion_result.get("task_time", 0),
            "conversion_method": "compdf_api"
        }
        
        # Try to get actual row/col counts from Excel file
        try:
            processor = ExcelProcessor()
            sheet_names = processor.get_sheet_names(excel_path)
            if sheet_names:
                # Read first sheet to get dimensions
                df = processor.read_sheet(excel_path, sheet_names[0])
                stats["total_rows"] = len(df)
                stats["total_cols"] = len(df.columns)
                stats["sheets"] = sheet_names
        except Exception as e:
            logger.warning(f"Could not read Excel dimensions: {e}")
        
        # Update metadata
        meta["converted_excel_id"] = excel_file_id
        meta["converted_excel_path"] = str(excel_path)
        meta["conversion_stats"] = stats
        meta["status"] = "converted"
        save_meta(upload_id, meta)
        
        # Create separate metadata for Excel file
        excel_meta = {
            "file_id": excel_file_id,
            "upload_id": upload_id,
            "source_pdf_path": str(pdf_path),
            "excel_path": str(excel_path),
            "filename": f"{meta['filename']}.xlsx",
            "file_type": "excel",
            "sheet_name": sheet_name,
            "station": meta.get("station", "HAN"),
            "created_at": _iso_now(),
            "expires_at": _now_ts() + FILE_TTL_SECONDS,
            "status": "ready"
        }
        save_meta(excel_file_id, excel_meta)
        
        logger.info(
            "PDF converted to Excel",
            upload_id=upload_id,
            excel_id=excel_file_id,
            **stats
        )
        
        return JSONResponse({
            "upload_id": upload_id,
            "excel_id": excel_file_id,
            "excel_path": str(excel_path),
            "filename": excel_meta["filename"],
            "conversion_stats": stats,
            "status": "converted"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/map")
async def map_pdf(
    upload_id: str = Form(...),
    station: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None)
) -> JSONResponse:
    """
    Apply mapping to converted Excel file from PDF.
    
    This endpoint:
    1. Loads the converted Excel file
    2. Applies mapping using Mapper service
    3. Returns mapped Excel file for download
    
    Args:
        upload_id: Upload ID from /upload endpoint
        station: Station code for mapping (uses metadata if not provided)
        sheet_name: Sheet name to process (uses first sheet if not provided)
        
    Returns:
        JSON with mapped file info and download URL
    """
    try:
        # Load metadata
        meta = load_meta(upload_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Get Excel file path
        excel_id = meta.get("converted_excel_id")
        if not excel_id:
            raise HTTPException(
                status_code=400,
                detail="PDF not converted yet. Call /convert first."
            )
        
        excel_meta = load_meta(excel_id)
        if not excel_meta:
            raise HTTPException(status_code=404, detail="Converted Excel file not found")
        
        excel_path = Path(excel_meta["excel_path"])
        if not excel_path.exists():
            raise HTTPException(status_code=404, detail="Excel file not found")
        
        # Get station
        station = station or meta.get("station") or "HAN"
        
        # Get sheet name
        processor = ExcelProcessor()
        available_sheets = processor.get_sheet_names(excel_path)
        
        if not available_sheets:
            raise HTTPException(status_code=400, detail="No sheets found in Excel file")
        
        target_sheet = sheet_name or available_sheets[0]
        if target_sheet not in available_sheets:
            raise HTTPException(
                status_code=400,
                detail=f"Sheet '{target_sheet}' not found. Available: {available_sheets}"
            )
        
        # Initialize mapper
        mapper = Mapper(station=station)
        
        # Generate output path for mapped file
        mapped_file_id = str(uuid.uuid4())
        mapped_path = OUTPUT_DIR / f"{mapped_file_id}_mapped.xlsx"
        mapped_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Apply mapping with style preservation
        stats = processor.map_workbook_preserve_style(
            source_path=excel_path,
            dest_path=mapped_path,
            mapper_func=mapper.map_cell,
            sheet_names=[target_sheet]
        )
        
        # Create metadata for mapped file
        mapped_meta = {
            "file_id": mapped_file_id,
            "upload_id": upload_id,
            "excel_id": excel_id,
            "source_excel_path": str(excel_path),
            "mapped_path": str(mapped_path),
            "filename": f"{meta['filename']}_mapped.xlsx",
            "file_type": "excel",
            "station": station,
            "sheet_name": target_sheet,
            "mapping_stats": stats,
            "created_at": _iso_now(),
            "expires_at": _now_ts() + FILE_TTL_SECONDS,
            "status": "mapped"
        }
        save_meta(mapped_file_id, mapped_meta)
        
        logger.info(
            "PDF mapped successfully",
            upload_id=upload_id,
            mapped_id=mapped_file_id,
            station=station,
            **stats
        )
        
        return JSONResponse({
            "upload_id": upload_id,
            "mapped_file_id": mapped_file_id,
            "filename": mapped_meta["filename"],
            "download_url": f"/api/v1/pdf/download/{mapped_file_id}",
            "station": station,
            "sheet_name": target_sheet,
            "mapping_stats": stats,
            "status": "mapped"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mapping error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(file_id: str) -> FileResponse:
    """
    Download processed file (Excel or mapped Excel).
    
    Args:
        file_id: File ID from conversion or mapping
        
    Returns:
        File download response
    """
    meta = load_meta(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = None
    
    # Check for mapped file first
    if "mapped_path" in meta:
        file_path = Path(meta["mapped_path"])
    elif "excel_path" in meta:
        file_path = Path(meta["excel_path"])
    elif "upload_path" in meta:
        file_path = Path(meta["upload_path"])
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    filename = meta.get("filename", file_path.name)
    
    logger.info(f"Downloading file: {file_id}, path: {file_path}")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/status/{upload_id}")
async def get_status(upload_id: str) -> JSONResponse:
    """
    Get status of PDF processing.
    
    Args:
        upload_id: Upload ID
        
    Returns:
        JSON with current status and file info
    """
    meta = load_meta(upload_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    response = {
        "upload_id": upload_id,
        "status": meta.get("status", "unknown"),
        "filename": meta.get("filename"),
        "file_type": meta.get("file_type"),
        "page_count": meta.get("page_count"),
        "station": meta.get("station"),
        "created_at": meta.get("created_at")
    }
    
    # Add conversion info if available
    if "converted_excel_id" in meta:
        response["converted"] = True
        response["excel_id"] = meta["converted_excel_id"]
        response["conversion_stats"] = meta.get("conversion_stats")
    
    # Add mapping info if available
    excel_id = meta.get("converted_excel_id")
    if excel_id:
        excel_meta = load_meta(excel_id)
        if excel_meta and "mapped_file_id" in excel_meta:
            response["mapped"] = True
            response["mapped_file_id"] = excel_meta["mapped_file_id"]
    
    return JSONResponse(response)

