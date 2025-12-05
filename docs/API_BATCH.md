# API BATCH - Batch Processing Endpoints

---

## Overview

Batch processing cho phép upload và xử lý nhiều files cùng lúc, với output là ZIP archive chứa tất cả mapped files.

---

## Endpoints

### POST /api/v1/batch-upload

Upload nhiều files và nhận kết quả processing.

**Request:**
```
Content-Type: multipart/form-data

files: File[] (required) - Multiple Excel files
station: string (optional) - Common station for all files
auto_detect: boolean (default: true) - Auto-detect station from filename
```

**Response:**
```json
{
  "success": true,
  "message": "Processed 3 files",
  "total_files": 3,
  "successful_files": 3,
  "failed_files": 0,
  "results": [
    {
      "filename": "HAN_ROSTER.xlsx",
      "station": "HAN",
      "success": true,
      "mapped_cells": 2101,
      "unchanged_cells": 2479,
      "error": null
    },
    {
      "filename": "SGN_ROSTER.xlsx",
      "station": "SGN",
      "success": true,
      "mapped_cells": 1500,
      "unchanged_cells": 2000,
      "error": null
    }
  ],
  "download_url": "/api/v1/batch-download"
}
```

---

### POST /api/v1/batch-map

Upload và map files, return ZIP stream.

**Request:**
```
Content-Type: multipart/form-data

files: File[] (required)
station: string (optional)
auto_detect: boolean (default: true)
return_zip: boolean (default: true) - Return ZIP or JSON
```

**Response (return_zip=true):**
```
Content-Type: application/zip
Content-Disposition: attachment; filename=roster_mapped_batch.zip

<ZIP binary data>
```

**Response (return_zip=false):**
```json
{
  "success": true,
  "files_processed": 3,
  "errors": [],
  "download_url": "/api/v1/batch-download"
}
```

---

### GET /api/v1/batch-download

Download the latest batch ZIP file.

**Response:**
```
Content-Type: application/zip
Content-Disposition: attachment; filename=roster_mapped_batch.zip

<ZIP binary data>
```

**Error (404):**
```json
{
  "detail": "No batch file available"
}
```

---

## Usage Examples

### cURL - Batch Upload

```bash
curl -X POST "http://localhost:8000/api/v1/batch-upload" \
  -F "files=@HAN_ROSTER.xlsx" \
  -F "files=@SGN_ROSTER.xlsx" \
  -F "auto_detect=true"
```

### cURL - Batch Map (ZIP)

```bash
curl -X POST "http://localhost:8000/api/v1/batch-map" \
  -F "files=@HAN_ROSTER.xlsx" \
  -F "files=@SGN_ROSTER.xlsx" \
  -o mapped_files.zip
```

### cURL - Specific Station

```bash
curl -X POST "http://localhost:8000/api/v1/batch-map" \
  -F "files=@roster1.xlsx" \
  -F "files=@roster2.xlsx" \
  -F "station=HAN" \
  -F "auto_detect=false" \
  -o mapped_files.zip
```

### Python - Batch Processing

```python
import requests

files = [
    ('files', open('HAN_ROSTER.xlsx', 'rb')),
    ('files', open('SGN_ROSTER.xlsx', 'rb')),
]
data = {'auto_detect': 'true'}

response = requests.post(
    'http://localhost:8000/api/v1/batch-map',
    files=files,
    data=data
)

with open('mapped_files.zip', 'wb') as f:
    f.write(response.content)
```

---

## Station Auto-Detection

Khi `auto_detect=true`, system sẽ detect station từ filename:

| Filename Pattern | Detected Station |
|-----------------|------------------|
| `HAN_ROSTER.xlsx` | HAN |
| `roster_SGN_dec.xlsx` | SGN |
| `DAD_ENG_ROSTER.xlsx` | DAD |
| `roster_december.xlsx` | (fallback to provided station or global) |

---

## ZIP File Structure

```
roster_mapped_batch.zip
├── mapped_HAN_HAN_ROSTER.xlsx
├── mapped_SGN_SGN_ROSTER.xlsx
└── mapped_DAD_DAD_ROSTER.xlsx
```

Filename format: `mapped_{station}_{original_filename}.xlsx`

---

## Error Handling

| Error | HTTP Code | Response |
|-------|-----------|----------|
| No files provided | 400 | `{"detail": "No files provided"}` |
| Invalid file format | 400 | `{"detail": "..."}` |
| No sheets found | 400 | Included in results with error |
| Processing error | 200 | Result with `success: false` |

---

## Performance Notes

- Files are processed sequentially
- ZIP is created in memory for streaming
- Large batches (>10 files) may take longer
- Recommend chunking for very large batches

