"""
UI Routes - Web Interface
=========================
Jinja2 + Tailwind + HTMX based web interface.

Author: datnguyentien@vietjetair.com
"""

from typing import Optional, List
from pathlib import Path
import json
import os
import time

from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.logging import get_logger
from app.services.mapper import Mapper
from app.services.storage import StorageService
from app.services.excel_processor import ExcelProcessor

router = APIRouter()
logger = get_logger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")

# Constants
STATIONS = ["SGN", "HAN", "DAD", "CXR", "HPH", "VCA", "VII"]


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirect to upload."""
    return RedirectResponse(url="/upload", status_code=302)


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page - multi-file upload with station selection."""
    storage = StorageService()
    
    # Get station mapping status
    station_status = []
    for station in STATIONS:
        has_mapping = storage.mapping_exists(station)
        mappings = storage.load_mapping(station) or {}
        station_status.append({
            "code": station,
            "has_mapping": has_mapping,
            "count": len(mappings)
        })
    
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "stations": station_status,
        "auto_detect": settings.AUTO_DETECT_STATION,
        "page_title": "Upload Files"
    })


@router.post("/upload", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
    files: List[UploadFile] = File(...),
    station: str = Form("auto"),
    auto_detect: bool = Form(False)
):
    """Handle file upload and redirect to sheet selection."""
    if not files or all(f.filename == "" for f in files):
        storage = StorageService()
        station_status = []
        for s in STATIONS:
            has_mapping = storage.mapping_exists(s)
            mappings = storage.load_mapping(s) or {}
            station_status.append({
                "code": s, "has_mapping": has_mapping, "count": len(mappings)
            })
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "stations": station_status,
            "error": "Vui lòng chọn ít nhất 1 file"
        })
    
    storage = StorageService()
    processor = ExcelProcessor()
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            continue
            
        # Save file
        file_id, saved_path = await storage.save_uploaded_file(file)
        
        # Get sheets
        try:
            sheets = processor.get_sheet_names(saved_path)
        except Exception as e:
            sheets = []
            logger.error(f"Error reading sheets: {e}")
        
        # Detect station if enabled
        detected_station = None
        if auto_detect or station == "auto":
            detected_station = _detect_station(file.filename)
        
        uploaded_files.append({
            "file_id": file_id,
            "filename": file.filename,
            "sheets": sheets,
            "station": detected_station or (station if station != "auto" else "HAN"),
            "selected_sheets": sheets,  # Default: all sheets selected
            "sheet_selection_mode": "all"  # "all" or "specific"
        })
    
    # Store in session
    session_data = {"files": uploaded_files}
    session_path = settings.TEMP_DIR / "session_upload.json"
    with open(session_path, "w") as f:
        json.dump(session_data, f)
    
    # Redirect to sheet selection page
    return RedirectResponse(url="/select-sheets", status_code=302)


@router.get("/select-sheets", response_class=HTMLResponse)
async def select_sheets_page(request: Request):
    """Sheet selection page - choose which sheets to process."""
    session_path = settings.TEMP_DIR / "session_upload.json"
    if not session_path.exists():
        return RedirectResponse(url="/upload", status_code=302)
    
    with open(session_path, "r") as f:
        session_data = json.load(f)
    
    return templates.TemplateResponse("select_sheets.html", {
        "request": request,
        "files": session_data.get("files", []),
        "stations": STATIONS,
        "page_title": "Select Sheets"
    })


@router.post("/select-sheets", response_class=HTMLResponse)
async def handle_sheet_selection(request: Request):
    """Handle sheet selection and redirect to preview."""
    form_data = await request.form()
    
    session_path = settings.TEMP_DIR / "session_upload.json"
    with open(session_path, "r") as f:
        session_data = json.load(f)
    
    # Update selected sheets for each file
    for file_info in session_data.get("files", []):
        file_id = file_info["file_id"]
        
        # Get selection mode
        mode_key = f"mode_{file_id}"
        mode = form_data.get(mode_key, "all")
        file_info["sheet_selection_mode"] = mode
        
        # Get station
        station_key = f"station_{file_id}"
        file_info["station"] = form_data.get(station_key, file_info["station"])
        
        if mode == "all":
            file_info["selected_sheets"] = file_info["sheets"]
        else:
            # Get specifically selected sheets
            selected = []
            for sheet in file_info["sheets"]:
                checkbox_key = f"sheet_{file_id}_{sheet}"
                if form_data.get(checkbox_key):
                    selected.append(sheet)
            file_info["selected_sheets"] = selected if selected else file_info["sheets"]
    
    # Save updated session
    with open(session_path, "w") as f:
        json.dump(session_data, f)
    
    return RedirectResponse(url="/preview", status_code=302)


@router.get("/preview", response_class=HTMLResponse)
async def preview_page(request: Request):
    """Preview page - show before/after mapping for multiple sheets."""
    # Load session data
    session_path = settings.TEMP_DIR / "session_upload.json"
    if not session_path.exists():
        return RedirectResponse(url="/upload", status_code=302)
    
    with open(session_path, "r") as f:
        session_data = json.load(f)
    
    storage = StorageService()
    processor = ExcelProcessor()
    
    previews = []
    for file_info in session_data.get("files", []):
        file_path = storage.get_uploaded_file_path(file_info["file_id"])
        
        if not file_path.exists():
            continue
        
        # Load mapper for station
        mapper = Mapper(station=file_info["station"])
        
        # Get selected sheets (multi-sheet support)
        selected_sheets = file_info.get("selected_sheets", file_info.get("sheets", []))
        if not selected_sheets:
            continue
        
        file_preview = {
            "file_id": file_info["file_id"],
            "filename": file_info["filename"],
            "station": file_info["station"],
            "all_sheets": file_info["sheets"],
            "selected_sheets": selected_sheets,
            "sheet_previews": []
        }
        
        # Preview each selected sheet
        for sheet in selected_sheets:
            try:
                preview_data = processor.preview_sheet(file_path, sheet, max_rows=15)
                
                # Create before/after comparison
                rows_comparison = []
                unmapped_codes = set()
                mapped_count = 0
                
                for row in preview_data["rows"]:
                    row_mapped = []
                    for cell in row:
                        original = cell
                        mapped = mapper.map_cell(cell) if cell else ""
                        
                        # Check if mapped
                        is_mapped = mapped != original and mapped != ""
                        is_unmapped = not is_mapped and original and mapper.map_code(original) is None and not str(original).isdigit()
                        
                        if is_mapped:
                            mapped_count += 1
                        if is_unmapped and original:
                            unmapped_codes.add(original)
                        
                        row_mapped.append({
                            "original": original,
                            "mapped": mapped,
                            "is_mapped": is_mapped,
                            "is_unmapped": is_unmapped
                        })
                    rows_comparison.append(row_mapped)
                
                file_preview["sheet_previews"].append({
                    "sheet": sheet,
                    "headers": preview_data["headers"],
                    "rows": rows_comparison,
                    "total_rows": preview_data["total_rows"],
                    "mapped_count": mapped_count,
                    "unmapped_codes": list(unmapped_codes)[:10]
                })
            except Exception as e:
                logger.error(f"Preview error for sheet {sheet}: {e}")
                continue
        
        previews.append(file_preview)
    
    # Calculate total sheets for display
    total_sheets = sum(len(p.get("sheet_previews", [])) for p in previews)
    
    return templates.TemplateResponse("preview.html", {
        "request": request,
        "previews": previews,
        "stations": STATIONS,
        "total_sheets": total_sheets,
        "page_title": "Preview Mapping"
    })


@router.post("/preview/update-station", response_class=HTMLResponse)
async def update_station(
    request: Request,
    file_id: str = Form(...),
    station: str = Form(...)
):
    """Update station for a specific file (HTMX endpoint)."""
    session_path = settings.TEMP_DIR / "session_upload.json"
    
    with open(session_path, "r") as f:
        session_data = json.load(f)
    
    for file_info in session_data.get("files", []):
        if file_info["file_id"] == file_id:
            file_info["station"] = station
            break
    
    with open(session_path, "w") as f:
        json.dump(session_data, f)
    
    return HTMLResponse(content=f'<span class="text-green-600">✓ Updated to {station}</span>')


@router.post("/process", response_class=HTMLResponse)
async def process_files(request: Request):
    """Process all files with multiple sheets and redirect to results."""
    session_path = settings.TEMP_DIR / "session_upload.json"
    
    if not session_path.exists():
        return RedirectResponse(url="/upload", status_code=302)
    
    with open(session_path, "r") as f:
        session_data = json.load(f)
    
    storage = StorageService()
    processor = ExcelProcessor()
    
    results = []
    for file_info in session_data.get("files", []):
        file_path = storage.get_uploaded_file_path(file_info["file_id"])
        
        if not file_path.exists():
            continue
        
        mapper = Mapper(station=file_info["station"])
        
        # Get selected sheets (multi-sheet support)
        selected_sheets = file_info.get("selected_sheets", [])
        if not selected_sheets:
            selected_sheets = file_info.get("sheets", [])[:1]  # Fallback to first sheet
        
        try:
            total_stats = {
                "total_cells": 0,
                "mapped_cells": 0,
                "unmapped_cells": 0,
                "empty_cells": 0,
                "sheets_processed": 0
            }
            sheet_results = []
            
            # ========== FORMAT 1: STYLED (preserve formatting) ==========
            # Copy original file and map directly to preserve styles
            styled_path = storage.copy_file_for_processing(file_info["file_id"], "styled")
            styled_stats = processor.map_workbook_preserve_style(
                source_path=file_path,
                dest_path=styled_path,
                mapper_func=mapper.map_cell,
                sheet_names=selected_sheets
            )
            
            # Aggregate stats from styled processing
            # styled_stats has structure: {sheets_processed, total_cells_mapped, total_cells_unchanged, sheet_stats: {sheet_name: {mapped, unchanged, total}}}
            for sheet_name, sheet_stat in styled_stats.get("sheet_stats", {}).items():
                total_stats["total_cells"] += sheet_stat.get("total", 0)
                total_stats["mapped_cells"] += sheet_stat.get("mapped", 0)
                total_stats["unmapped_cells"] += sheet_stat.get("unchanged", 0)
                total_stats["sheets_processed"] += 1
                
                sheet_results.append({
                    "sheet": sheet_name,
                    "rows": sheet_stat.get("total", 0),
                    "mapped": sheet_stat.get("mapped", 0),
                    "unmapped": sheet_stat.get("unchanged", 0)
                })
                    
            # ========== FORMAT 2: PLAIN (text only, no formatting) ==========
            # Use DataFrame approach for clean text output
            mapped_sheets = {}
            for sheet in selected_sheets:
                try:
                    df = processor.read_workbook(file_path, sheet)
                    mapped_df, _ = mapper.map_dataframe(df)
                    mapped_sheets[sheet] = mapped_df
                except Exception as e:
                    logger.error(f"Error processing sheet {sheet} for plain format: {e}")
            
            if mapped_sheets:
                storage.save_processed_file_multi_sheet(
                    file_info["file_id"] + "_plain",
                    mapped_sheets
                )
                
            results.append({
                "file_id": file_info["file_id"],
                "filename": file_info["filename"],
                "station": file_info["station"],
                "stats": total_stats,
                "sheet_results": sheet_results,
                "download_url_styled": f"/api/v1/download/{file_info['file_id']}?format=styled",
                "download_url_plain": f"/api/v1/download/{file_info['file_id']}?format=plain"
            })
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            results.append({
                "file_id": file_info["file_id"],
                "filename": file_info["filename"],
                "error": str(e)
            })
    
    # Store results - Use a unique session ID to avoid conflicts across Cloud Run instances
    session_id = f"session_{int(time.time() * 1000)}"
    
    # Store results in OUTPUT_DIR/results (same location as processed files)
    # Note: On Cloud Run, OUTPUT_DIR is /tmp/output (ephemeral, instance-specific)
    # But since processed files are also here, results should be accessible via download endpoint
    # For true multi-instance support, would need GCS or database
    results_dir = settings.OUTPUT_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / f"{session_id}.json"
    
    # Cleanup old result files (older than 1 hour) to prevent disk space issues
    try:
        current_time = time.time()
        for old_file in results_dir.glob("session_*.json"):
            try:
                if old_file.stat().st_mtime < current_time - 3600:  # 1 hour
                    old_file.unlink()
                    logger.debug(f"Cleaned up old result file: {old_file.name}")
            except Exception as e:
                logger.warning(f"Error cleaning up old result file {old_file}: {e}")
    except Exception as e:
        logger.warning(f"Error during result file cleanup: {e}")
    
    try:
        # Write results with explicit flush
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump({"results": results, "session_id": session_id}, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        # Verify file was written
        if not results_path.exists():
            logger.error(f"Failed to create results file: {results_path}")
            raise Exception("Failed to save results file")
        
        logger.info(f"Results saved successfully: {results_path}, size: {results_path.stat().st_size} bytes, session_id: {session_id}")
        
        # Check if client wants JSON response (AJAX request)
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header.lower():
            # Return JSON for API/AJAX clients
            return JSONResponse(content={
                "success": True,
                "session_id": session_id,
                "message": f"Processing completed. {len(results)} file(s) processed.",
                "results_url": f"/results?session_id={session_id}",
                "status_url": f"/api/v1/results/status?session_id={session_id}",
                "files_count": len(results)
            })
        
        # Default: Redirect for form submissions
        return RedirectResponse(url=f"/results?session_id={session_id}", status_code=302)
        
    except Exception as e:
        logger.error(f"Error saving results file: {e}", exc_info=True)
        # Fallback: try TEMP_DIR (may work if same instance)
        fallback_path = settings.TEMP_DIR / "session_results.json"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(fallback_path, "w", encoding="utf-8") as f:
                json.dump({"results": results}, f, ensure_ascii=False)
                f.flush()
            logger.warning(f"Used fallback path: {fallback_path}")
            return RedirectResponse(url="/results", status_code=302)
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}", exc_info=True)
            # Last resort: redirect anyway, frontend will show error
            return RedirectResponse(url="/upload?error=processing_failed", status_code=302)


@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - show processing results."""
    # Try to get session_id from query parameter
    session_id = request.query_params.get("session_id")
    
    results_data = None
    
    # Method 1: Try OUTPUT_DIR/results/{session_id}.json (preferred for Cloud Run)
    if session_id:
        results_dir = settings.OUTPUT_DIR / "results"
        results_path = results_dir / f"{session_id}.json"
        logger.info(f"Looking for results with session_id: {session_id}, path: {results_path}")
        
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    results_data = json.load(f)
                logger.info(f"Loaded results from OUTPUT_DIR: {results_path}")
            except Exception as e:
                logger.error(f"Error reading results file from OUTPUT_DIR: {e}", exc_info=True)
    
    # Method 2: Fallback to TEMP_DIR/session_results.json (for same-instance requests)
    if not results_data:
        fallback_path = settings.TEMP_DIR / "session_results.json"
        logger.info(f"Trying fallback path: {fallback_path}")
        
        if fallback_path.exists():
            try:
                with open(fallback_path, "r", encoding="utf-8") as f:
                    results_data = json.load(f)
                logger.info(f"Loaded results from TEMP_DIR: {fallback_path}")
            except Exception as e:
                logger.error(f"Error reading fallback results file: {e}", exc_info=True)
    
    if not results_data:
        logger.warning(f"Results file not found. session_id: {session_id}, TEMP_DIR: {settings.TEMP_DIR}, OUTPUT_DIR: {settings.OUTPUT_DIR}")
        # List available files for debugging
        if settings.OUTPUT_DIR.exists():
            results_dir = settings.OUTPUT_DIR / "results"
            if results_dir.exists():
                result_files = list(results_dir.glob("*.json"))
                logger.info(f"Available result files in OUTPUT_DIR/results: {[f.name for f in result_files[:5]]}")
        if settings.TEMP_DIR.exists():
            temp_files = list(settings.TEMP_DIR.glob("*"))
            logger.info(f"Files in TEMP_DIR: {[f.name for f in temp_files[:5]]}")
        return RedirectResponse(url="/upload?error=results_not_found", status_code=302)
    
    results = results_data.get("results", [])
    logger.info(f"Loaded {len(results)} results")
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "results": results,
        "page_title": "Results"
    })


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin page - manage mappings."""
    storage = StorageService()
    
    stations_data = []
    for station in STATIONS:
        mappings = storage.load_mapping(station) or {}
        versions = storage.list_mapping_versions(station)
        
        stations_data.append({
            "code": station,
            "count": len(mappings),
            "versions": versions[:5],
            "mappings": dict(list(mappings.items())[:20])
        })
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stations": stations_data,
        "page_title": "Admin - Mapping Management"
    })


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page - statistics and charts."""
    storage = StorageService()
    
    # Get stats per station
    station_stats = []
    total_mappings = 0
    
    for station in STATIONS:
        mappings = storage.load_mapping(station) or {}
        count = len(mappings)
        total_mappings += count
        
        station_stats.append({
            "code": station,
            "mapping_count": count,
            "has_mapping": count > 0
        })
    
    # Get audit log summary
    audit_entries = storage.get_audit_log(limit=50)
    
    # Count by action type
    action_counts = {}
    for entry in audit_entries:
        action = entry.get("action", "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "station_stats": station_stats,
        "total_mappings": total_mappings,
        "action_counts": action_counts,
        "recent_activity": audit_entries[:10],
        "page_title": "Dashboard"
    })


def _detect_station(filename: str) -> Optional[str]:
    """Detect station code from filename."""
    filename_upper = filename.upper()
    for station in STATIONS:
        if station in filename_upper:
            return station
    return None

