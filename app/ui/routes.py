"""
UI Routes - Web Interface
=========================
Jinja2 + Tailwind + HTMX based web interface.

Author: datnguyentien@vietjetair.com
"""

from typing import Optional, List
from pathlib import Path
import json

from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
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
            # Process each selected sheet
            mapped_sheets = {}
            total_stats = {
                "total_cells": 0,
                "mapped_cells": 0,
                "unmapped_cells": 0,
                "sheets_processed": 0
            }
            sheet_results = []
            
            for sheet in selected_sheets:
                try:
                    df = processor.read_workbook(file_path, sheet)
                    mapped_df, stats = mapper.map_dataframe(df)
                    mapped_sheets[sheet] = mapped_df
                    
                    # Aggregate stats
                    total_stats["total_cells"] += stats.get("total_cells", 0)
                    total_stats["mapped_cells"] += stats.get("mapped_cells", 0)
                    total_stats["unmapped_cells"] += stats.get("unmapped_cells", 0)
                    total_stats["sheets_processed"] += 1
                    
                    sheet_results.append({
                        "sheet": sheet,
                        "rows": len(mapped_df),
                        "mapped": stats.get("mapped_cells", 0),
                        "unmapped": stats.get("unmapped_cells", 0)
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing sheet {sheet}: {e}")
                    sheet_results.append({
                        "sheet": sheet,
                        "error": str(e)
                    })
            
            # Save output with all mapped sheets
            if mapped_sheets:
                output_path = storage.save_processed_file_multi_sheet(
                    file_info["file_id"], 
                    mapped_sheets
                )
                
                results.append({
                    "file_id": file_info["file_id"],
                    "filename": file_info["filename"],
                    "station": file_info["station"],
                    "stats": total_stats,
                    "sheet_results": sheet_results,
                    "download_url": f"/api/v1/download/{file_info['file_id']}"
                })
            else:
                results.append({
                    "file_id": file_info["file_id"],
                    "filename": file_info["filename"],
                    "error": "No sheets could be processed"
                })
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            results.append({
                "file_id": file_info["file_id"],
                "filename": file_info["filename"],
                "error": str(e)
            })
    
    # Store results
    results_path = settings.TEMP_DIR / "session_results.json"
    with open(results_path, "w") as f:
        json.dump({"results": results}, f)
    
    return RedirectResponse(url="/results", status_code=302)


@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - show processing results."""
    results_path = settings.TEMP_DIR / "session_results.json"
    
    if not results_path.exists():
        return RedirectResponse(url="/upload", status_code=302)
    
    with open(results_path, "r") as f:
        data = json.load(f)
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "results": data.get("results", []),
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

