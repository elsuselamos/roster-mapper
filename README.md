# Roster Mapper

**Vietjet — Bộ phận Quản lý Bảo dưỡng**

Ứng dụng chuyển đổi mã roster của các station trong file Excel thành code của HR.

## 📋 Mô tả

Roster Mapper là công cụ hỗ trợ việc chuyển đổi các mã hoạt động (roster codes) trong bảng phân công nhân sự sang mã chuẩn HR. Hệ thống hỗ trợ:

- ✅ Upload file Excel (.xlsx, .xls)
- ✅ **Upload file PDF** - Hỗ trợ convert PDF sang Excel và mapping (v1.3.0)
- ✅ Mapping mã theo từng station (SGN, HAN, DAD, CXR, HPH, VCA, VII)
- ✅ Xử lý multi-code cells (A/B, A,B, A B)
- ✅ Longest-key-first matching (B19 được match trước B1)
- ✅ **Xử lý nhiều sheets** trong cùng 1 file
- ✅ **Giữ nguyên định dạng** (màu sắc, font, border) của file gốc
- ✅ **2 tùy chọn download**: Giữ format gốc hoặc Text only
- ✅ **Import mapping**: Hỗ trợ CSV/JSON/Excel với modal xác nhận
- ✅ **Loading spinner**: UX chuyên nghiệp khi xử lý
- ✅ **Mapping sang rỗng**: Hỗ trợ xóa code không cần thiết `{"BD1": ""}`
- ✅ **Unmapped Preserve**: Code không có trong mapping sẽ **giữ nguyên** giá trị gốc (v1.0.1)
- ✅ Quản lý phiên bản mapping
- ✅ **Web UI với tabs** - Tách riêng Excel và PDF upload (v1.3.0)
- ✅ API RESTful

---

## 🔄 Mapping Behavior (Chi tiết)

### Bảng xử lý Mapping Code

| Cell gốc | Mapping định nghĩa | Kết quả | Giải thích |
|----------|-------------------|---------|------------|
| `B1` | `{"B1": "NP"}` | `NP` | ✅ Exact match |
| `B19` | `{"B1": "NP", "B19": "TR"}` | `TR` | ✅ Longest-key-first (B19 > B1) |
| `b1` | `{"B1": "NP"}` | `NP` | ✅ Case-insensitive |
| `OT` | `{"OT": ""}` | *(rỗng)* | ✅ Map sang empty string |
| `XYZ` | *(không có trong mapping)* | `XYZ` | ⚠️ Unmapped |
| `B1/B2` | `{"B1": "NP", "B2": "SB"}` | `NP/SB` | ✅ Multi-code với separator `/` |
| `B1,B2` | `{"B1": "NP", "B2": "SB"}` | `NP,SB` | ✅ Multi-code với separator `,` |
| `B1 B2` | `{"B1": "NP", "B2": "SB"}` | `NP SB` | ✅ Multi-code với separator ` ` |
| `B1/XYZ` | `{"B1": "NP"}` | `NP/XYZ` | ✅ B1 mapped, XYZ preserved |
| `ABC/DEF` | *(không có)* | `ABC/DEF` | ✅ Cả 2 preserved |
| `^O'.*` | `{"^O'.*": "OT"}` | `OT` | ✅ Regex pattern match |
| `B*` | `{"B*": "B-Series"}` | `B-Series` | ✅ Wildcard pattern |

### Separators được hỗ trợ

| Separator | Ví dụ | Kết quả | Ghi chú |
|-----------|-------|---------|---------|
| `/` | `A/B` | `MappedA/MappedB` | Thông dụng nhất |
| `,` | `A,B` | `MappedA,MappedB` | Hỗ trợ |
| `;` | `A;B` | `MappedA;MappedB` | Hỗ trợ |
| ` ` (space) | `A B` | `MappedA MappedB` | Hỗ trợ nếu rõ ràng |

> **Note**: Hệ thống tự động detect separator đầu tiên tìm thấy trong cell và sử dụng nó để split.

### Định nghĩa Mapping (3 cách)

**1. JSON format:**
```json
{
  "B1": "NP",
  "B2": "SB",
  "OT": "",
  "^TR.*": "Training"
}
```

**2. CSV format:**
```csv
from,to
B1,NP
B2,SB
OT,
```

**3. Excel format:**
| From Code | To Code |
|-----------|---------|
| B1 | NP |
| B2 | SB |
| OT | *(để trống)* |

> ✅ **Lưu ý**: Code không có trong mapping sẽ **giữ nguyên** giá trị gốc. Chỉ khi mapping rõ ràng sang empty `{"BD1": ""}` thì code mới bị xóa.

## 🚀 Cài đặt & Chạy

### Yêu cầu

- Python 3.11+
- Docker & Docker Compose (optional)

### Cách 1: Chạy Local (Development)

```bash
# Clone repository
cd roster-mapper

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc: .venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Copy và cấu hình environment
cp .env.example .env
# Chỉnh sửa .env theo nhu cầu

# Chạy ứng dụng
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Truy cập:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Cách 2: Chạy với Docker Compose

#### Bước 1: Chuẩn bị thư mục và phân quyền

```bash
# Clone repository
git clone https://github.com/elsuselamos/roster-mapper.git
cd roster-mapper

# Tạo các thư mục cần thiết
mkdir -p uploads/uploads uploads/processed uploads/temp

# Phân quyền cho container (container chạy với uid 1000)
sudo chown -R 1000:1000 uploads/ mappings/
sudo chmod -R 755 uploads/ mappings/
```

#### Bước 2: Build và chạy

```bash
# Build và khởi động
docker-compose up -d --build

# Xem logs
docker-compose logs -f web

# Kiểm tra status
docker-compose ps
```

#### Bước 3: Xử lý lỗi thường gặp

**Lỗi "Permission denied":**
```bash
# Chạy lại lệnh phân quyền
sudo chown -R 1000:1000 uploads/ mappings/
docker-compose restart web
```

**Lỗi "Port đã được sử dụng":**
```bash
# Kiểm tra port nào đang dùng
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Sửa port trong docker-compose.yml nếu cần
```

#### Bước 4: Dừng services

```bash
# Dừng
docker-compose down

# Dừng và xóa volumes (reset data)
docker-compose down -v
```

Truy cập:
- Web UI: http://localhost:8000/upload
- API Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin
- Dashboard: http://localhost:8000/dashboard

## ⚙️ Cấu hình Environment

### Local Development

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `APP_NAME` | Tên ứng dụng | roster-mapper |
| `APP_ENV` | Môi trường (development/production) | development |
| `DEBUG` | Bật chế độ debug | true |
| `LOG_LEVEL` | Mức log (DEBUG/INFO/WARNING/ERROR) | INFO |
| `MAPPING_DIR` | Thư mục chứa file mapping | ./mappings |
| `STORAGE_DIR` | Thư mục lưu file upload | ./uploads |
| `OUTPUT_DIR` | Thư mục lưu file output | ./uploads/processed |
| `TEMP_DIR` | Thư mục lưu file tạm | ./uploads/temp |
| `META_DIR` | Thư mục lưu metadata JSON (No-DB) | ./uploads/meta |
| `AUTO_DETECT_STATION` | Tự động detect station từ filename | true |
| `SECRET_KEY` | Secret key cho security | change-me-in-production |
| `CORS_ORIGINS` | Danh sách origins cho CORS | ["http://localhost:3000"] |
| `MAX_UPLOAD_SIZE` | Kích thước upload tối đa (bytes) | 52428800 (50MB) |
| `FILE_TTL_SECONDS` | Thời gian sống của files (seconds) | 3600 (1 hour) |

### Cloud Run Production (No-DB)

| Biến | Giá trị | Mô tả | Required |
|------|---------|-------|----------|
| `STORAGE_TYPE` | `local` | Dùng local filesystem (ephemeral) | ✅ |
| `STORAGE_DIR` | `/tmp/uploads` | Thư mục upload (ephemeral) | ✅ |
| `OUTPUT_DIR` | `/tmp/output` | Thư mục output (ephemeral) | ✅ |
| `TEMP_DIR` | `/tmp/temp` | Thư mục temp (ephemeral) | ✅ |
| `META_DIR` | `/tmp/meta` | Thư mục metadata JSON (ephemeral) | ✅ |
| `PORT` | `8080` | Cloud Run tự set | ✅ |
| `APP_ENV` | `production` | Environment | ✅ |
| `LOG_LEVEL` | `INFO` | Log level | ✅ |
| `DEBUG` | `false` | Disable debug mode | ✅ |
| `AUTO_DETECT_STATION` | `true` | Auto detect station | ✅ |
| `MAX_UPLOAD_SIZE` | `52428800` | Max upload size (50MB) | ⚠️ |
| `FILE_TTL_SECONDS` | `3600` | File TTL (1 hour) | ⚠️ |

**Lưu ý:**
- Tất cả files và metadata lưu trong `/tmp` (ephemeral storage)
- Files tự động xóa sau khi download hoặc TTL expiry
- Metadata lưu trong JSON files, không cần database

## 📁 Cấu trúc Project

```
roster-mapper/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── upload.py      # Upload & process endpoints
│   │       ├── admin.py       # Admin mapping endpoints
│   │       └── no_db_files.py  # No-DB file management API
│   ├── core/
│   │   ├── config.py          # Pydantic settings
│   │   └── logging.py         # Structured logging
│   ├── services/
│   │   ├── mapper.py          # Core mapping logic
│   │   ├── excel_processor.py # Excel read/write
│   │   └── storage.py         # File storage
│   └── main.py                # FastAPI app
├── mappings/
│   ├── global/                # Global fallback mappings
│   ├── SGN/                   # Tân Sơn Nhất
│   ├── HAN/                   # Nội Bài
│   ├── DAD/                   # Đà Nẵng
│   └── ...
├── uploads/                   # Uploaded files
├── tests/
│   └── test_mapper.py         # Unit tests
├── docker/
│   └── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔌 API Endpoints

### No-DB File Management API (Recommended) ⭐

**UI routes đã chuyển sang dùng No-DB endpoints để giải quyết vấn đề multi-instance.**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/no-db-files/upload` | Upload file Excel |
| POST | `/api/v1/no-db-files/map` | Process với mapping |
| GET | `/api/v1/no-db-files/download/{file_id}` | Download file đã xử lý (auto-delete) |
| GET | `/api/v1/no-db-files/status/{file_id}` | Check status |

**Xem chi tiết:** [`docs/API_SPEC.md`](docs/API_SPEC.md) - Section 7: No-DB File Management API

### Legacy Endpoints (Deprecated - UI đã chuyển sang No-DB)

**Lưu ý:** UI routes (`/upload`, `/process`, `/results`) đã được cập nhật để dùng No-DB endpoints internally.

| Method | Endpoint | Mô tả | Status |
|--------|----------|-------|--------|
| POST | `/api/v1/upload` | Upload file Excel (UI) | ⚠️ Deprecated - UI dùng No-DB |
| GET | `/api/v1/preview/{file_id}` | Preview sheet | ✅ Active |
| POST | `/api/v1/process/{file_id}` | Process với mapping (UI) | ⚠️ Deprecated - UI dùng No-DB |
| GET | `/api/v1/download/{file_id}` | Download file đã xử lý | ⚠️ Deprecated - UI dùng No-DB |
| GET | `/api/v1/stations` | Danh sách stations | ✅ Active |
| GET | `/api/v1/results/status` | Check processing status | ✅ Active (dùng No-DB metadata) |

### Admin

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/admin/mappings/import` | Import mappings (JSON) |
| POST | `/api/v1/admin/mappings/import-csv` | Import mappings (CSV) |
| GET | `/api/v1/admin/mappings/{station}` | Get mappings |
| GET | `/api/v1/admin/mappings/{station}/versions` | List versions |
| DELETE | `/api/v1/admin/mappings/{station}` | Delete mappings |
| GET | `/api/v1/admin/audit-log` | Audit log |

## 🧪 Testing

```bash
# Chạy tất cả tests
pytest

# Chạy với coverage
pytest --cov=app --cov-report=html

# Chạy test cụ thể
pytest tests/test_mapper.py -v
```

## 📝 Ví dụ sử dụng

### No-DB API (Recommended)

```bash
# 1. Upload file
curl -X POST "http://localhost:8000/api/v1/no-db-files/upload" \
  -F "file=@roster_SGN.xlsx" \
  -F "station=SGN"

# Response: {"success": true, "upload_id": "abc123", "sheets": ["Sheet1", "Sheet2"], ...}

# 2. Map file
curl -X POST "http://localhost:8000/api/v1/no-db-files/map" \
  -F "upload_id=abc123" \
  -F "station=SGN" \
  -F "download_mode=styled"

# Response: {"success": true, "file_id": "xyz789", "download_url": "/api/v1/no-db-files/download/xyz789", ...}

# 3. Download (file sẽ tự động xóa sau download)
curl -O "http://localhost:8000/api/v1/no-db-files/download/xyz789"

# 4. Check status
curl "http://localhost:8000/api/v1/no-db-files/status/xyz789"
```

### Legacy UI API

```bash
# 1. Upload file
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@roster_SGN.xlsx"

# Response: {"file_id": "abc123", "sheets": ["Sheet1", "Sheet2"]}

# 2. Preview
curl "http://localhost:8000/api/v1/preview/abc123?sheet=Sheet1"

# 3. Process
curl -X POST "http://localhost:8000/api/v1/process/abc123" \
  -F "sheet=Sheet1" \
  -F "station=SGN"

# 4. Download
curl -O "http://localhost:8000/api/v1/download/abc123"
```

### Import mappings

```bash
# Import từ JSON
curl -X POST "http://localhost:8000/api/v1/admin/mappings/import" \
  -H "Content-Type: application/json" \
  -d '{
    "station": "SGN",
    "mappings": [
      {"code": "B1", "description": "Nghỉ phép"},
      {"code": "B19", "description": "Đào tạo chuyên sâu"}
    ]
  }'

# Import từ CSV
curl -X POST "http://localhost:8000/api/v1/admin/mappings/import-csv?station=SGN" \
  -F "file=@mappings.csv"
```

## 🚀 Production Deployment

> **Hướng dẫn đầy đủ để deploy lên Google Cloud Run (No-DB)**

### 📋 Deployment Overview

Hệ thống sử dụng **No-DB architecture** - không cần database:
- ✅ Đơn giản, dễ deploy
- ✅ Metadata lưu trong JSON files (`/tmp/meta/`)
- ✅ Files lưu trong ephemeral storage (`/tmp/`)
- ✅ Auto-deletion sau download hoặc TTL expiry
- ✅ **Single-instance deployment** - Giải quyết vấn đề multi-instance
- ✅ **No-DB Endpoints** - UI routes đã chuyển sang dùng `/api/v1/no-db-files/*`

**Xem chi tiết:** [`docs/NO_DB_DEPLOYMENT.md`](docs/NO_DB_DEPLOYMENT.md)

---

### Option 1: Deploy lên Cloud Run (No-DB) ⭐

### 📋 Prerequisites

- Google Cloud account với billing enabled
- `gcloud` CLI đã được cài đặt và authenticated (`gcloud auth login`)
- Quyền tạo Cloud Run, IAM resources
- Code đã được commit và push lên GitHub (đặc biệt `requirements.txt`)

### ⚠️ Kiểm tra Files trong Repo (QUAN TRỌNG)

**Trước khi deploy, đảm bảo các file sau đã được commit và push:**

```bash
# Kiểm tra files có trong git không
git ls-files | grep -E "(requirements.txt|pyproject.toml|docker/Dockerfile.cloudrun)"

# Nếu thiếu, thêm vào git
git add requirements.txt pyproject.toml docker/Dockerfile.cloudrun app/ mappings/
git commit -m "Add files for Cloud Run deployment"
git push origin main
```

**Files bắt buộc:**
- ✅ `requirements.txt` - **BẮT BUỘC** - Python dependencies
- ✅ `docker/Dockerfile.cloudrun` - Dockerfile cho Cloud Run
- ✅ `app/` - Application code
- ✅ `mappings/` - Mapping files

#### Bước 1: Setup Google Cloud Project

```bash
# 1.1. Tạo hoặc chọn project
gcloud projects create roster-mapper-prod --name="Roster Mapper Production"
# Hoặc chọn project có sẵn:
gcloud config set project YOUR_PROJECT_ID

# 1.2. Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com

# 1.3. Verify project
gcloud config get-value project
```

#### Bước 2: Setup Service Accounts & IAM

**Linux/Mac:**
```bash
# 2.1. Tạo Service Account cho Cloud Run runtime
gcloud iam service-accounts create roster-mapper-runner \
    --display-name="Roster Mapper Cloud Run Service Account"

SA_RUNNER_EMAIL="roster-mapper-runner@$(gcloud config get-value project).iam.gserviceaccount.com"

# 2.2. Grant Logging access
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_RUNNER_EMAIL" \
    --role="roles/logging.logWriter"
```
# xóa IAM user (roster-mapper-iam-user)
SA_RUNNER_EMAIL="roster-mapper-iam-user@$PROJECT.iam.gserviceaccount.com"
gcloud iam service-accounts delete $SA_RUNNER_EMAIL --quiet

**PowerShell (Windows):**
```powershell
# 2.1. Tạo Service Account cho Cloud Run runtime
gcloud iam service-accounts create roster-mapper-runner `
    --display-name="Roster Mapper Cloud Run Service Account"

$PROJECT = gcloud config get-value project
$SA_RUNNER_EMAIL = "roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# 2.2. Grant Logging access
gcloud projects add-iam-policy-binding $PROJECT `
    --member="serviceAccount:$SA_RUNNER_EMAIL" `
    --role="roles/logging.logWriter"
```

#### Bước 3: Cấu hình Secrets và API Keys

**Cách 1: Set Environment Variables trực tiếp (Đơn giản)**

```bash
# Set các biến cần thiết
export SECRET_KEY="your-secret-key-here"
export COMPDF_PUBLIC_KEY="your-compdf-public-key"
export COMPDF_SECRET_KEY="your-compdf-secret-key"  # Optional
```

**Cách 2: Sử dụng Secret Manager (Khuyến nghị cho Production)**

```bash
# 3.1. Tạo secrets trong Secret Manager
echo -n "your-secret-key-here" | gcloud secrets create secret-key --data-file=-
echo -n "your-compdf-public-key" | gcloud secrets create compdf-public-key --data-file=-
echo -n "your-compdf-secret-key" | gcloud secrets create compdf-secret-key --data-file=-

# 3.2. Grant quyền cho Service Account
SA_RUNNER_EMAIL="roster-mapper-runner@$(gcloud config get-value project).iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding secret-key \
    --member="serviceAccount:$SA_RUNNER_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding compdf-public-key \
    --member="serviceAccount:$SA_RUNNER_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding compdf-secret-key \
    --member="serviceAccount:$SA_RUNNER_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

#### Bước 4: Build và Deploy Cloud Run (Single Instance)

**Linux/Mac:**
```bash
# 4.1. Ensure code is up-to-date
git pull origin main

# 4.2. Build Docker image
PROJECT=$(gcloud config get-value project)
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions "_SHORT_SHA=latest"

# 4.3. Deploy to Cloud Run (No-DB, Single Instance)
SA_RUNNER_EMAIL="roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# 4.4. Deploy với Environment Variables (Cách 1)
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:latest" \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account "$SA_RUNNER_EMAIL" \
    --set-env-vars "STORAGE_TYPE=local" \
    --set-env-vars "STORAGE_DIR=/tmp/uploads" \
    --set-env-vars "OUTPUT_DIR=/tmp/output" \
    --set-env-vars "TEMP_DIR=/tmp/temp" \
    --set-env-vars "META_DIR=/tmp/meta" \
    --set-env-vars "APP_ENV=production" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --set-env-vars "DEBUG=false" \
    --set-env-vars "AUTO_DETECT_STATION=true" \
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" \
    --set-env-vars "FILE_TTL_SECONDS=3600" \
    --set-env-vars "SECRET_KEY=$SECRET_KEY" \
    --set-env-vars "COMPDF_PUBLIC_KEY=$COMPDF_PUBLIC_KEY" \
    --set-env-vars "COMPDF_SECRET_KEY=$COMPDF_SECRET_KEY" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 1 \
    --concurrency 80

# 4.5. Hoặc Deploy với Secret Manager (Cách 2 - Khuyến nghị)
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:latest" \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account "$SA_RUNNER_EMAIL" \
    --set-env-vars "STORAGE_TYPE=local" \
    --set-env-vars "STORAGE_DIR=/tmp/uploads" \
    --set-env-vars "OUTPUT_DIR=/tmp/output" \
    --set-env-vars "TEMP_DIR=/tmp/temp" \
    --set-env-vars "META_DIR=/tmp/meta" \
    --set-env-vars "APP_ENV=production" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --set-env-vars "DEBUG=false" \
    --set-env-vars "AUTO_DETECT_STATION=true" \
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" \
    --set-env-vars "FILE_TTL_SECONDS=3600" \
    --set-secrets "SECRET_KEY=secret-key:latest" \
    --set-secrets "COMPDF_PUBLIC_KEY=compdf-public-key:latest" \
    --set-secrets "COMPDF_SECRET_KEY=compdf-secret-key:latest" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 1 \
    --concurrency 80

# 4.6. Set IAM policy (cho phép public access)
gcloud run services add-iam-policy-binding roster-mapper \
    --region asia-southeast1 \
    --member allUsers \
    --role roles/run.invoker

# 4.4. Get service URL
SERVICE_URL=$(gcloud run services describe roster-mapper \
    --region asia-southeast1 \
    --format='value(status.url)')
echo "✅ Service deployed to: $SERVICE_URL"
```

**PowerShell (Windows):**
```powershell
# 4.1. Ensure code is up-to-date
git pull origin main

# 4.2. Set environment variables (Cách 1)
$env:SECRET_KEY = "your-secret-key-here"
$env:COMPDF_PUBLIC_KEY = "your-compdf-public-key"
$env:COMPDF_SECRET_KEY = "your-compdf-secret-key"

# 4.3. Deploy to Cloud Run (No-DB, Single Instance)
$PROJECT = gcloud config get-value project
$SA_RUNNER_EMAIL = "roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Nếu dùng Environment Variables (Cách 1)
gcloud run deploy roster-mapper `
    --image "gcr.io/$PROJECT/roster-mapper:latest" `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --service-account $SA_RUNNER_EMAIL `
    --set-env-vars "STORAGE_TYPE=local" `
    --set-env-vars "STORAGE_DIR=/tmp/uploads" `
    --set-env-vars "OUTPUT_DIR=/tmp/output" `
    --set-env-vars "TEMP_DIR=/tmp/temp" `
    --set-env-vars "META_DIR=/tmp/meta" `
    --set-env-vars "APP_ENV=production" `
    --set-env-vars "LOG_LEVEL=INFO" `
    --set-env-vars "DEBUG=false" `
    --set-env-vars "AUTO_DETECT_STATION=true" `
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" `
    --set-env-vars "FILE_TTL_SECONDS=3600" `
    --set-env-vars "SECRET_KEY=$env:SECRET_KEY" `
    --set-env-vars "COMPDF_PUBLIC_KEY=$env:COMPDF_PUBLIC_KEY" `
    --set-env-vars "COMPDF_SECRET_KEY=$env:COMPDF_SECRET_KEY" `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --min-instances 1 `
    --max-instances 1 `
    --concurrency 80

# Hoặc nếu dùng Secret Manager (Cách 2 - Khuyến nghị)
gcloud run deploy roster-mapper `
    --image "gcr.io/$PROJECT/roster-mapper:latest" `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --service-account $SA_RUNNER_EMAIL `
    --set-env-vars "STORAGE_TYPE=local" `
    --set-env-vars "STORAGE_DIR=/tmp/uploads" `
    --set-env-vars "OUTPUT_DIR=/tmp/output" `
    --set-env-vars "TEMP_DIR=/tmp/temp" `
    --set-env-vars "META_DIR=/tmp/meta" `
    --set-env-vars "APP_ENV=production" `
    --set-env-vars "LOG_LEVEL=INFO" `
    --set-env-vars "DEBUG=false" `
    --set-env-vars "AUTO_DETECT_STATION=true" `
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" `
    --set-env-vars "FILE_TTL_SECONDS=3600" `
    --set-secrets "SECRET_KEY=secret-key:latest" `
    --set-secrets "COMPDF_PUBLIC_KEY=compdf-public-key:latest" `
    --set-secrets "COMPDF_SECRET_KEY=compdf-secret-key:latest" `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --min-instances 1 `
    --max-instances 1 `
    --concurrency 80

# 4.4. Set IAM policy (cho phép public access)
gcloud run services add-iam-policy-binding roster-mapper `
    --region asia-southeast1 `
    --member allUsers `
    --role roles/run.invoker

# 4.5. Get service URL
$SERVICE_URL = gcloud run services describe roster-mapper `
    --region asia-southeast1 `
    --format='value(status.url)'
Write-Host "✅ Service deployed to: $SERVICE_URL"
```

**Lưu ý về Single Instance:**
- ✅ **Giải quyết vấn đề multi-instance**: Tất cả requests đến cùng 1 instance
- ✅ **Files luôn tìm thấy**: Upload, process, download đều trên cùng instance
- ⚠️ **Không có auto-scaling**: Nếu traffic cao, có thể chậm
- ⚠️ **Instance restart**: Files trong `/tmp` sẽ mất (ephemeral storage)
- ⚠️ **Chi phí**: Instance luôn chạy (không scale to zero)

#### Bước 5: Verify Deployment

```bash
# 5.1. Health check
curl "$SERVICE_URL/health"
# Expected: {"status":"ok","storage":{"writable":true},...}

# 5.2. Test No-DB upload API
curl -X POST "$SERVICE_URL/api/v1/no-db-files/upload" \
    -F "file=@test_file.xlsx" \
    -F "station=HAN"

# 5.3. Check logs
gcloud run logs read roster-mapper \
    --region asia-southeast1 \
    --limit 50 \
    --format="table(timestamp,severity,textPayload)"
```


---

### 🔍 Monitoring & Logging

#### Xem logs

```bash
# Stream logs
gcloud run logs read roster-mapper --region asia-southeast1 --follow

# Filter logs
gcloud run logs read roster-mapper \
    --region asia-southeast1 \
    --limit 50 \
    --format="table(timestamp,severity,textPayload)"
```

#### Cloud Logging Console

1. Mở [Cloud Logging](https://console.cloud.google.com/logs)
2. Filter: `resource.type="cloud_run_revision" AND resource.labels.service_name="roster-mapper"`

#### Metrics

```bash
# Xem service status
gcloud run services describe roster-mapper \
    --region asia-southeast1 \
    --format='yaml(status)'
```

---

### 📊 Resource Recommendations (Single Instance)

| Workload | Memory | CPU | Timeout | Notes |
|----------|--------|-----|---------|-------|
| Light (< 5k cells) | 512Mi | 1 | 300s | Đủ cho file nhỏ |
| Medium (5k-20k cells) | 1Gi | 1 | 300s | **Khuyến nghị** |
| Heavy (> 20k cells) | 2Gi | 1-2 | 600s | File lớn, nhiều sheets |

**Lưu ý:** Với single-instance, không cần `--max-instances` (luôn = 1)

**Update resources:**
```bash
# Linux/Mac
gcloud run services update roster-mapper \
    --region asia-southeast1 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600

# PowerShell
gcloud run services update roster-mapper `
    --region asia-southeast1 `
    --memory 2Gi `
    --cpu 2 `
    --timeout 600
```

---

### 🔒 Security Recommendations

#### 1. Restrict Access (Production)

```bash
# Remove public access
gcloud run services update roster-mapper \
    --region asia-southeast1 \
    --no-allow-unauthenticated

# Add specific IAM members
gcloud run services add-iam-policy-binding roster-mapper \
    --region asia-southeast1 \
    --member="user:admin@company.com" \
    --role="roles/run.invoker"
```

#### 2. Custom Domain

```bash
gcloud run domain-mappings create \
    --service roster-mapper \
    --region asia-southeast1 \
    --domain mapper.company.com
```

#### 3. Secret Manager

Đã được cấu hình trong bước 4. Luôn dùng Secret Manager cho sensitive data thay vì env vars.

---

### 📝 Deployment Checklist

#### Pre-deploy
- [ ] Tests pass (`pytest -q`)
- [ ] `requirements.txt` đã commit và push
- [ ] Tất cả code đã commit và push
- [ ] Dockerfile.cloudrun build OK (test local)
- [ ] GCP APIs enabled
- [ ] Service account `roster-mapper-runner` created với `roles/logging.logWriter`
- [ ] GitHub secrets configured (chỉ nếu dùng CI/CD - optional)

#### Post-deploy
- [ ] Service URL accessible
- [ ] `/health` returns 200 với `storage.writable: true`
- [ ] Upload .xlsx works (`/api/v1/no-db-files/upload`)
- [ ] Upload .xls (LibreOffice convert) works
- [ ] Mapping works (`/api/v1/no-db-files/map`)
- [ ] Download works (`/api/v1/no-db-files/download/{file_id}`)
- [ ] Files auto-delete after download
- [ ] Logs visible in Cloud Logging

---

### Option 2: Deploy với Docker Compose (Local/On-premise)

```bash
# 1. Clone repo
git clone https://github.com/elsuselamos/roster-mapper.git
cd roster-mapper

# 2. Tạo thư mục và phân quyền
mkdir -p uploads/uploads uploads/processed uploads/temp
sudo chown -R 1000:1000 uploads/ mappings/
sudo chmod -R 755 uploads/ mappings/

# 3. Build và chạy
docker-compose up -d --build

# 4. Kiểm tra
docker-compose logs -f web
curl http://localhost:8000/health
```

---

### Cập nhật phiên bản mới

**Linux/Mac:**
```bash
# Rebuild và redeploy
PROJECT=$(gcloud config get-value project)
SA_RUNNER_EMAIL="roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Set environment variables (nếu dùng Cách 1)
export SECRET_KEY="your-secret-key-here"
export COMPDF_PUBLIC_KEY="your-compdf-public-key"
export COMPDF_SECRET_KEY="your-compdf-secret-key"  # Optional

# Build
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions "_SHORT_SHA=latest"

# Deploy với Environment Variables (Cách 1)
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:latest" \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account "$SA_RUNNER_EMAIL" \
    --set-env-vars "STORAGE_TYPE=local" \
    --set-env-vars "STORAGE_DIR=/tmp/uploads" \
    --set-env-vars "OUTPUT_DIR=/tmp/output" \
    --set-env-vars "TEMP_DIR=/tmp/temp" \
    --set-env-vars "META_DIR=/tmp/meta" \
    --set-env-vars "APP_ENV=production" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --set-env-vars "DEBUG=false" \
    --set-env-vars "AUTO_DETECT_STATION=true" \
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" \
    --set-env-vars "FILE_TTL_SECONDS=3600" \
    --set-env-vars "SECRET_KEY=$SECRET_KEY" \
    --set-env-vars "COMPDF_PUBLIC_KEY=$COMPDF_PUBLIC_KEY" \
    --set-env-vars "COMPDF_SECRET_KEY=$COMPDF_SECRET_KEY" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 1 \
    --concurrency 80

# Hoặc Deploy với Secret Manager (Cách 2 - Khuyến nghị)
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:latest" \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account "$SA_RUNNER_EMAIL" \
    --set-env-vars "STORAGE_TYPE=local" \
    --set-env-vars "STORAGE_DIR=/tmp/uploads" \
    --set-env-vars "OUTPUT_DIR=/tmp/output" \
    --set-env-vars "TEMP_DIR=/tmp/temp" \
    --set-env-vars "META_DIR=/tmp/meta" \
    --set-env-vars "APP_ENV=production" \
    --set-env-vars "LOG_LEVEL=INFO" \
    --set-env-vars "DEBUG=false" \
    --set-env-vars "AUTO_DETECT_STATION=true" \
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" \
    --set-env-vars "FILE_TTL_SECONDS=3600" \
    --set-secrets "SECRET_KEY=secret-key:latest" \
    --set-secrets "COMPDF_PUBLIC_KEY=compdf-public-key:latest" \
    --set-secrets "COMPDF_SECRET_KEY=compdf-secret-key:latest" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 1 \
    --concurrency 80
```

**PowerShell (Windows):**
```powershell
# Rebuild và redeploy
$PROJECT = gcloud config get-value project
$SA_RUNNER_EMAIL = "roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Set environment variables (nếu dùng Cách 1)
$env:SECRET_KEY = "your-secret-key-here"
$env:COMPDF_PUBLIC_KEY = "your-compdf-public-key"
$env:COMPDF_SECRET_KEY = "your-compdf-secret-key"

# Build
gcloud builds submit `
    --config cloudbuild.yaml `
    --substitutions "_SHORT_SHA=latest"

# Deploy với Environment Variables (Cách 1)
gcloud run deploy roster-mapper `
    --image "gcr.io/$PROJECT/roster-mapper:latest" `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --service-account $SA_RUNNER_EMAIL `
    --set-env-vars "STORAGE_TYPE=local" `
    --set-env-vars "STORAGE_DIR=/tmp/uploads" `
    --set-env-vars "OUTPUT_DIR=/tmp/output" `
    --set-env-vars "TEMP_DIR=/tmp/temp" `
    --set-env-vars "META_DIR=/tmp/meta" `
    --set-env-vars "APP_ENV=production" `
    --set-env-vars "LOG_LEVEL=INFO" `
    --set-env-vars "DEBUG=false" `
    --set-env-vars "AUTO_DETECT_STATION=true" `
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" `
    --set-env-vars "FILE_TTL_SECONDS=3600" `
    --set-env-vars "SECRET_KEY=$env:SECRET_KEY" `
    --set-env-vars "COMPDF_PUBLIC_KEY=$env:COMPDF_PUBLIC_KEY" `
    --set-env-vars "COMPDF_SECRET_KEY=$env:COMPDF_SECRET_KEY" `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --min-instances 1 `
    --max-instances 1 `
    --concurrency 80

# Hoặc Deploy với Secret Manager (Cách 2 - Khuyến nghị)
gcloud run deploy roster-mapper `
    --image "gcr.io/$PROJECT/roster-mapper:latest" `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --service-account $SA_RUNNER_EMAIL `
    --set-env-vars "STORAGE_TYPE=local" `
    --set-env-vars "STORAGE_DIR=/tmp/uploads" `
    --set-env-vars "OUTPUT_DIR=/tmp/output" `
    --set-env-vars "TEMP_DIR=/tmp/temp" `
    --set-env-vars "META_DIR=/tmp/meta" `
    --set-env-vars "APP_ENV=production" `
    --set-env-vars "LOG_LEVEL=INFO" `
    --set-env-vars "DEBUG=false" `
    --set-env-vars "AUTO_DETECT_STATION=true" `
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" `
    --set-env-vars "FILE_TTL_SECONDS=3600" `
    --set-secrets "SECRET_KEY=secret-key:latest" `
    --set-secrets "COMPDF_PUBLIC_KEY=compdf-public-key:latest" `
    --set-secrets "COMPDF_SECRET_KEY=compdf-secret-key:latest" `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --min-instances 1 `
    --max-instances 1 `
    --concurrency 80
```

**Docker Compose:**
```bash
cd roster-mapper
git pull
docker-compose down
docker-compose up -d --build
```

---

### 🔄 CI/CD (Optional - Chỉ khi cần)

Nếu muốn tự động build & deploy khi push code lên GitHub:

#### Bước 1: Setup Service Account cho CI/CD

**Linux/Mac:**
```bash
# Tạo Service Account cho CI/CD
gcloud iam service-accounts create roster-mapper-ci \
    --display-name="Roster Mapper CI/CD Service Account"

SA_CI_EMAIL="roster-mapper-ci@$(gcloud config get-value project).iam.gserviceaccount.com"

# Grant CI/CD roles
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_CI_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_CI_EMAIL" \
    --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_CI_EMAIL" \
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_CI_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# Tạo và download CI service account key
gcloud iam service-accounts keys create ~/roster-mapper-ci-key.json \
    --iam-account=$SA_CI_EMAIL

echo "✅ CI Service Account key saved to: ~/roster-mapper-ci-key.json"
```

**PowerShell (Windows):**
```powershell
# Tạo Service Account cho CI/CD
gcloud iam service-accounts create roster-mapper-ci `
    --display-name="Roster Mapper CI/CD Service Account"

$PROJECT = gcloud config get-value project
$SA_CI_EMAIL = "roster-mapper-ci@$PROJECT.iam.gserviceaccount.com"

# Grant CI/CD roles
gcloud projects add-iam-policy-binding $PROJECT `
    --member="serviceAccount:$SA_CI_EMAIL" `
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT `
    --member="serviceAccount:$SA_CI_EMAIL" `
    --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $PROJECT `
    --member="serviceAccount:$SA_CI_EMAIL" `
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT `
    --member="serviceAccount:$SA_CI_EMAIL" `
    --role="roles/iam.serviceAccountUser"

# Tạo và download CI service account key
gcloud iam service-accounts keys create "$HOME\roster-mapper-ci-key.json" `
    --iam-account=$SA_CI_EMAIL

Write-Host "✅ CI Service Account key saved to: $HOME\roster-mapper-ci-key.json"
```

#### Bước 2: Setup GitHub Secrets

Vào GitHub repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Value | Lấy từ đâu |
|-------------|-------|------------|
| `GCP_PROJECT` | Project ID | `gcloud config get-value project` |
| `GCP_SA_KEY` | Nội dung JSON key | File `~/roster-mapper-ci-key.json` (Linux/Mac) hoặc `$HOME\roster-mapper-ci-key.json` (Windows) |

**Cách lấy GCP_SA_KEY:**

**Linux/Mac:**
```bash
cat ~/roster-mapper-ci-key.json
# Copy toàn bộ output và paste vào GitHub Secret
```

**PowerShell (Windows):**
```powershell
Get-Content "$HOME\roster-mapper-ci-key.json"
# Copy toàn bộ output và paste vào GitHub Secret
```

#### Bước 3: CI/CD Workflow

File `.github/workflows/cloudrun-deploy.yml` đã được cấu hình sẵn. Chỉ cần:
- Push code lên branch `main`
- Workflow sẽ tự động: test → build → deploy

**Lưu ý:** CI/CD workflow sẽ deploy với **single-instance** (min-instances 1, max-instances 1) để đảm bảo consistency.

## 👤 Author

**Vietjet AMO - IT Department**  
Website: [vietjetair.com](https://www.vietjetair.com)

## 📄 License

Internal use only - Vietjet Aviation Joint Stock Company

---

---

## 📚 Tài liệu tham khảo

- **No-DB Deployment**: `docs/NO_DB_DEPLOYMENT.md` - Complete No-DB deployment guide
- **File Lifecycle**: `docs/FILE_LIFECYCLE.md` - Ephemeral file management
- **API Specification**: `docs/API_SPEC.md` - Complete API documentation
- **Deployment Context**: `docs/CONTEXT_SESSION.md` - Quick reference
- **Context**: `CONTEXT.md` - Project context và architecture

---

**Version**: 1.3.0 (PDF Support + UI Improvements)  
**Last Updated**: December 18, 2025  
**Architecture**: No-DB (Metadata in JSON files, Ephemeral storage)  
**Deployment**: Single-instance Cloud Run (min-instances 1, max-instances 1)  
**UI Routes**: Chuyển sang dùng No-DB endpoints (`/api/v1/no-db-files/*`)  
**Mapping Behavior**: Unmapped codes preserve original value (v1.0.1), Empty mapping supported

