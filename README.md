# Roster Mapper

**Vietjet — Bộ phận Quản lý Bảo dưỡng**

Ứng dụng chuyển đổi mã roster của các station trong file Excel thành code của HR.

## 📋 Mô tả

Roster Mapper là công cụ hỗ trợ việc chuyển đổi các mã hoạt động (roster codes) trong bảng phân công nhân sự sang mã chuẩn HR. Hệ thống hỗ trợ:

- ✅ Upload file Excel (.xlsx, .xls)
- ✅ Mapping mã theo từng station (SGN, HAN, DAD, CXR, HPH, VCA, VII)
- ✅ Xử lý multi-code cells (A/B, A,B, A B)
- ✅ Longest-key-first matching (B19 được match trước B1)
- ✅ **Xử lý nhiều sheets** trong cùng 1 file
- ✅ **Giữ nguyên định dạng** (màu sắc, font, border) của file gốc
- ✅ **2 tùy chọn download**: Giữ format gốc hoặc Text only
- ✅ **Import mapping**: Hỗ trợ CSV/JSON/Excel với modal xác nhận
- ✅ **Loading spinner**: UX chuyên nghiệp khi xử lý
- ✅ **Mapping sang rỗng**: Hỗ trợ xóa code không cần thiết `{"OT": ""}`
- ✅ **Unmapped → Empty**: Code không có trong mapping sẽ bị xóa
- ✅ Quản lý phiên bản mapping
- ✅ Web UI thân thiện (Tailwind + HTMX)
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
| `XYZ` | *(không có trong mapping)* | *(rỗng)* | ⚠️ Unmapped → empty |
| `B1/B2` | `{"B1": "NP", "B2": "SB"}` | `NP/SB` | ✅ Multi-code với separator `/` |
| `B1,B2` | `{"B1": "NP", "B2": "SB"}` | `NP,SB` | ✅ Multi-code với separator `,` |
| `B1 B2` | `{"B1": "NP", "B2": "SB"}` | `NP SB` | ✅ Multi-code với separator ` ` |
| `B1/XYZ` | `{"B1": "NP"}` | `NP/` | ⚠️ B1 mapped, XYZ unmapped → empty |
| `ABC/DEF` | *(không có)* | `/` | ⚠️ Cả 2 unmapped → empty |
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

> ⚠️ **Lưu ý quan trọng**: Code không có trong mapping sẽ thành **giá trị rỗng**. Hãy đảm bảo định nghĩa đầy đủ tất cả các code cần giữ lại!

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

### No-DB File Management (Recommended)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/no-db-files/upload` | Upload file Excel |
| POST | `/api/v1/no-db-files/map` | Process với mapping |
| GET | `/api/v1/no-db-files/download/{file_id}` | Download file đã xử lý (auto-delete) |
| GET | `/api/v1/no-db-files/status/{file_id}` | Check status |

**Xem chi tiết:** [`docs/API_SPEC.md`](docs/API_SPEC.md) - Section 7: No-DB File Management API

### Legacy Endpoints (UI)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/upload` | Upload file Excel (UI) |
| GET | `/api/v1/preview/{file_id}` | Preview sheet |
| POST | `/api/v1/process/{file_id}` | Process với mapping (UI) |
| GET | `/api/v1/download/{file_id}` | Download file đã xử lý |
| GET | `/api/v1/stations` | Danh sách stations |

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
- ✅ Phù hợp cho Pilot/MVP và single-instance deployment

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

```bash
# 2.1. Tạo Service Account cho Cloud Run runtime
gcloud iam service-accounts create roster-mapper-runner \
    --display-name="Roster Mapper Cloud Run Service Account"

SA_RUNNER_EMAIL="roster-mapper-runner@$(gcloud config get-value project).iam.gserviceaccount.com"

# 2.2. Grant Logging access
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_RUNNER_EMAIL" \
    --role="roles/logging.logWriter"

# 2.3. Tạo Service Account cho CI/CD (GitHub Actions) - Optional
gcloud iam service-accounts create roster-mapper-ci \
    --display-name="Roster Mapper CI/CD Service Account"

SA_CI_EMAIL="roster-mapper-ci@$(gcloud config get-value project).iam.gserviceaccount.com"

# 2.4. Grant CI/CD roles
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

# 2.5. Tạo và download CI service account key (nếu dùng CI/CD)
gcloud iam service-accounts keys create ~/roster-mapper-ci-key.json \
    --iam-account=$SA_CI_EMAIL

echo "✅ CI Service Account key saved to: ~/roster-mapper-ci-key.json"
echo "⚠️  Add this to GitHub Secrets as GCP_SA_KEY (if using CI/CD)"
```

#### Bước 3: Build và Deploy Cloud Run

```bash
# 3.1. Ensure code is up-to-date
git pull origin main

# 3.2. Build Docker image với Cloud Build
gcloud builds submit \
    --tag gcr.io/$(gcloud config get-value project)/roster-mapper:latest \
    -f docker/Dockerfile.cloudrun \
    .

# Hoặc dùng cloudbuild.yaml (nếu có):
# gcloud builds submit \
#     --config cloudbuild.yaml \
#     --substitutions _SHORT_SHA=$(git rev-parse --short HEAD)

# 3.3. Deploy to Cloud Run (No-DB)
gcloud run deploy roster-mapper \
    --image gcr.io/$(gcloud config get-value project)/roster-mapper:latest \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account $SA_RUNNER_EMAIL \
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
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80

# 3.4. Set IAM policy (cho phép public access)
gcloud run services add-iam-policy-binding roster-mapper \
    --region asia-southeast1 \
    --member allUsers \
    --role roles/run.invoker

# 3.5. Get service URL
SERVICE_URL=$(gcloud run services describe roster-mapper \
    --region asia-southeast1 \
    --format='value(status.url)')
echo "✅ Service deployed to: $SERVICE_URL"
```

#### Bước 4: Verify Deployment

```bash
# 4.1. Health check
curl "$SERVICE_URL/health"
# Expected: {"status":"ok","storage":{"writable":true},...}

# 4.2. Test No-DB upload API
curl -X POST "$SERVICE_URL/api/v1/no-db-files/upload" \
    -F "file=@test_file.xlsx" \
    -F "station=HAN"

# 4.3. Check logs
gcloud run logs read roster-mapper \
    --region asia-southeast1 \
    --limit 50 \
    --format="table(timestamp,severity,textPayload)"
```

#### Bước 5: Setup GitHub Secrets (cho CI/CD) - Optional

Nếu dùng CI/CD, vào GitHub repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Value | Lấy từ đâu |
|-------------|-------|------------|
| `GCP_PROJECT` | Project ID | `gcloud config get-value project` |
| `GCP_SA_KEY` | Nội dung JSON key | File `~/roster-mapper-ci-key.json` (bước 2.5) |

**Cách lấy GCP_SA_KEY:**
```bash
# Copy toàn bộ nội dung file JSON
cat ~/roster-mapper-ci-key.json
# Copy output và paste vào GitHub Secret
```

#### Bước 6: CI/CD Workflow (Automatic) - Optional

File `.github/workflows/cloudrun-deploy.yml` đã được cấu hình sẵn. Chỉ cần:
- Push code lên branch `main`
- Workflow sẽ tự động: test → build → deploy

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

### 🐛 Troubleshooting

#### Lỗi: requirements.txt not found

**Nguyên nhân:** File chưa được commit/push hoặc build context sai

**Giải pháp:**
```bash
# 1. Kiểm tra file có trong git
git ls-files requirements.txt

# 2. Nếu không có, thêm và push
git add requirements.txt
git commit -m "Add requirements.txt"
git push origin main

# 3. Verify trên GitHub web
# 4. Deploy lại với build context đúng (root của repo)
```

#### Lỗi: Substitution key format error

**Nếu gặp:** `substitution key SHORT_SHA does not respect format ^_[A-Z0-9_]+$`

**Giải pháp:**
```bash
# Pull code mới nhất
git pull origin main

# Verify cloudbuild.yaml
cat cloudbuild.yaml | grep "_SHORT_SHA"
# Phải thấy: _SHORT_SHA (có dấu _ ở đầu)

# Dùng đúng format
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _SHORT_SHA=$(git rev-parse --short HEAD)
```

#### Lỗi: Forbidden (403)

**Nếu gặp:** `Error: Forbidden - Your client does not have permission`

**Giải pháp:**
```bash
# Cho phép public access
gcloud run services add-iam-policy-binding roster-mapper \
    --region asia-southeast1 \
    --member allUsers \
    --role roles/run.invoker

# Verify
gcloud run services get-iam-policy roster-mapper --region asia-southeast1
```

#### Bảng lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `COPY failed: file not found: stat requirements.txt` | File chưa commit/push | `git add requirements.txt && git commit && git push` |
| `substitution key SHORT_SHA does not respect format` | Format sai | Dùng `_SHORT_SHA` (có `_` ở đầu) |
| `Error: Forbidden` | IAM policy chưa set | `gcloud run services add-iam-policy-binding ... --member allUsers --role roles/run.invoker` |
| `Container failed to start` | Dockerfile lỗi | Check build logs, verify Dockerfile.cloudrun |
| `Memory limit exceeded` | File quá lớn | Tăng memory: `--memory 2Gi` |
| `Files not found after upload` | Ephemeral storage issue | Check `/tmp` permissions, verify env vars |

---

### 📊 Resource Recommendations

| Workload | Memory | CPU | Max Instances | Timeout |
|----------|--------|-----|---------------|---------|
| Light (< 5k cells) | 512Mi | 1 | 5 | 300s |
| Medium (5k-20k cells) | 1Gi | 1 | 10 | 300s |
| Heavy (> 20k cells) | 2Gi | 2 | 20 | 600s |

**Update resources:**
```bash
gcloud run services update roster-mapper \
    --region asia-southeast1 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 20 \
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
- [ ] GitHub secrets configured (nếu dùng CI/CD)
- [ ] GCP APIs enabled
- [ ] Service accounts created với đúng roles

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

**Cloud Run:**
```bash
# Rebuild và redeploy
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/roster-mapper:latest -f docker/Dockerfile.cloudrun .
gcloud run deploy roster-mapper \
    --image gcr.io/$(gcloud config get-value project)/roster-mapper:latest \
    --region asia-southeast1
```

**Docker Compose:**
```bash
cd roster-mapper
git pull
docker-compose down
docker-compose up -d --build
```

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

**Version**: 1.2.0 (No-DB)  
**Last Updated**: December 13, 2025  
**Architecture**: No-DB (Metadata in JSON files, Ephemeral storage)

