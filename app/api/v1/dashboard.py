"""
Dashboard API
=============
Statistics and analytics endpoints.

Author: datnguyentien@vietjetair.com
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage import StorageService

router = APIRouter()
logger = get_logger(__name__)

STATIONS = ["SGN", "HAN", "DAD", "CXR", "HPH", "VCA", "VII"]


class StationStats(BaseModel):
    """Statistics for a single station."""
    code: str
    mapping_count: int
    has_mapping: bool
    last_updated: Optional[datetime] = None


class DashboardStats(BaseModel):
    """Overall dashboard statistics."""
    total_mappings: int
    active_stations: int
    total_stations: int
    stations: List[StationStats]
    recent_uploads: int
    recent_mappings: int


class ActionSummary(BaseModel):
    """Summary of actions by type."""
    action: str
    count: int


class TimeSeriesPoint(BaseModel):
    """Single point in time series."""
    date: str
    count: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Get overall dashboard statistics.
    
    Returns mapping counts per station, activity summary, etc.
    """
    storage = StorageService()
    
    station_stats = []
    total_mappings = 0
    active_stations = 0
    
    for station in STATIONS:
        mappings = storage.load_mapping(station) or {}
        count = len(mappings)
        total_mappings += count
        
        has_mapping = count > 0
        if has_mapping:
            active_stations += 1
        
        # Get last update from versions
        versions = storage.list_mapping_versions(station)
        last_updated = None
        if versions:
            last_updated = versions[0].get("created_at")
        
        station_stats.append(StationStats(
            code=station,
            mapping_count=count,
            has_mapping=has_mapping,
            last_updated=last_updated
        ))
    
    # Get recent activity counts
    audit_entries = storage.get_audit_log(limit=100)
    
    # Count recent uploads and mappings (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_uploads = sum(
        1 for e in audit_entries 
        if "upload" in e.get("action", "") and e.get("timestamp", datetime.min) > week_ago
    )
    recent_mappings = sum(
        1 for e in audit_entries 
        if "mapping" in e.get("action", "") and e.get("timestamp", datetime.min) > week_ago
    )
    
    return DashboardStats(
        total_mappings=total_mappings,
        active_stations=active_stations,
        total_stations=len(STATIONS),
        stations=station_stats,
        recent_uploads=recent_uploads,
        recent_mappings=recent_mappings
    )


@router.get("/stats/station/{station}")
async def get_station_stats(station: str) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific station.
    """
    if station not in STATIONS:
        return {"error": f"Unknown station: {station}"}
    
    storage = StorageService()
    
    mappings = storage.load_mapping(station) or {}
    versions = storage.list_mapping_versions(station)
    
    # Analyze mappings
    to_codes = {}
    for from_code, to_code in mappings.items():
        to_codes[to_code] = to_codes.get(to_code, 0) + 1
    
    return {
        "station": station,
        "mapping_count": len(mappings),
        "versions_count": len(versions),
        "versions": versions[:10],
        "to_code_distribution": dict(sorted(to_codes.items(), key=lambda x: -x[1])[:10]),
        "sample_mappings": dict(list(mappings.items())[:20])
    }


@router.get("/stats/actions", response_model=List[ActionSummary])
async def get_action_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get action statistics for the specified period.
    """
    storage = StorageService()
    
    cutoff = datetime.now() - timedelta(days=days)
    audit_entries = storage.get_audit_log(limit=1000)
    
    # Filter by date and count
    action_counts = {}
    for entry in audit_entries:
        timestamp = entry.get("timestamp")
        if timestamp and timestamp > cutoff:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
    
    return [
        ActionSummary(action=action, count=count)
        for action, count in sorted(action_counts.items(), key=lambda x: -x[1])
    ]


@router.get("/stats/timeline", response_model=List[TimeSeriesPoint])
async def get_timeline_stats(
    days: int = Query(30, ge=1, le=365),
    action_filter: Optional[str] = Query(None, description="Filter by action type")
):
    """
    Get time series data for activity over time.
    """
    storage = StorageService()
    
    cutoff = datetime.now() - timedelta(days=days)
    audit_entries = storage.get_audit_log(limit=1000)
    
    # Group by date
    daily_counts = {}
    for entry in audit_entries:
        timestamp = entry.get("timestamp")
        if not timestamp or timestamp < cutoff:
            continue
        
        if action_filter and action_filter not in entry.get("action", ""):
            continue
        
        date_str = timestamp.strftime("%Y-%m-%d")
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
    
    # Fill in missing dates
    result = []
    current = cutoff
    while current <= datetime.now():
        date_str = current.strftime("%Y-%m-%d")
        result.append(TimeSeriesPoint(
            date=date_str,
            count=daily_counts.get(date_str, 0)
        ))
        current += timedelta(days=1)
    
    return result


@router.get("/stats/unmapped")
async def get_unmapped_codes(
    station: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get list of commonly unmapped codes.
    
    This would typically be populated from processing logs.
    For now, returns placeholder data structure.
    """
    # In a full implementation, this would query a database
    # of unmapped codes encountered during processing
    
    return {
        "station": station or "all",
        "unmapped_codes": [],
        "message": "Unmapped codes tracking requires processing history database"
    }

