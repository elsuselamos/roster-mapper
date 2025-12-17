# 📋 PROJECT CONTEXT - Roster Mapper

> File này chứa toàn bộ context của dự án để tiếp tục trên máy mới.

## 🎯 Mục đích dự án

**Roster Mapper** - Công cụ chuyển đổi mã code roster của Vietjet AMO (Bộ phận Quản lý Bảo dưỡng).

- Đọc file Excel roster từ các station (HAN, SGN, DAD, CXR, HPH, VCA, VII)
- Mapping các code ngắn (B1, TR, OFF, v.v.) sang code chuẩn hoặc mô tả
- Hỗ trợ xử lý **nhiều sheets** trong cùng 1 file
- **Giữ nguyên định dạng** (màu sắc, font, border) của file gốc
- Web UI để upload, preview, và download kết quả

## 👤 Author

- **Website**: vietjetair.com

---

## 📊 Project Status

| Phase | Trạng thái | Mô tả |
|-------|------------|-------|
| **Phase 1** | ✅ 100% | Project skeleton, FastAPI, Mapper engine, tests |
| **Phase 2** | ✅ 100% | Web UI, batch processing, multi-station, style preservation |
| **Phase 2.5** | ✅ 100% | No-DB File Management (v1.2.0 → v1.2.4) |
| **Phase 3** | ⏸️ 0% | Authentication + Database Integration (future) |

**Current Version**: `v1.3.0` (PDF Support + UI Improvements)

---

## 🏗️ Kiến trúc dự án

```
roster-mapper/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── upload.py     # Upload file API + Download (styled/plain) - Deprecated, UI dùng No-DB
│   │   ├── no_db_files.py # No-DB file management API (v1.2.4) - ⭐ Recommended
│   │   ├── admin.py      # Admin API
│   │   ├── batch.py      # Batch processing API
│   │   └── dashboard.py  # Dashboard stats API
│   ├── ui/
│   │   └── routes.py     # Web UI routes (Jinja2)
│   ├── services/
│   │   ├── mapper.py     # Core mapping engine
│   │   ├── excel_processor.py  # Excel read/write + Style preservation
│   │   ├── storage.py    # File storage service
│   │   └── local_storage.py  # Ephemeral storage adapter (Cloud Run)
│   ├── utils/
│   │   └── xls_converter.py  # LibreOffice XLS→XLSX converter
│   ├── core/
│   │   ├── config.py     # Pydantic settings
│   │   └── logging.py    # Structured logging
│   └── main.py           # FastAPI app entry
├── templates/            # Jinja2 HTML templates
├── static/               # CSS, JS, favicon
├── mappings/             # JSON mapping files per station
├── tests/                # Pytest test files
├── docs/                 # Documentation
│   ├── NO_DB_DEPLOYMENT.md  # No-DB deployment guide
│   ├── FILE_LIFECYCLE.md   # Ephemeral file lifecycle
│   └── IMPLEMENTATION_SUMMARY.md  # Implementation summary
├── docker/               # Dockerfile
│   ├── Dockerfile        # Local/Docker Compose
│   └── Dockerfile.cloudrun  # Cloud Run optimized
├── .github/workflows/    # CI/CD
│   └── cloudrun-deploy.yml  # Cloud Run deployment pipeline
└── requirements.txt      # Python dependencies
```

---

## 🔧 Core Features

### 1. Mapper Engine (`app/services/mapper.py`)

- **Longest-key-first matching**: Ưu tiên match key dài nhất (B19 trước B1)
- **Case-insensitive**: Không phân biệt hoa/thường
- **Multi-code cells**: Hỗ trợ cell có nhiều code (phân cách bởi `/`, `,`, `;`, space)
- **Regex patterns**: Hỗ trợ wildcard và regex trong mapping
- **Empty string mapping**: Hỗ trợ map code sang giá trị rỗng `{"BD1": ""}` - code sẽ bị xóa
- **Unmapped = Preserve**: Code không có trong mapping sẽ **giữ nguyên** giá trị gốc (v1.0.1 behavior)

```python
mapper = Mapper(station="HAN")
result = mapper.map_cell("B1/TR")  # -> "NP/TR" (nếu cả 2 có mapping)
result = mapper.map_cell("B1/XYZ")  # -> "NP/" (XYZ không có mapping → rỗng)
```

#### Mapping Behavior Table

| Input | Mapping | Output | Note |
|-------|---------|--------|------|
| `B1` | `{"B1": "NP"}` | `NP` | Exact match |
| `OT` | `{"OT": ""}` | *(empty)* | Map to empty |
| `XYZ` | *(none)* | `XYZ` | Unmapped → preserve original |
| `B1/B2` | `{"B1": "NP", "B2": "SB"}` | `NP/SB` | Multi-code |

### 2. Excel Processing với Style Preservation

- **Giữ nguyên định dạng**: Màu sắc, font, border, merge cells, chiều rộng cột
- **2 loại output**:
  - 🎨 **Styled**: Giữ nguyên format gốc
  - 📄 **Plain**: Text only (giống CSV)

```python
processor = ExcelProcessor()
stats = processor.map_workbook_preserve_style(
    source_path="input.xlsx",
    dest_path="output.xlsx",
    mapper_func=mapper.map_cell,
    sheet_names=["Sheet1", "Sheet2"]
)
```

### 3. Multi-Sheet Processing

- Upload 1 file Excel với nhiều sheets
- Chọn xử lý **tất cả sheets** hoặc **sheets cụ thể**
- Output: 1 file Excel với tất cả sheets đã mapped

### 4. Web UI Flow

```
📤 Upload → ⏳ Loading → 📋 Select Sheets → ⏳ Loading → 👁️ Preview → ⏳ Loading → ✅ Process → 🎉 Results (2 download options)
```

**Loading Spinner**: Hiển thị vòng xoay màu đỏ Vietjet với text mô tả khi:
- Upload files
- Tạo preview
- Bắt đầu mapping

### 5. Mapping Format

File `mappings/{STATION}/latest.json`:
```json
{
  "_meta": {
    "version": "20241205_120000",
    "station": "HAN",
    "entry_count": 74
  },
  "mappings": {
    "B1": "NP",
    "B2": "SB", 
    "TR": "TR",
    "OFF": "OFF"
  }
}
```

**Quy tắc mapping**: FROM code → TO code (không phải code → description)

---

## 📊 Stations & Mappings

| Station | File | Entries |
|---------|------|---------|
| HAN | `mappings/HAN/latest.json` | 74 |
| SGN | `mappings/SGN/latest.json` | 5 (sample) |
| DAD | `mappings/DAD/latest.json` | 5 (sample) |
| CXR | `mappings/CXR/latest.json` | 5 (sample) |
| HPH | `mappings/HPH/latest.json` | 5 (sample) |
| VCA | `mappings/VCA/latest.json` | 5 (sample) |
| VII | `mappings/VII/latest.json` | 5 (sample) |

**HAN có mapping thực tế từ file `mapping_code.xlsx`**

---

## 🧪 Test Files

- `tests/test_mapper.py` - Unit tests cho Mapper
- `tests/test_batch_processing.py` - Batch API tests
- `tests/test_ui_routes.py` - UI route tests
- `tests/test_dashboard_queries.py` - Dashboard tests
- `tests/test_multi_station.py` - Multi-station tests

```bash
# Run tests
source .venv/bin/activate
pytest tests/ -v
```

**Test Results**: 79/79 passed ✅

---

## 🚀 How to Run

### Local Development

```bash
cd roster-mapper
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker-compose up --build
```

### Google Cloud Run (Production - No-DB, Single Instance)

**Hướng dẫn đầy đủ:** Xem `README.md` - Section "🚀 Production Deployment"

**Quick Start (No-DB, Single Instance):**
```bash
# Build và deploy (không cần Cloud SQL)
PROJECT=$(gcloud config get-value project)
SHORT_SHA=$(git rev-parse --short HEAD)

# Build
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions "_SHORT_SHA=$SHORT_SHA"

# Deploy (Single Instance)
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:$SHORT_SHA" \
    --region asia-southeast1 \
    --set-env-vars "STORAGE_DIR=/tmp/uploads,OUTPUT_DIR=/tmp/output,META_DIR=/tmp/meta" \
    --memory 1Gi \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 1
```

**Lưu ý:** Single-instance deployment giải quyết vấn đề multi-instance (files luôn tìm thấy trên cùng instance).

**Tài liệu chi tiết:**
- `README.md` - Step-by-step deployment guide (No-DB)
- `docs/NO_DB_DEPLOYMENT.md` - No-DB deployment guide
- `docs/FILE_LIFECYCLE.md` - Ephemeral file lifecycle documentation

### Access

**Local:**
- Web UI: http://localhost:8000/upload
- API Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin
- Dashboard: http://localhost:8000/dashboard

**Cloud Run:**
- Service URL sẽ được cung cấp sau khi deploy
- Tất cả endpoints tương tự như local

---

## 📝 Important Notes

1. **Python 3.11+** required (tested with 3.12, 3.13)
2. **Mapping logic**: Code → Code (NOT code → description)
3. **Unmapped codes**: **Giữ nguyên** giá trị gốc (v1.0.1 behavior)
4. **Empty mapping**: Hỗ trợ `{"BD1": ""}` để xóa code (mapping thành empty string)
5. **Multi-sheet**: Output file giữ nguyên tên sheets gốc
6. **Style preservation**: Chỉ thay đổi value, giữ nguyên tất cả formatting
7. **Session data**: Stored in `uploads/temp/session_*.json`

> ⚠️ **QUAN TRỌNG**: Phải định nghĩa đầy đủ TẤT CẢ code cần giữ trong mapping!

---

## 🔄 Recent Changes (Dec 2025)

### Phase 2 Completion:
1. ✅ Multi-sheet processing support
2. ✅ Sheet selection page (`/select-sheets`)
3. ✅ Preview with tabs for multiple sheets
4. ✅ **Style Preservation** - Giữ nguyên định dạng file gốc
5. ✅ **2 Download Options** - Styled vs Plain text
6. ✅ Updated footer với link vietjetair.com
7. ✅ Favicon support
8. ✅ Fixed Jinja2 template errors
9. ✅ Updated requirements.txt for Python 3.13
10. ✅ **Loading Spinner** - Hiển thị trạng thái xử lý khi upload/preview/mapping

### v1.0.1 Updates (08/12/2025):
11. ✅ **Import Mapping Modal** - Import với xác nhận, loading spinner
12. ✅ **Support CSV/JSON/Excel** import cho mappings
13. ✅ **Gunicorn timeout 300s** - Xử lý file lớn không bị timeout
14. ✅ Fix `styled_stats` iteration bug
15. ✅ Fix `UnboundLocalError` trong admin.py
16. ✅ **API Docs enabled** - Bật /docs và /redoc trong production
17. ✅ **Empty string mapping** - Hỗ trợ map code sang rỗng `{"OT": ""}`
18. ✅ **Unmapped → Empty** - Code không có mapping sẽ thành rỗng

### v1.0.2 Updates (08/12/2025):
19. ✅ **Behavior Table** - Thêm bảng mapping behavior đầy đủ vào docs
20. ✅ **Documentation Update** - Cập nhật README, CONTEXT, BAO_CAO_TIEN_DO
21. ✅ **Separators Table** - Thêm bảng separators được hỗ trợ
22. ✅ **3 Mapping Formats** - Hướng dẫn JSON/CSV/Excel

### v1.1.0 Updates (08/12/2025) - Cloud Run Deployment:
23. ✅ **Cloud Run Support** - Deploy lên Google Cloud Run với ephemeral storage
24. ✅ **LocalStorage Adapter** - Ephemeral `/tmp` storage cho Cloud Run
25. ✅ **LibreOffice Integration** - XLS → XLSX conversion support
26. ✅ **Dockerfile.cloudrun** - Optimized Dockerfile cho Cloud Run (LibreOffice, port 8080)
27. ✅ **CI/CD Pipeline** - GitHub Actions tự động build & deploy
28. ✅ **Health Endpoint Enhanced** - Storage check, Cloud Run detection
29. ✅ **Deployment Documentation** - `docs/DEPLOY_CLOUDRUN.md` với hướng dẫn chi tiết

---

## 📋 Version History

| Version | Ngày | Thay đổi chính |
|---------|------|----------------|
| v1.0.0 | 05/12/2025 | Phase 2 hoàn thành: Web UI, Multi-sheet, Style preservation, 2 download options |
| v1.0.1 | 08/12/2025 | Import Mapping Modal, Gunicorn timeout, Empty mapping, Unmapped → Empty |
| v1.0.2 | 08/12/2025 | Documentation update, Behavior Table, Separators Table |
| v1.1.0 | 08/12/2025 | **Cloud Run Deployment** - Ephemeral storage, LibreOffice, CI/CD pipeline |
| v1.2.0 | 13/12/2025 | **Ephemeral File Lifecycle (No-DB)** - No-DB File Management API, JSON metadata, auto-deletion, Empty mapping support |
| v1.2.4 | 13/12/2025 | **Single-Instance Deployment** - Giải quyết vấn đề multi-instance, UI routes chuyển sang No-DB endpoints, CI/CD optional |

---

## 📁 Key Files to Review

| File | Purpose |
|------|---------|
| `app/services/mapper.py` | Core mapping logic |
| `app/services/excel_processor.py` | Excel read/write + Style preservation |
| `app/services/storage.py` | File storage (styled/plain support) |
| `app/services/local_storage.py` | Ephemeral storage adapter (Cloud Run) |
| `app/utils/xls_converter.py` | LibreOffice XLS→XLSX converter |
| `app/ui/routes.py` | Web UI routes |
| `app/api/v1/upload.py` | Upload & Download API |
| `app/api/v1/no_db_files.py` | No-DB file management API (v1.2.4) - ⭐ UI routes đã chuyển sang dùng endpoints này |
| `app/api/v1/admin.py` | Admin API - Import CSV/JSON/Excel |
| `mappings/HAN/latest.json` | HAN station mappings |
| `templates/admin.html` | Admin UI với Import Modal |
| `docker/Dockerfile` | Docker config (timeout 300s) |
| `docker/Dockerfile.cloudrun` | Cloud Run optimized Dockerfile |
| `.github/workflows/cloudrun-deploy.yml` | CI/CD pipeline cho Cloud Run |
| `docs/NO_DB_DEPLOYMENT.md` | No-DB deployment guide |
| `docs/FILE_LIFECYCLE.md` | Ephemeral file lifecycle documentation (v1.2.4) |
| `docs/IMPLEMENTATION_SUMMARY.md` | Implementation summary for No-DB files |

---

## 🐛 Known Issues / TODO

- [ ] Add authentication (currently NO-AUTH)
- [ ] Implement mapping diff viewer in admin
- [ ] Add batch download as ZIP
- [x] Ephemeral file lifecycle with auto-deletion (v1.2.0 - No-DB)
- [x] Single-instance deployment (v1.2.4 - Giải quyết multi-instance)
- [ ] More station mappings needed (SGN, DAD, CXR, etc.)

---

## 💬 Conversation Summary

Dự án được xây dựng qua các phase:

**Phase 1**: Project skeleton, FastAPI setup, Mapper engine, basic tests

**Phase 2**: 
- Web UI (Jinja2 + Tailwind + HTMX)
- Batch processing, dashboard, multi-station
- Multi-sheet processing
- **Style preservation** - Giữ nguyên định dạng Excel gốc
- **2 download options** - Styled (giữ format) vs Plain (text only)

**Phase 2.5 (v1.2.0 → v1.2.4)**: 
- **No-DB File Management** - Ephemeral file lifecycle với JSON metadata
- **Cloud Run No-DB Deployment** - Deploy không cần database
- **Single-Instance Deployment** (v1.2.4) - Giải quyết vấn đề multi-instance
- **UI Routes Updated** (v1.2.4) - Chuyển sang dùng No-DB endpoints (`/api/v1/no-db-files/*`)
- **CI/CD Optional** (v1.2.4) - Di chuyển CI/CD ra khỏi bước deploy chính

**Phase 3** (Future - Chưa triển khai):
- **Authentication** - User authentication & authorization
- **Database Integration** - Cloud SQL (Postgres) cho production
  - **Local Development**: PostgreSQL với `DATABASE_URL` (asyncpg driver)
  - **Production**: Google Cloud SQL (Postgres 15) với Cloud SQL Python Connector
  - **Connection Pool**: Configurable (pool_size=3, max_overflow=10)
  - **Security**: Private IP, no public access
  - **Migrations**: Alembic với Cloud SQL Connector
  - **Models**: 
    - `MappingVersion` - Mapping versions per station
    - `AuditLog` - System audit logs
    - `UploadMeta` - Uploaded file metadata
    - `ProcessedFile` - Processed file lifecycle tracking
  - **Tài liệu**: Xem `docs/DB_MIGRATION.md` và `docs/CLOUD_SQL_SETUP.md` (deprecated, sẽ được cập nhật khi triển khai Phase 3)

---

*Last updated: December 13, 2025*
*Version: 1.2.4 (No-DB - Ephemeral File Lifecycle + Empty Mapping Support + Single-Instance Deployment)*
*Highlights: Empty mapping `{"BD1": ""}`, Unmapped preserve (v1.0.1), Single-instance deployment, UI routes dùng No-DB endpoints, CI/CD optional*
