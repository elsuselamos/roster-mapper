# 🧪 Hướng dẫn Test Local - No-DB API

**Hướng dẫn test các endpoints No-DB File Management trên local**

---

## 📋 Prerequisites

1. Python 3.11+ đã cài đặt
2. Dependencies đã được cài đặt: `pip install -r requirements.txt`
3. Server đang chạy trên `http://localhost:8000`

---

## 🚀 Bước 1: Khởi động Server

### Option 1: Chạy với uvicorn (Development)

```bash
cd roster-mapper

# Activate virtual environment (nếu có)
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Khởi động server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Chạy với Docker

```bash
docker-compose up --build
```

**Kiểm tra server đang chạy:**
- Mở browser: http://localhost:8000/docs
- Hoặc test health: `curl http://localhost:8000/health`

---

## 🧪 Bước 2: Test với Script

### Sử dụng test script tự động

```bash
# Test với file có sẵn trong uploads/uploads/
python scripts/test_no_db_api.py

# Test với file cụ thể
python scripts/test_no_db_api.py --file path/to/your/file.xlsx

# Test với server khác
python scripts/test_no_db_api.py --url http://localhost:8000
```

**Script sẽ test:**
1. ✅ Health endpoint
2. ✅ Upload file
3. ✅ Map file
4. ✅ Check status
5. ✅ Download file (và verify auto-deletion)

---

## 🔧 Bước 3: Test Manual với cURL

### 1. Test Health

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "version": "1.2.0"
}
```

### 2. Upload File

```bash
curl -X POST "http://localhost:8000/api/v1/no-db-files/upload" \
  -F "file=@path/to/your/file.xlsx" \
  -F "station=HAN"
```

**Expected response:**
```json
{
  "upload_id": "abc123...",
  "filename": "file.xlsx",
  "preview": {...},
  "meta": {...}
}
```

**Lưu `upload_id` để dùng cho bước tiếp theo!**

### 3. Map File

```bash
curl -X POST "http://localhost:8000/api/v1/no-db-files/map" \
  -F "upload_id=abc123..." \
  -F "station=HAN" \
  -F "download_mode=styled"
```

**Expected response:**
```json
{
  "success": true,
  "file_id": "xyz789...",
  "download_url": "/api/v1/no-db-files/download/xyz789...",
  "output_filename": "xyz789..._mapped.xlsx",
  "expires_at": "2025-12-13T..."
}
```

**Lưu `file_id` để download!**

### 4. Check Status

```bash
curl "http://localhost:8000/api/v1/no-db-files/status/xyz789..."
```

**Expected response:**
```json
{
  "file_id": "xyz789...",
  "status": "ready",
  "station": "HAN",
  "created_at": "2025-12-13T...",
  "mapped_at": "2025-12-13T...",
  "expires_at": 1700000000
}
```

### 5. Download File

```bash
curl -O "http://localhost:8000/api/v1/no-db-files/download/xyz789..."
```

**File sẽ được download và tự động xóa sau khi download xong!**

---

## 🌐 Bước 4: Test với Browser/Postman

### 1. API Documentation

Mở browser: http://localhost:8000/docs

Tìm section **"no-db-files"** và test các endpoints:
- `POST /api/v1/no-db-files/upload`
- `POST /api/v1/no-db-files/map`
- `GET /api/v1/no-db-files/status/{file_id}`
- `GET /api/v1/no-db-files/download/{file_id}`

### 2. Test Flow

1. **Upload**: Chọn file Excel, nhập station (ví dụ: HAN), click "Execute"
2. **Map**: Copy `upload_id` từ response, paste vào form, chọn `download_mode` (styled/plain), click "Execute"
3. **Status**: Copy `file_id` từ response, paste vào path parameter, click "Execute"
4. **Download**: Copy `file_id`, paste vào path parameter, click "Execute" → File sẽ được download

---

## ✅ Checklist Test

### Functional Tests

- [ ] Upload file thành công
- [ ] Upload file với station code
- [ ] Map file với styled mode
- [ ] Map file với plain mode
- [ ] Check status sau khi map
- [ ] Download file thành công
- [ ] File tự động xóa sau download (verify bằng status check → 404)

### Error Handling

- [ ] Upload file quá lớn (>50MB) → 413
- [ ] Upload file không hợp lệ → 400
- [ ] Map với upload_id không tồn tại → 404
- [ ] Download với file_id không tồn tại → 404
- [ ] Download file đã bị xóa → 404

### Metadata Tests

- [ ] Metadata JSON được tạo trong `META_DIR` (default: `/tmp/meta` hoặc `./uploads/meta`)
- [ ] Metadata chứa đầy đủ thông tin (upload_id, file_id, paths, status, timestamps)
- [ ] Metadata được xóa sau khi download

### Cleanup Tests

- [ ] Files trong `/tmp/uploads` được xóa sau download
- [ ] Files trong `/tmp/output` được xóa sau download
- [ ] Metadata JSON được xóa sau download
- [ ] Periodic cleanup job chạy (kiểm tra logs)

---

## 🔍 Kiểm tra Files & Metadata

### Local Development (Windows)

```bash
# Kiểm tra uploads
dir uploads\uploads

# Kiểm tra output
dir uploads\processed

# Kiểm tra metadata (nếu META_DIR = ./uploads/meta)
dir uploads\meta
```

### Local Development (Linux/Mac)

```bash
# Kiểm tra uploads
ls -la uploads/uploads/

# Kiểm tra output
ls -la uploads/processed/

# Kiểm tra metadata
ls -la uploads/meta/
```

### Cloud Run (ephemeral /tmp)

```bash
# SSH vào container (nếu có thể)
ls -la /tmp/uploads/
ls -la /tmp/output/
ls -la /tmp/meta/
```

---

## 🐛 Troubleshooting

### Server không chạy

```bash
# Kiểm tra port 8000 đã được sử dụng
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Kill process nếu cần
# Windows:
taskkill /PID <PID> /F
# Linux/Mac:
kill -9 <PID>
```

### Import Error

```bash
# Đảm bảo đã cài đặt dependencies
pip install -r requirements.txt

# Kiểm tra virtual environment
python --version
which python  # Linux/Mac
where python  # Windows
```

### File không tìm thấy

```bash
# Kiểm tra STORAGE_DIR, OUTPUT_DIR, META_DIR trong .env hoặc environment
# Default:
# STORAGE_DIR=./uploads
# OUTPUT_DIR=./uploads/processed
# META_DIR=./uploads/meta
```

### Metadata không được tạo

- Kiểm tra quyền ghi vào thư mục metadata
- Kiểm tra logs: `tail -f logs/app.log` (nếu có)
- Kiểm tra console output khi chạy server

---

## 📊 Expected Results

### Successful Flow

```
1. Upload → upload_id: "abc123..."
2. Map → file_id: "xyz789..."
3. Status → status: "ready"
4. Download → File downloaded, status → 404 (deleted)
```

### File Locations (Local Dev)

```
uploads/
├── uploads/
│   └── abc123..._file.xlsx  (tạm thời, sẽ bị xóa)
├── processed/
│   └── xyz789..._mapped.xlsx  (tạm thời, sẽ bị xóa)
└── meta/
    └── xyz789....json  (tạm thời, sẽ bị xóa)
```

---

## 📝 Notes

- **Files là ephemeral**: Tất cả files sẽ bị xóa sau download hoặc sau TTL (default: 1 hour)
- **Metadata trong JSON**: Không dùng database, metadata lưu trong JSON files
- **Background deletion**: Files được xóa bằng BackgroundTasks sau khi response hoàn tất
- **Periodic cleanup**: Cleanup job chạy mỗi 10 phút để xóa expired files

---

**Last Updated:** 2025-12-13  
**Version:** v1.2.0

