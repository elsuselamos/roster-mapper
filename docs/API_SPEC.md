# API SPEC – Roster Mapper

---

## 1. Overview

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
- Phase 1: No authentication required (internal use)
- Phase 2: API Key / JWT Bearer token

### Response Format
```json
{
  "success": true,
  "message": "Operation completed",
  "data": { ... }
}
```

### Error Format
```json
{
  "detail": "Error description"
}
```

---

## 2. Upload & Process Endpoints

### POST /upload

**Mục đích:** Upload file Excel để xử lý

**Request:**
```
Content-Type: multipart/form-data

file: <binary> (required) - File .xlsx hoặc .xls
```

**Response (200):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_id": "abc123-uuid",
  "filename": "roster_SGN.xlsx",
  "sheets": ["Sheet1", "Sheet2", "Data"]
}
```

**Errors:**
| Code | Mô tả |
|------|-------|
| 400 | File type không hợp lệ (.xlsx, .xls only) |
| 400 | Filename missing |
| 500 | Upload failed (server error) |

---

### GET /preview/{file_id}

**Mục đích:** Preview data từ sheet

**Query Parameters:**
| Param | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| sheet | string | ✅ | - | Tên sheet cần preview |
| rows | int | ❌ | 10 | Số rows preview (1-100) |

**Response (200):**
```json
{
  "sheet_name": "Sheet1",
  "headers": ["Name", "Code", "Date", "Activity"],
  "rows": [
    ["Nguyễn Văn A", "B1", "2024-12-01", "OFF"],
    ["Trần Thị B", "B19", "2024-12-01", "TR"]
  ],
  "total_rows": 150
}
```

**Errors:**
| Code | Mô tả |
|------|-------|
| 404 | File not found |
| 400 | Sheet không tồn tại |

---

### POST /process/{file_id}

**Mục đích:** Process file với mapping

**Request (form-data):**
| Field | Type | Required | Mô tả |
|-------|------|----------|-------|
| sheet | string | ✅ | Sheet name |
| station | string | ❌ | Station code (auto-detect nếu không có) |
| columns | string | ❌ | Comma-separated column names |

**Response (200):**
```json
{
  "success": true,
  "message": "File processed successfully",
  "download_url": "/api/v1/download/abc123",
  "stats": {
    "total_cells": 450,
    "mapped_cells": 380,
    "unchanged_cells": 50,
    "empty_cells": 20,
    "columns_processed": ["Code", "Activity"]
  }
}
```

**Errors:**
| Code | Mô tả |
|------|-------|
| 404 | File not found |
| 400 | Sheet không tồn tại |
| 500 | Processing failed |

---

### GET /download/{file_id}

**Mục đích:** Download file đã xử lý

**Response:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="mapped_abc123.xlsx"

<binary data>
```

**Errors:**
| Code | Mô tả |
|------|-------|
| 404 | Processed file not found |

---

### GET /stations

**Mục đích:** Liệt kê các stations có sẵn

**Response (200):**
```json
[
  {"code": "SGN", "name": "Tân Sơn Nhất", "has_mapping": true},
  {"code": "HAN", "name": "Nội Bài", "has_mapping": false},
  {"code": "DAD", "name": "Đà Nẵng", "has_mapping": false}
]
```

---

## 3. Admin Endpoints

### POST /admin/mappings/import

**Mục đích:** Import mappings từ JSON

**Request Body:**
```json
{
  "station": "SGN",
  "mappings": [
    {"code": "B1", "description": "Nghỉ phép"},
    {"code": "B19", "description": "Đào tạo chuyên sâu"}
  ],
  "replace_existing": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Successfully imported 15 mappings",
  "station": "SGN",
  "imported_count": 15,
  "version": "20241205_143022"
}
```

---

### POST /admin/mappings/import-csv

**Mục đích:** Import mappings từ CSV file

**Request:**
```
Content-Type: multipart/form-data

file: <CSV file>
```

**Query Parameters:**
| Param | Type | Required | Mô tả |
|-------|------|----------|-------|
| station | string | ✅ | Station code |
| replace_existing | bool | ❌ | Thay thế hoàn toàn (default: false) |

**CSV Format:**
```csv
code,description
B1,Nghỉ phép
B19,Đào tạo chuyên sâu
OFF,Nghỉ
```

**Response (200):**
```json
{
  "success": true,
  "message": "Successfully imported 15 mappings from CSV",
  "station": "SGN",
  "imported_count": 15,
  "version": "20241205_143022"
}
```

---

### GET /admin/mappings/{station}

**Mục đích:** Lấy mappings của station

**Query Parameters:**
| Param | Type | Required | Mô tả |
|-------|------|----------|-------|
| version | string | ❌ | Specific version (default: latest) |

**Response (200):**
```json
{
  "station": "SGN",
  "version": "latest",
  "mappings": {
    "B1": "Nghỉ phép",
    "B19": "Đào tạo chuyên sâu",
    "OFF": "Nghỉ"
  },
  "entry_count": 15
}
```

---

### GET /admin/mappings/{station}/versions

**Mục đích:** Liệt kê các versions của mapping

**Response (200):**
```json
[
  {
    "version": "20241205_143022",
    "station": "SGN",
    "created_at": "2024-12-05T14:30:22",
    "entry_count": 15,
    "created_by": "admin"
  },
  {
    "version": "20241204_091500",
    "station": "SGN",
    "created_at": "2024-12-04T09:15:00",
    "entry_count": 12,
    "created_by": null
  }
]
```

---

### DELETE /admin/mappings/{station}

**Mục đích:** Xóa mappings

**Query Parameters:**
| Param | Type | Required | Mô tả |
|-------|------|----------|-------|
| version | string | ❌ | Version cụ thể (xóa tất cả nếu không có) |

**Response (200):**
```json
{
  "success": true,
  "message": "Mappings deleted for station: SGN",
  "version": "all"
}
```

---

### POST /admin/mappings/{station}/validate

**Mục đích:** Validate mappings trước khi import

**Request Body:**
```json
{
  "B1": "Nghỉ phép",
  "B19": "Đào tạo"
}
```

**Response (200):**
```json
{
  "valid": true,
  "issues": [],
  "warnings": ["Found 2 code(s) with different descriptions"],
  "entry_count": 2
}
```

---

### GET /admin/audit-log

**Mục đích:** Xem audit log

**Query Parameters:**
| Param | Type | Mô tả |
|-------|------|-------|
| station | string | Filter by station |
| action | string | Filter by action type |
| limit | int | Max entries (default: 100) |

**Response (200):**
```json
[
  {
    "timestamp": "2024-12-05T14:30:22",
    "action": "mapping_saved",
    "user": null,
    "station": "SGN",
    "details": {
      "version": "20241205_143022",
      "entry_count": 15
    }
  }
]
```

---

## 4. Health Check

### GET /health

**Response (200):**
```json
{
  "status": "healthy",
  "service": "roster-mapper",
  "version": "1.0.0"
}
```

---

## 5. Security Notes

### Phase 1 (Current):
- No authentication
- Internal network only
- File size limit: 10MB

### Phase 2 (Planned):
- API Key authentication
- Rate limiting: 100 requests/minute
- CORS configuration for specific origins

