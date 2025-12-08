"""
Admin API Endpoints
===================
Administrative endpoints for mapping management.

Author: datnguyentien@vietjetair.com
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage import StorageService

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Models
class MappingEntry(BaseModel):
    """Single mapping entry."""
    code: str
    description: str
    category: Optional[str] = None


class MappingImportRequest(BaseModel):
    """Request model for importing mappings."""
    station: str
    mappings: List[MappingEntry]
    replace_existing: bool = False


class MappingImportResponse(BaseModel):
    """Response model for mapping import."""
    success: bool
    message: str
    station: str
    imported_count: int
    version: str


class MappingVersionInfo(BaseModel):
    """Mapping version information."""
    version: str
    station: str
    created_at: datetime
    entry_count: int
    created_by: Optional[str] = None


class MappingExportResponse(BaseModel):
    """Response model for mapping export."""
    station: str
    version: str
    mappings: Dict[str, str]
    entry_count: int


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    timestamp: datetime
    action: str
    user: Optional[str]
    station: Optional[str]
    details: Dict[str, Any]


# Endpoints
@router.post("/mappings/import", response_model=MappingImportResponse)
async def import_mappings(
    request: MappingImportRequest
) -> MappingImportResponse:
    """
    Import mappings for a station.
    
    Accepts a list of code-description pairs and saves them as a new mapping version.
    """
    logger.info(
        "Mapping import started",
        station=request.station,
        count=len(request.mappings)
    )
    
    try:
        storage = StorageService()
        
        # Convert to mapping dict
        mapping_dict = {
            entry.code: entry.description
            for entry in request.mappings
        }
        
        # Save mapping
        version = storage.save_mapping(
            station=request.station,
            mappings=mapping_dict,
            replace=request.replace_existing
        )
        
        logger.info(
            "Mapping import completed",
            station=request.station,
            version=version,
            count=len(mapping_dict)
        )
        
        return MappingImportResponse(
            success=True,
            message=f"Successfully imported {len(mapping_dict)} mappings",
            station=request.station,
            imported_count=len(mapping_dict),
            version=version
        )
        
    except Exception as e:
        logger.error("Mapping import failed", error=str(e), station=request.station)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/mappings/import-csv", response_model=MappingImportResponse)
async def import_mappings_file(
    file: UploadFile = File(..., description="CSV, JSON, or Excel file with mappings"),
    station: str = Query(..., description="Station code"),
    replace_existing: bool = Query(False, description="Replace existing mappings")
) -> MappingImportResponse:
    """
    Import mappings from a file (CSV, JSON, or Excel).
    
    Supported formats:
    - CSV: columns 'from'/'to' or 'code'/'description'
    - JSON: {"FROM_CODE": "TO_CODE", ...}
    - Excel: First two columns are From and To codes
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    filename_lower = file.filename.lower()
    logger.info("Mapping file import started", station=station, filename=file.filename)
    
    try:
        content = await file.read()
        mapping_dict = {}
        
        # ========== CSV ==========
        if filename_lower.endswith(".csv"):
            import csv
            from io import StringIO
            
            text_content = content.decode("utf-8")
            reader = csv.DictReader(StringIO(text_content))
            
            for row in reader:
                # Support both 'from'/'to' and 'code'/'description' column names
                from_code = row.get("from", row.get("code", row.get("FROM", row.get("Code", "")))).strip()
                to_code = row.get("to", row.get("description", row.get("TO", row.get("Description", "")))).strip()
                
                if from_code and to_code:
                    mapping_dict[from_code] = to_code
        
        # ========== JSON ==========
        elif filename_lower.endswith(".json"):
            import json
            
            text_content = content.decode("utf-8")
            data = json.loads(text_content)
            
            # Handle both formats: {"mappings": {...}} or direct {...}
            if isinstance(data, dict):
                if "mappings" in data:
                    mapping_dict = data["mappings"]
                else:
                    # Filter out metadata keys starting with '_'
                    mapping_dict = {k: v for k, v in data.items() if not k.startswith("_")}
        
        # ========== Excel ==========
        elif filename_lower.endswith((".xlsx", ".xls")):
            import pandas as pd
            from io import BytesIO
            
            df = pd.read_excel(BytesIO(content), header=None)
            
            # Use first two columns as from/to
            if len(df.columns) >= 2:
                for idx, row in df.iterrows():
                    from_code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                    to_code = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                    
                    # Skip header row if it looks like headers
                    if idx == 0 and from_code.lower() in ["from", "code", "from_code", "mã gốc"]:
                        continue
                    
                    if from_code and to_code:
                        mapping_dict[from_code] = to_code
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Use CSV, JSON, or Excel (.xlsx/.xls)"
            )
        
        if not mapping_dict:
            raise HTTPException(status_code=400, detail="No valid mappings found in file")
        
        # Save mapping
        storage = StorageService()
        version = storage.save_mapping(
            station=station,
            mappings=mapping_dict,
            replace=replace_existing
        )
        
        logger.info(
            "Mapping file import completed",
            station=station,
            version=version,
            count=len(mapping_dict),
            file_type=filename_lower.split(".")[-1]
        )
        
        return MappingImportResponse(
            success=True,
            message=f"Successfully imported {len(mapping_dict)} mappings",
            station=station,
            imported_count=len(mapping_dict),
            version=version
        )
        
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error("JSON parse error", error=str(e), station=station)
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error("File import failed", error=str(e), station=station)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/mappings/{station}", response_model=MappingExportResponse)
async def get_mappings(
    station: str,
    version: Optional[str] = Query(None, description="Specific version (default: latest)")
) -> MappingExportResponse:
    """
    Get mappings for a station.
    
    Returns all code-description mappings for the specified station.
    """
    try:
        storage = StorageService()
        mappings = storage.load_mapping(station, version)
        
        if mappings is None:
            raise HTTPException(
                status_code=404,
                detail=f"No mappings found for station: {station}"
            )
        
        return MappingExportResponse(
            station=station,
            version=version or "latest",
            mappings=mappings,
            entry_count=len(mappings)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get mappings failed", error=str(e), station=station)
        raise HTTPException(status_code=500, detail=f"Failed to get mappings: {str(e)}")


@router.get("/mappings/{station}/versions", response_model=List[MappingVersionInfo])
async def list_mapping_versions(station: str) -> List[MappingVersionInfo]:
    """
    List all mapping versions for a station.
    """
    try:
        storage = StorageService()
        versions = storage.list_mapping_versions(station)
        
        return [
            MappingVersionInfo(
                version=v["version"],
                station=station,
                created_at=v["created_at"],
                entry_count=v["entry_count"],
                created_by=v.get("created_by")
            )
            for v in versions
        ]
        
    except Exception as e:
        logger.error("List versions failed", error=str(e), station=station)
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.delete("/mappings/{station}")
async def delete_mappings(
    station: str,
    version: Optional[str] = Query(None, description="Specific version to delete")
) -> dict:
    """
    Delete mappings for a station.
    
    If version is specified, deletes only that version.
    Otherwise, deletes all mappings for the station.
    """
    logger.warning("Mapping deletion requested", station=station, version=version)
    
    try:
        storage = StorageService()
        deleted = storage.delete_mapping(station, version)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"No mappings found for station: {station}"
            )
        
        return {
            "success": True,
            "message": f"Mappings deleted for station: {station}",
            "version": version or "all"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete mappings failed", error=str(e), station=station)
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/audit-log", response_model=List[AuditLogEntry])
async def get_audit_log(
    station: Optional[str] = Query(None, description="Filter by station"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return")
) -> List[AuditLogEntry]:
    """
    Get audit log entries.
    
    Returns recent actions performed on mappings and uploads.
    """
    try:
        storage = StorageService()
        entries = storage.get_audit_log(
            station=station,
            action=action,
            limit=limit
        )
        
        return [
            AuditLogEntry(
                timestamp=e["timestamp"],
                action=e["action"],
                user=e.get("user"),
                station=e.get("station"),
                details=e.get("details", {})
            )
            for e in entries
        ]
        
    except Exception as e:
        logger.error("Get audit log failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")


@router.post("/mappings/{station}/validate")
async def validate_mappings(
    station: str,
    mappings: Dict[str, str]
) -> dict:
    """
    Validate mappings without saving.
    
    Checks for duplicates, format issues, and conflicts with existing mappings.
    """
    issues = []
    warnings = []
    
    # Check for empty codes or descriptions
    for code, desc in mappings.items():
        if not code.strip():
            issues.append(f"Empty code found with description: {desc}")
        if not desc.strip():
            warnings.append(f"Empty description for code: {code}")
    
    # Check for duplicate codes (case-insensitive)
    codes_lower = {}
    for code in mappings.keys():
        lower = code.lower()
        if lower in codes_lower:
            issues.append(f"Duplicate code (case-insensitive): {code} and {codes_lower[lower]}")
        codes_lower[lower] = code
    
    # Load existing mappings to check for conflicts
    storage = StorageService()
    existing = storage.load_mapping(station)
    
    if existing:
        conflicts = []
        for code, new_desc in mappings.items():
            if code in existing and existing[code] != new_desc:
                conflicts.append({
                    "code": code,
                    "existing": existing[code],
                    "new": new_desc
                })
        
        if conflicts:
            warnings.append(f"Found {len(conflicts)} code(s) with different descriptions")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "entry_count": len(mappings)
    }

