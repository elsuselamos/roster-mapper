# No-DB Deployment Guide

**Hướng dẫn triển khai Roster Mapper không cần Database**

---

## 📋 Tổng quan

File `app/api/v1/no_db_files.py` cung cấp các endpoints để xử lý upload → mapping → download **không cần database**. Metadata được lưu trong JSON files thay vì database.

### Khi nào nên dùng No-DB approach?

✅ **Phù hợp khi:**
- Pilot / MVP / Demo
- Single-instance deployment (hoặc chấp nhận rủi ro multi-instance)
- Files chỉ cần tồn tại tạm thời (ephemeral)
- Không cần audit trail lâu dài
- Không cần chia sẻ metadata giữa các instances

❌ **Không phù hợp khi:**
- Production với yêu cầu audit/compliance
- Multi-instance Cloud Run với load balancing
- Cần retry/resume mapping jobs
- Cần lưu trữ lâu dài

---

## 🏗️ Kiến trúc

```
User Upload → /tmp/uploads/<upload_id>_<filename>
     ↓
Mapping → /tmp/output/<file_id>_mapped.xlsx
     ↓
Metadata → /tmp/meta/<file_id>.json
     ↓
Download → Stream file → Delete files + metadata
```

### Metadata Format

File JSON tại `/tmp/meta/<file_id>.json`:

```json
{
  "file_id": "abc123",
  "upload_id": "xyz789",
  "upload_path": "/tmp/uploads/xyz789_file.xlsx",
  "output_path": "/tmp/output/abc123_mapped.xlsx",
  "station": "HAN",
  "created_at": "2025-12-10T12:00:00Z",
  "mapped_at": "2025-12-10T12:01:00Z",
  "expires_at": 1700000000,
  "status": "ready",
  "download_mode": "styled"
}
```

---

## 🚀 Deployment

### Environment Variables

| Variable | Default | Mô tả |
|----------|---------|-------|
| `STORAGE_DIR` | `/tmp/uploads` | Thư mục upload |
| `OUTPUT_DIR` | `/tmp/output` | Thư mục output |
| `META_DIR` | `/tmp/meta` | Thư mục metadata JSON |
| `MAX_UPLOAD_SIZE` | `52428800` (50MB) | Kích thước upload tối đa |
| `FILE_TTL_SECONDS` | `3600` (1 hour) | Thời gian sống của files |

### Cloud Run Deployment

**Không cần Cloud SQL!** Chỉ cần:

```bash
gcloud run deploy roster-mapper \
    --image gcr.io/PROJECT/roster-mapper:latest \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "STORAGE_TYPE=local,STORAGE_DIR=/tmp/uploads,OUTPUT_DIR=/tmp/output,META_DIR=/tmp/meta,MAX_UPLOAD_SIZE=52428800,FILE_TTL_SECONDS=3600" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300
```

**Lưu ý:** Không cần:
- `--add-cloudsql-instances`
- `--set-secrets DB_PASS=...`
- Database environment variables

---

## 📡 API Endpoints

### 1. POST `/api/v1/no-db-files/upload`

Upload file Excel.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/no-db-files/upload" \
  -F "file=@roster.xlsx" \
  -F "station=HAN"
```

**Response:**
```json
{
  "success": true,
  "upload_id": "abc123",
  "filename": "roster.xlsx",
  "file_size": 12345,
  "sheets": ["Sheet1", "Sheet2"],
  "preview": {
    "sheets": ["Sheet1", "Sheet2"],
    "rows_sample": [...],
    "headers": [...]
  },
  "expires_at": "2025-12-10T13:00:00Z"
}
```

### 2. POST `/api/v1/no-db-files/map`

Run mapping trên file đã upload.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/no-db-files/map" \
  -F "upload_id=abc123" \
  -F "station=HAN" \
  -F "download_mode=styled"
```

**Response:**
```json
{
  "success": true,
  "file_id": "xyz789",
  "download_url": "/api/v1/no-db-files/download/xyz789",
  "output_filename": "xyz789_mapped.xlsx",
  "expires_at": "2025-12-10T13:00:00Z"
}
```

### 3. GET `/api/v1/no-db-files/download/{file_id}`

Download file đã mapped. **File sẽ tự động xóa sau khi download hoàn tất.**

**Request:**
```bash
curl -O "http://localhost:8000/api/v1/no-db-files/download/xyz789"
```

### 4. GET `/api/v1/no-db-files/status/{file_id}`

Check status của file.

**Response:**
```json
{
  "file_id": "xyz789",
  "upload_id": "abc123",
  "status": "ready",
  "station": "HAN",
  "created_at": "2025-12-10T12:00:00Z",
  "mapped_at": "2025-12-10T12:01:00Z",
  "expires_at": 1700000000
}
```

---

## ⚙️ Tính năng

### Auto-deletion

- Files và metadata được xóa tự động sau khi download hoàn tất (BackgroundTasks)
- Periodic cleanup task xóa files expired (> TTL) mỗi 10 phút

### TTL (Time To Live)

- Files expire sau `FILE_TTL_SECONDS` (default: 1 hour)
- Cleanup task tự động dọn dẹp expired files

### Security

- Filename sanitization để tránh path traversal
- Size limits để tránh abuse
- Secure headers (`Cache-Control: no-store`)

---

## ⚠️ Rủi ro & Giới hạn

### 1. Multi-instance Cloud Run

**Vấn đề:** Nếu Cloud Run scale đến nhiều instances, metadata không được chia sẻ giữa instances.

**Giải pháp:**
- Dùng sticky sessions (không khuyến nghị)
- Hoặc upgrade lên GCS + signed URLs (không cần DB)
- Hoặc dùng database (Cloud SQL)

### 2. Instance Crash

**Vấn đề:** Nếu instance crash trước khi user download, files sẽ mất.

**Giải pháp:**
- User phải re-upload và re-map
- Hoặc upgrade lên GCS để files durable

### 3. No Audit Trail

**Vấn đề:** Không có lịch sử lâu dài về uploads/mappings.

**Giải pháp:**
- Logs được ghi vào Cloud Logging (stdout)
- Nhưng không có structured queries
- Cần DB nếu cần audit/compliance

---

## 🔄 Migration Path

Nếu sau này cần database:

1. Metadata JSON format đã được thiết kế để dễ migrate
2. Có thể import metadata JSON vào database
3. Switch từ `no_db_files` endpoints sang `files` endpoints (có DB)

---

## 📝 Checklist

### Pre-deploy
- [ ] Code đã được test local
- [ ] Environment variables configured
- [ ] Cloud Run không cần Cloud SQL setup
- [ ] Memory/CPU đủ cho workload

### Post-deploy
- [ ] Upload endpoint works
- [ ] Map endpoint works
- [ ] Download endpoint works và files được xóa
- [ ] Cleanup task chạy (check logs)
- [ ] TTL cleanup hoạt động

---

## 🔗 Related Documentation

- **Full Deployment Guide**: `README.md` - Section "🚀 Production Deployment"
- **Database Migration**: `docs/DB_MIGRATION.md` - Nếu muốn upgrade lên DB
- **File Lifecycle**: `docs/FILE_LIFECYCLE.md` - Ephemeral file management

---

**Last Updated:** 2025-12-10  
**Status:** Production Ready (with limitations)

