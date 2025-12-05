"""
Batch Processing API
====================
Handle multiple file uploads and batch mapping.

Author: datnguyentien@vietjetair.com
"""

import io
import zipfile
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.mapper import Mapper
from app.services.storage import StorageService
from app.services.excel_processor import ExcelProcessor

router = APIRouter()
logger = get_logger(__name__)


class BatchFileResult(BaseModel):
    """Result for a single file in batch."""
    filename: str
    station: str
    success: bool
    mapped_cells: int = 0
    unchanged_cells: int = 0
    error: Optional[str] = None


class BatchResponse(BaseModel):
    """Response for batch processing."""
    success: bool
    message: str
    total_files: int
    successful_files: int
    failed_files: int
    results: List[BatchFileResult]
    download_url: Optional[str] = None


@router.post("/batch-upload", response_model=BatchResponse)
async def batch_upload(
    files: List[UploadFile] = File(..., description="Multiple Excel files"),
    station: Optional[str] = Form(None, description="Common station for all files"),
    auto_detect: bool = Form(True, description="Auto-detect station from filename")
):
    """
    Upload multiple files for batch processing.
    
    Returns individual results and a ZIP download URL.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    logger.info(f"Batch upload started: {len(files)} files")
    
    storage = StorageService()
    processor = ExcelProcessor()
    
    results = []
    output_paths = []
    
    for file in files:
        if not file.filename:
            continue
        
        # Detect station
        file_station = station
        if auto_detect or not station:
            detected = _detect_station(file.filename)
            file_station = detected or station or "global"
        
        try:
            # Save uploaded file
            file_id, file_path = await storage.save_uploaded_file(file)
            
            # Get first sheet
            sheets = processor.get_sheet_names(file_path)
            if not sheets:
                raise ValueError("No sheets found in file")
            
            # Load mapper
            mapper = Mapper(station=file_station)
            
            # Read and map
            df = processor.read_workbook(file_path, sheets[0])
            mapped_df, stats = mapper.map_dataframe(df)
            
            # Save output
            output_path = storage.save_processed_file(file_id, mapped_df)
            output_paths.append((file.filename, output_path))
            
            results.append(BatchFileResult(
                filename=file.filename,
                station=file_station,
                success=True,
                mapped_cells=stats["mapped_cells"],
                unchanged_cells=stats["unchanged_cells"]
            ))
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            results.append(BatchFileResult(
                filename=file.filename,
                station=file_station or "unknown",
                success=False,
                error=str(e)
            ))
    
    # Create ZIP if multiple successful files
    download_url = None
    successful = [r for r in results if r.success]
    
    if len(successful) > 0:
        # Create batch ZIP
        zip_path = settings.TEMP_DIR / "batch_output.zip"
        _create_zip(output_paths, zip_path)
        download_url = "/api/v1/batch-download"
    
    return BatchResponse(
        success=len(successful) > 0,
        message=f"Processed {len(results)} files",
        total_files=len(results),
        successful_files=len(successful),
        failed_files=len(results) - len(successful),
        results=results,
        download_url=download_url
    )


@router.post("/batch-map")
async def batch_map(
    files: List[UploadFile] = File(...),
    station: Optional[str] = Form(None),
    auto_detect: bool = Form(True),
    return_zip: bool = Form(True)
):
    """
    Batch map multiple files and return ZIP.
    
    Accepts multiple files, processes each with station-specific mapping,
    and returns a ZIP archive of all mapped files.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    storage = StorageService()
    processor = ExcelProcessor()
    
    output_files = []
    errors = []
    
    for file in files:
        if not file.filename:
            continue
        
        # Detect station
        file_station = station
        if auto_detect or not station:
            detected = _detect_station(file.filename)
            file_station = detected or station or "global"
        
        try:
            # Save and process
            file_id, file_path = await storage.save_uploaded_file(file)
            sheets = processor.get_sheet_names(file_path)
            
            if not sheets:
                errors.append(f"{file.filename}: No sheets found")
                continue
            
            mapper = Mapper(station=file_station)
            df = processor.read_workbook(file_path, sheets[0])
            mapped_df, stats = mapper.map_dataframe(df)
            
            output_path = storage.save_processed_file(file_id, mapped_df)
            
            # Prepare output filename
            output_filename = f"mapped_{file_station}_{file.filename}"
            if not output_filename.endswith('.xlsx'):
                output_filename += '.xlsx'
            
            output_files.append((output_filename, output_path))
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    if not output_files:
        raise HTTPException(
            status_code=400,
            detail=f"No files processed successfully. Errors: {errors}"
        )
    
    if return_zip:
        # Create and stream ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, filepath in output_files:
                zf.write(filepath, filename)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=roster_mapped_batch.zip"
            }
        )
    else:
        # Return JSON response
        return {
            "success": True,
            "files_processed": len(output_files),
            "errors": errors,
            "download_url": "/api/v1/batch-download"
        }


@router.get("/batch-download")
async def batch_download():
    """Download the latest batch ZIP file."""
    zip_path = settings.TEMP_DIR / "batch_output.zip"
    
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="No batch file available")
    
    def iterfile():
        with open(zip_path, "rb") as f:
            yield from f
    
    return StreamingResponse(
        iterfile(),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=roster_mapped_batch.zip"
        }
    )


def _detect_station(filename: str) -> Optional[str]:
    """Detect station code from filename."""
    stations = ["SGN", "HAN", "DAD", "CXR", "HPH", "VCA", "VII"]
    filename_upper = filename.upper()
    for station in stations:
        if station in filename_upper:
            return station
    return None


def _create_zip(files: List[tuple], output_path: Path) -> None:
    """Create ZIP archive from list of (filename, filepath) tuples."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, filepath in files:
            if Path(filepath).exists():
                # Use mapped_ prefix
                archive_name = f"mapped_{filename}"
                if not archive_name.endswith('.xlsx'):
                    archive_name += '.xlsx'
                zf.write(filepath, archive_name)

