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
import pandas as pd

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
    
    # Use No-DB upload helper functions
    from app.api.v1.no_db_files import upload_file as no_db_upload
    processor = ExcelProcessor()
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            continue
        
        # Detect station if enabled
        detected_station = None
        if auto_detect or station == "auto":
            detected_station = _detect_station(file.filename)
        
        station_code = detected_station or (station if station != "auto" else "HAN")
        
        # Upload using No-DB endpoint helper
        try:
            # Create a mock request for No-DB upload
            from fastapi import Request as FastAPIRequest
            from starlette.datastructures import FormData, UploadFile as StarletteUploadFile
            
            # Call No-DB upload helper directly
            from app.api.v1.no_db_files import UPLOAD_DIR, secure_filename, save_meta, _iso_now, _now_ts, FILE_TTL_SECONDS
            import uuid
            
            # Read file content
            content = await file.read()
            size = len(content)
            
            if size == 0:
                continue
            
            # Generate upload_id
            upload_id = str(uuid.uuid4())
            
            # Save file
            orig_name = secure_filename(file.filename or "upload")
            saved_name = f"{upload_id}_{orig_name}"
            saved_path = UPLOAD_DIR / saved_name
            
            with saved_path.open("wb") as f:
                f.write(content)
            
            # Get sheet names
            sheets = []
            try:
                sheets = processor.get_sheet_names(saved_path)
            except Exception as e:
                logger.error(f"Error reading sheets: {e}")
                sheets = []
            
            # Create metadata
            meta = {
                "upload_id": upload_id,
                "filename": orig_name,
                "upload_path": str(saved_path),
                "station": station_code,
                "created_at": _iso_now(),
                "expires_at": _now_ts() + FILE_TTL_SECONDS,
                "status": "uploaded",
                "sheets": sheets,
                "file_size": size
            }
            save_meta(upload_id, meta)
            
            uploaded_files.append({
                "upload_id": upload_id,  # Use upload_id from No-DB
                "file_id": upload_id,  # For backward compatibility
                "filename": file.filename,
                "sheets": sheets,
                "station": station_code,
                "selected_sheets": sheets,  # Default: all sheets selected
                "sheet_selection_mode": "all"  # "all" or "specific"
            })
            
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}", exc_info=True)
            continue
    
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
    
    # Use No-DB metadata to find files
    from app.api.v1.no_db_files import load_meta, UPLOAD_DIR
    processor = ExcelProcessor()
    
    previews = []
    for file_info in session_data.get("files", []):
        # Try to find file via No-DB metadata first
        upload_id = file_info.get("upload_id") or file_info.get("file_id")
        file_path = None
        
        # Method 1: Load from No-DB metadata
        meta = load_meta(upload_id) if upload_id else None
        if meta:
            upload_path = meta.get("upload_path")
            if upload_path and os.path.exists(upload_path):
                file_path = Path(upload_path)
        
        # Method 2: Fallback to StorageService
        if not file_path or not file_path.exists():
            storage = StorageService()
            file_path = storage.get_uploaded_file_path(file_info["file_id"])
        
        if not file_path or not file_path.exists():
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
    logger.info("POST /process called", 
                accept_header=request.headers.get("accept", ""),
                content_type=request.headers.get("content-type", ""))
    
    session_path = settings.TEMP_DIR / "session_upload.json"
    
    if not session_path.exists():
        logger.warning(f"Session file not found: {session_path}")
        return RedirectResponse(url="/upload", status_code=302)
    
    logger.info(f"Reading session data from: {session_path}")
    with open(session_path, "r") as f:
        session_data = json.load(f)
    
    logger.info(f"Session data loaded: {len(session_data.get('files', []))} file(s)")
    
    # Use No-DB metadata to find files
    from app.api.v1.no_db_files import load_meta, UPLOAD_DIR, OUTPUT_DIR, save_meta, _iso_now, _now_ts, FILE_TTL_SECONDS
    import uuid
    processor = ExcelProcessor()
    
    results = []
    for file_info in session_data.get("files", []):
        # Try to find file via No-DB metadata first
        upload_id = file_info.get("upload_id") or file_info.get("file_id")
        file_path = None
        
        # Method 1: Load from No-DB metadata
        meta = load_meta(upload_id) if upload_id else None
        if meta:
            upload_path = meta.get("upload_path")
            if upload_path and os.path.exists(upload_path):
                file_path = Path(upload_path)
        
        # Method 2: Fallback to StorageService
        if not file_path or not file_path.exists():
            storage = StorageService()
            file_path = storage.get_uploaded_file_path(file_info["file_id"])
        
        if not file_path or not file_path.exists():
            logger.warning(f"File not found: {file_info.get('file_id')}, upload_id: {upload_id}")
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
            # Generate file_id for No-DB
            styled_file_id = str(uuid.uuid4())
            styled_path = OUTPUT_DIR / f"{styled_file_id}_mapped.xlsx"
            styled_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Processing styled format for upload_id: {upload_id}, file_id: {styled_file_id}")
            
            # Copy original file and map directly to preserve styles
            styled_stats = processor.map_workbook_preserve_style(
                source_path=file_path,
                dest_path=styled_path,
                mapper_func=mapper.map_cell,
                sheet_names=selected_sheets
            )
            logger.info(f"Styled file saved: {styled_path}, exists: {styled_path.exists()}")
            
            # Save styled file metadata to No-DB
            styled_meta = {
                "file_id": styled_file_id,
                "upload_id": upload_id,
                "upload_path": str(file_path),
                "output_path": str(styled_path),
                "station": file_info["station"],
                "created_at": _iso_now(),
                "mapped_at": _iso_now(),
                "expires_at": _now_ts() + FILE_TTL_SECONDS,
                "status": "ready",
                "download_mode": "styled"
            }
            save_meta(styled_file_id, styled_meta)
            
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
            
            # ========== FORMAT 2: PLAIN (text only, no formatting) ==========
            plain_file_id = None
            plain_path = None
            
            if mapped_sheets:
                # Generate file_id for plain format
                plain_file_id = str(uuid.uuid4())
                plain_path = OUTPUT_DIR / f"{plain_file_id}_mapped.xlsx"
                plain_path.parent.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"Processing plain format for upload_id: {upload_id}, file_id: {plain_file_id}, {len(mapped_sheets)} sheets")
                
                # Save plain format file (text only, no formatting)
                with pd.ExcelWriter(plain_path, engine="openpyxl") as writer:
                    for sheet_name, df in mapped_sheets.items():
                        safe_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
                        df.to_excel(writer, sheet_name=safe_name, index=False)
                
                logger.info(f"Plain format file saved: {plain_path}, exists: {plain_path.exists()}, size: {plain_path.stat().st_size if plain_path.exists() else 0} bytes")
                
                # Save plain file metadata to No-DB
                plain_meta = {
                    "file_id": plain_file_id,
                    "upload_id": upload_id,
                    "upload_path": str(file_path),
                    "output_path": str(plain_path),
                    "station": file_info["station"],
                    "created_at": _iso_now(),
                    "mapped_at": _iso_now(),
                    "expires_at": _now_ts() + FILE_TTL_SECONDS,
                    "status": "ready",
                    "download_mode": "plain"
                }
                save_meta(plain_file_id, plain_meta)
                
            # Build download URLs using No-DB endpoints
            download_url_styled = f"/api/v1/no-db-files/download/{styled_file_id}" if styled_file_id else None
            download_url_plain = f"/api/v1/no-db-files/download/{plain_file_id}" if plain_file_id else None
            
            logger.info(f"File processed successfully: {file_info['file_id']}, "
                       f"styled_url: {download_url_styled}, plain_url: {download_url_plain}")
            
            results.append({
                "file_id": file_info.get("file_id") or upload_id,
                "upload_id": upload_id,
                "filename": file_info["filename"],
                "station": file_info["station"],
                "stats": total_stats,
                "sheet_results": sheet_results,
                "download_url_styled": download_url_styled,
                "download_url_plain": download_url_plain,
                "styled_file_id": styled_file_id,
                "plain_file_id": plain_file_id
            })
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            results.append({
                "file_id": file_info["file_id"],
                "filename": file_info["filename"],
                "error": str(e)
            })
    
    # Store results - Use No-DB metadata JSON for multi-instance support
    session_id = f"session_{int(time.time() * 1000)}"
    
    try:
        # Save results to metadata JSON (shared across instances via META_DIR)
        from app.api.v1.no_db_files import save_session_results
        save_session_results(session_id, results)
        
        logger.info(f"Results saved to metadata: session_id={session_id}, {len(results)} files")
        
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
        logger.error(f"Error saving results to metadata: {e}", exc_info=True)
        # Last resort: redirect anyway, frontend will show error
        return RedirectResponse(url="/upload?error=processing_failed", status_code=302)


@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - show processing results."""
    # Try to get session_id from query parameter
    session_id = request.query_params.get("session_id")
    
    results_data = None
    
    # Method 1: Try No-DB metadata JSON (preferred - works across instances)
    if session_id:
        try:
            from app.api.v1.no_db_files import load_session_results
            results_data = load_session_results(session_id)
            if results_data:
                logger.info(f"Loaded results from metadata: session_id={session_id}")
        except Exception as e:
            logger.error(f"Error loading results from metadata: {e}", exc_info=True)
    
    # Method 2: Fallback to old OUTPUT_DIR/results/{session_id}.json (for backward compatibility)
    if not results_data and session_id:
        results_dir = settings.OUTPUT_DIR / "results"
        results_path = results_dir / f"{session_id}.json"
        logger.info(f"Trying fallback path: {results_path}")
        
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    results_data = json.load(f)
                logger.info(f"Loaded results from OUTPUT_DIR: {results_path}")
            except Exception as e:
                logger.error(f"Error reading results file from OUTPUT_DIR: {e}", exc_info=True)
    
    # Method 3: Fallback to TEMP_DIR/session_results.json (for same-instance requests)
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
        logger.warning(f"Results not found. session_id: {session_id}, TEMP_DIR: {settings.TEMP_DIR}, OUTPUT_DIR: {settings.OUTPUT_DIR}")
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

