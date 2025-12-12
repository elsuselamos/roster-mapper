# File Lifecycle Management - Ephemeral Storage

**Version:** 1.0.0  
**Last Updated:** 2025-12-10  
**Status:** Production Ready

---

## 📋 Tổng quan

Hệ thống quản lý file tạm thời (ephemeral) cho Roster Mapper trên Cloud Run. Files chỉ tồn tại trong container `/tmp`, được trả về client qua HTTP, và **tự động xóa ngay sau khi download hoàn tất** hoặc sau TTL (Time To Live).

### Nguyên tắc thiết kế

1. ✅ **Ephemeral Storage**: Tất cả files lưu trong `/tmp` (không persistent)
2. ✅ **Auto-deletion**: Files bị xóa sau download hoặc TTL expiry
3. ✅ **Security**: Sanitize filenames, validate inputs, secure headers
4. ✅ **Metadata Tracking**: Lưu metadata trong database để track lifecycle
5. ✅ **Cleanup Job**: Background task dọn dẹp files bị bỏ quên
6. ✅ **Single-use Downloads**: Mỗi file chỉ download được 1 lần (có thể config)

---

## 🏗️ Kiến trúc

```
User Upload → /tmp/uploads/{upload_id}_{filename}
     ↓
Mapping Process → /tmp/output/{file_id}_mapped.xlsx
     ↓
Download Request → Stream file to client
     ↓
Background Task → Delete upload + output files
     ↓
Cleanup Job (periodic) → Remove expired/orphaned files
```

### Directories

- **`/tmp/uploads/`**: Uploaded files (temporary)
- **`/tmp/output/`**: Processed/mapped files (temporary)
- **Database**: Metadata tracking (PostgreSQL)

### File Naming

- **Upload**: `{upload_id}_{original_filename}`
  - Example: `a1b2c3d4-5678-90ef-ghij-klmnopqrstuv_roster_SGN.xlsx`
- **Output (styled)**: `{file_id}_mapped.xlsx`
  - Example: `b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw_mapped.xlsx`
- **Output (plain)**: `{file_id}_mapped_plain.xlsx`
  - Example: `b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw_mapped_plain.xlsx`

---

## 🔌 API Endpoints

### 1. POST `/api/v1/files/upload`

Upload file để xử lý.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -F "file=@roster.xlsx" \
  -F "station=HAN"
```

**Response:**
```json
{
  "success": true,
  "upload_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "filename": "roster.xlsx",
  "file_size": 123456,
  "sheets": ["Sheet1", "Sheet2"],
  "preview": {
    "sheets": ["Sheet1", "Sheet2"],
    "rows_sample": [...],
    "headers": [...]
  },
  "expires_at": "2025-12-10T18:00:00Z"
}
```

**Behavior:**
- File được lưu vào `/tmp/uploads/{upload_id}_{filename}`
- Metadata lưu vào database (`UploadMeta`)
- TTL: 1 giờ (có thể config)

---

### 2. POST `/api/v1/files/map`

Xử lý file đã upload với mapping.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/files/map" \
  -F "upload_id=a1b2c3d4-5678-90ef-ghij-klmnopqrstuv" \
  -F "station=HAN" \
  -F "download_mode=styled"
```

**Response:**
```json
{
  "success": true,
  "file_id": "b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw",
  "upload_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "download_url": "/api/v1/files/download/b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw",
  "download_url_plain": "/api/v1/files/download/b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw?format=plain",
  "file_size": 234567,
  "expires_at": "2025-12-10T19:00:00Z"
}
```

**Parameters:**
- `upload_id`: ID từ `/upload` endpoint
- `station`: Station code (SGN, HAN, DAD, etc.)
- `download_mode`: `"styled"` (giữ formatting) hoặc `"plain"` (text only)

**Behavior:**
- Load file từ `/tmp/uploads/`
- Process với mapper
- Lưu output vào `/tmp/output/{file_id}_mapped.xlsx`
- Metadata lưu vào database (`ProcessedFile`)

---

### 3. GET `/api/v1/files/download/{file_id}`

Download file đã mapping.

**Request:**
```bash
curl -O "http://localhost:8000/api/v1/files/download/b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw?format=styled"
```

**Query Parameters:**
- `format`: `"styled"` (default) hoặc `"plain"`

**Response:**
- File stream với headers:
  - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - `Content-Disposition: attachment; filename="..."`
  - `Cache-Control: no-store, no-cache, must-revalidate`
  - `Pragma: no-cache`

**Behavior:**
- Stream file đến client
- **Sau khi response hoàn tất**, background task xóa:
  - Output file (`/tmp/output/{file_id}_mapped.xlsx`)
  - Upload file (`/tmp/uploads/{upload_id}_{filename}`)
- Update status trong database: `DELETED`

**⚠️ Lưu ý:**
- File chỉ download được 1 lần (single-use)
- Nếu cần download lại, phải re-run mapping

---

### 4. GET `/api/v1/files/status/{file_id}`

Kiểm tra trạng thái file.

**Request:**
```bash
curl "http://localhost:8000/api/v1/files/status/b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw"
```

**Response:**
```json
{
  "status": "ready",
  "file_id": "b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw",
  "upload_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "station": "HAN",
  "format_type": "styled",
  "file_size": 234567,
  "file_exists": true,
  "created_at": "2025-12-10T17:00:00Z",
  "downloaded_at": null,
  "expires_at": "2025-12-10T19:00:00Z",
  "download_url": "/api/v1/files/download/b2c3d4e5-6789-01fg-hijk-lmnopqrstuvw"
}
```

**Status Values:**
- `ready`: File sẵn sàng download
- `downloading`: Đang được download
- `deleted`: Đã bị xóa
- `expired`: Đã hết hạn (TTL)

---

## 🔄 Lifecycle Flow

### Normal Flow (Success)

```
1. User uploads file
   → POST /api/v1/files/upload
   → File saved: /tmp/uploads/{upload_id}_{filename}
   → Metadata saved: UploadMeta (status=UPLOADED)

2. User starts mapping
   → POST /api/v1/files/map
   → Process file
   → File saved: /tmp/output/{file_id}_mapped.xlsx
   → Metadata saved: ProcessedFile (status=READY)
   → UploadMeta updated: status=COMPLETED

3. User downloads file
   → GET /api/v1/files/download/{file_id}
   → Stream file to client
   → Background task: Delete upload + output files
   → ProcessedFile updated: status=DELETED

4. Cleanup job (periodic)
   → Check expired files
   → Delete files > TTL
   → Update database
```

### Error Flow

```
1. Upload fails
   → HTTP 400/413/500
   → No file saved
   → No metadata

2. Mapping fails
   → HTTP 500
   → UploadMeta: status=FAILED
   → Upload file remains (cleanup job will delete)

3. Download fails (file not found)
   → HTTP 404
   → No deletion
```

### Expired Flow

```
1. File exceeds TTL
   → Cleanup job detects
   → Delete files from disk
   → ProcessedFile: status=EXPIRED → DELETED
```

---

## 🧹 Cleanup Job

Background task chạy định kỳ để dọn dẹp files:

### Chức năng

1. **Expired Files**: Xóa files có `expires_at < now`
2. **Orphaned Files**: Xóa files trên disk không có trong database
3. **Old Files**: Xóa files cũ hơn TTL (1 giờ)

### Configuration

```python
FILE_TTL_HOURS = 1  # Files expire after 1 hour
CLEANUP_INTERVAL_SECONDS = 10 * 60  # Run every 10 minutes
```

### Implementation

Cleanup job được start trong `app/main.py`:

```python
@app.on_event("startup")
async def startup_tasks():
    # Start cleanup task
    asyncio.create_task(periodic_cleanup())
```

---

## 🔒 Security

### File Upload Security

1. **Filename Sanitization**: Loại bỏ ký tự nguy hiểm
   ```python
   def secure_filename(name: str) -> str:
       # Keep alphanumeric, spaces, dots, underscores, hyphens only
   ```

2. **Size Limit**: Giới hạn 50MB (có thể config)
   ```python
   MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
   ```

3. **Extension Validation**: Chỉ cho phép `.xlsx` và `.xls`

4. **Path Traversal Prevention**: UUID prefix ngăn path traversal

### Download Security

1. **Cache Headers**: Ngăn browser cache
   ```
   Cache-Control: no-store, no-cache, must-revalidate
   Pragma: no-cache
   ```

2. **Content-Disposition**: Force download (không preview)
   ```
   Content-Disposition: attachment; filename="..."
   ```

3. **Database Validation**: Kiểm tra file_id trong database trước khi serve

---

## 📊 Database Schema

### UploadMeta

Tracks uploaded files:

```sql
CREATE TABLE upload_meta (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(36) UNIQUE NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100),
    station VARCHAR(10),
    sheet_names JSON,
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
    processed_at TIMESTAMP,
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    processing_stats JSON
);
```

### ProcessedFile

Tracks processed files:

```sql
CREATE TABLE processed_files (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(36) UNIQUE NOT NULL,
    upload_id VARCHAR(36) NOT NULL,
    upload_path VARCHAR(512) NOT NULL,
    output_path VARCHAR(512) NOT NULL,
    output_path_plain VARCHAR(512),
    station VARCHAR(10) NOT NULL,
    format_type VARCHAR(20) NOT NULL DEFAULT 'styled',
    status VARCHAR(20) NOT NULL DEFAULT 'ready',
    file_size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    downloaded_at TIMESTAMP,
    deleted_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

---

## 🧪 Testing

### Unit Tests

```python
# Test upload
def test_upload_file():
    response = client.post("/api/v1/files/upload", files={"file": ...})
    assert response.status_code == 200
    assert "upload_id" in response.json()

# Test mapping
def test_map_file():
    response = client.post("/api/v1/files/map", data={...})
    assert response.status_code == 200
    assert "file_id" in response.json()

# Test download
def test_download_file():
    response = client.get(f"/api/v1/files/download/{file_id}")
    assert response.status_code == 200
    # Verify file deleted after download
    assert not Path(output_path).exists()
```

### Integration Tests

```python
# Full flow test
def test_full_lifecycle():
    # 1. Upload
    upload_resp = client.post("/api/v1/files/upload", ...)
    upload_id = upload_resp.json()["upload_id"]
    
    # 2. Map
    map_resp = client.post("/api/v1/files/map", data={"upload_id": upload_id, ...})
    file_id = map_resp.json()["file_id"]
    
    # 3. Download
    download_resp = client.get(f"/api/v1/files/download/{file_id}")
    assert download_resp.status_code == 200
    
    # 4. Verify deletion
    # Wait for background task
    time.sleep(1)
    assert not Path(upload_path).exists()
    assert not Path(output_path).exists()
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Storage directories (Cloud Run)
STORAGE_DIR=/tmp/uploads
OUTPUT_DIR=/tmp/output
TEMP_DIR=/tmp/temp

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Cloud Run detection
K_SERVICE=roster-mapper  # Set by Cloud Run
```

### Cloud Run Settings

```yaml
# Recommended settings
memory: 1024Mi  # or 2048Mi for large files
timeout: 300s   # 5 minutes
concurrency: 1  # or 2 for lightweight
max_instances: 10
min_instances: 0  # Scale to zero
```

---

## 🐛 Troubleshooting

### File không bị xóa sau download

**Nguyên nhân:**
- Background task chưa chạy
- File đã bị xóa trước đó
- Permission error

**Giải pháp:**
- Check logs: `file_deleted` event
- Verify background task hoạt động
- Check file permissions

### 404 khi download

**Nguyên nhân:**
- File đã bị xóa (single-use)
- File expired (TTL)
- File_id không tồn tại

**Giải pháp:**
- Re-run mapping để tạo file mới
- Check status: `GET /api/v1/files/status/{file_id}`

### Cleanup job không chạy

**Nguyên nhân:**
- Cloud Run instance scale to 0
- Background task bị interrupt

**Giải pháp:**
- Set `min_instances: 1` để giữ instance running
- Hoặc dùng Cloud Scheduler + Cloud Function cho cleanup

---

## 📝 Best Practices

1. **Always check status** trước khi download
2. **Handle errors gracefully** (404, 500, etc.)
3. **Log all operations** để audit
4. **Monitor disk usage** trên Cloud Run
5. **Set appropriate TTL** dựa trên use case
6. **Test cleanup job** định kỳ

---

## 🔮 Future Enhancements

1. **Batch Download**: ZIP nhiều files
2. **Streaming Download**: Cho files lớn
3. **GCS Integration**: Lưu trữ persistent cho production
4. **WebSocket Progress**: Real-time progress updates
5. **Rate Limiting**: Giới hạn requests per IP
6. **Multi-download Support**: Cho phép download nhiều lần (configurable)

---

## 📚 References

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Cloud Run Ephemeral Storage](https://cloud.google.com/run/docs/configuring/ephemeral-storage)
- [File Upload Security](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)

---

## 🔗 Related Documentation

- **Deployment Guide**: `README.md` - Section "🚀 Production Deployment"
- **No-DB Deployment**: `docs/NO_DB_DEPLOYMENT.md` - Deploy không cần database
- **Database Migration**: `docs/DB_MIGRATION.md` - Cloud SQL setup
- **Deployment Context**: `docs/CONTEXT_SESSION.md` - Quick reference
- **API Specification**: `docs/API_SPEC.md` - Complete API docs

---

**Version:** 1.2.4  
**Last Updated:** 2025-12-10  
**Maintainer:** datnguyentien@vietjetair.com

