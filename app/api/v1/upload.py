"""
Upload API Endpoints
====================
Handles file upload and processing for roster mapping.

Author: datnguyentien@vietjetair.com
"""

from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.mapper import Mapper
from app.services.excel_processor import ExcelProcessor
from app.services.storage import StorageService

router = APIRouter()
logger = get_logger(__name__)


# Response Models
class UploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    message: str
    file_id: str
    filename: str
    sheets: List[str]


class PreviewResponse(BaseModel):
    """Response model for sheet preview."""
    sheet_name: str
    headers: List[str]
    rows: List[List[str]]
    total_rows: int


class ProcessResponse(BaseModel):
    """Response model for file processing."""
    success: bool
    message: str
    download_url: str
    stats: dict


class StationInfo(BaseModel):
    """Station information model."""
    code: str
    name: str
    has_mapping: bool


# Endpoints
@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="Excel file to upload (.xlsx, .xls)")
) -> UploadResponse:
    """
    Upload an Excel roster file for processing.
    
    Accepts .xlsx and .xls files. Returns file ID and available sheets.
    """
    logger.info("File upload started", filename=file.filename)
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    allowed_extensions = {".xlsx", ".xls"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save uploaded file
        storage = StorageService()
        file_id, saved_path = await storage.save_uploaded_file(file)
        
        # Get sheet names
        processor = ExcelProcessor()
        sheets = processor.get_sheet_names(saved_path)
        
        logger.info(
            "File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            sheets=sheets
        )
        
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            sheets=sheets
        )
        
    except Exception as e:
        logger.error("File upload failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/preview/{file_id}", response_model=PreviewResponse)
async def preview_sheet(
    file_id: str,
    sheet: str = Query(..., description="Sheet name to preview"),
    rows: int = Query(10, ge=1, le=100, description="Number of rows to preview")
) -> PreviewResponse:
    """
    Preview a sheet from an uploaded file.
    
    Returns headers and sample rows for verification before processing.
    """
    logger.info("Preview requested", file_id=file_id, sheet=sheet)
    
    try:
        storage = StorageService()
        file_path = storage.get_uploaded_file_path(file_id)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        processor = ExcelProcessor()
        preview_data = processor.preview_sheet(file_path, sheet, max_rows=rows)
        
        return PreviewResponse(
            sheet_name=sheet,
            headers=preview_data["headers"],
            rows=preview_data["rows"],
            total_rows=preview_data["total_rows"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Preview failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.post("/process/{file_id}", response_model=ProcessResponse)
async def process_file(
    file_id: str,
    sheet: str = Form(..., description="Sheet name to process"),
    station: Optional[str] = Form(None, description="Station code (auto-detect if not provided)"),
    columns: Optional[str] = Form(None, description="Comma-separated column names to map")
) -> ProcessResponse:
    """
    Process an uploaded file with roster code mapping.
    
    Maps roster codes in specified columns using station-specific or global mappings.
    """
    logger.info(
        "Processing started",
        file_id=file_id,
        sheet=sheet,
        station=station
    )
    
    try:
        storage = StorageService()
        file_path = storage.get_uploaded_file_path(file_id)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Auto-detect station if needed
        if not station and settings.AUTO_DETECT_STATION:
            station = _detect_station_from_file(file_path)
        
        station = station or "global"
        
        # Load mapping
        mapper = Mapper(station)
        
        # Process Excel file
        processor = ExcelProcessor()
        df = processor.read_workbook(file_path, sheet)
        
        # Determine columns to map
        target_columns = columns.split(",") if columns else _detect_code_columns(df)
        
        # Apply mapping
        mapped_df, stats = mapper.map_dataframe(df, target_columns)
        
        # Save processed file
        output_path = storage.save_processed_file(file_id, mapped_df)
        download_url = f"/api/v1/download/{file_id}"
        
        logger.info(
            "Processing completed",
            file_id=file_id,
            station=station,
            mapped_cells=stats["mapped_cells"]
        )
        
        return ProcessResponse(
            success=True,
            message="File processed successfully",
            download_url=download_url,
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Processing failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(file_id: str) -> FileResponse:
    """
    Download a processed file.
    
    Returns the mapped Excel file for download.
    """
    storage = StorageService()
    output_path = storage.get_processed_file_path(file_id)
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Processed file not found")
    
    return FileResponse(
        path=output_path,
        filename=f"mapped_{file_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/stations", response_model=List[StationInfo])
async def list_stations() -> List[StationInfo]:
    """
    List available stations and their mapping status.
    """
    stations = [
        ("SGN", "Tân Sơn Nhất"),
        ("HAN", "Nội Bài"),
        ("DAD", "Đà Nẵng"),
        ("CXR", "Cam Ranh"),
        ("HPH", "Cát Bi"),
        ("VCA", "Cần Thơ"),
        ("VII", "Vinh"),
    ]
    
    storage = StorageService()
    
    return [
        StationInfo(
            code=code,
            name=name,
            has_mapping=storage.mapping_exists(code)
        )
        for code, name in stations
    ]


# Helper functions
def _detect_station_from_file(file_path: Path) -> Optional[str]:
    """
    Attempt to detect station code from filename or content.
    
    Args:
        file_path: Path to the uploaded file.
        
    Returns:
        Station code if detected, None otherwise.
    """
    filename = file_path.stem.upper()
    
    station_codes = ["SGN", "HAN", "DAD", "CXR", "HPH", "VCA", "VII"]
    
    for code in station_codes:
        if code in filename:
            return code
    
    return None


def _detect_code_columns(df) -> List[str]:
    """
    Detect columns likely to contain roster codes.
    
    Args:
        df: pandas DataFrame to analyze.
        
    Returns:
        List of column names likely containing codes.
    """
    code_keywords = ["code", "mã", "roster", "duty", "activity"]
    
    detected = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in code_keywords):
            detected.append(col)
    
    return detected if detected else list(df.columns[:3])

