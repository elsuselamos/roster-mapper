# BLUEPRINT – Roster Mapper
**Kiến trúc tổng thể dự án**

---

## 1. Tóm tắt dự án

**Roster Mapper** là ứng dụng web nội bộ cho Bộ phận Quản lý Bảo dưỡng (AMO) Vietjet, giúp:
- Chuyển đổi mã roster trong file Excel thành mô tả tiếng Việt
- Quản lý bộ mapping codes theo từng trạm (station)
- Hỗ trợ longest-key-first matching (B19 trước B1) và multi-code cells (B1/B19)

**Loại dự án:** Web Application (API + Optional UI)

---

## 2. Mục tiêu & KPI chính

### Mục tiêu chức năng:
- Upload file Excel → Process → Download mapped file
- CRUD mapping codes theo station
- Version control cho mappings

### Mục tiêu trải nghiệm:
- 3-click workflow: Upload → Process → Download
- Zero learning curve cho end users
- Clear error messages bằng tiếng Việt

### Mục tiêu kỹ thuật:
- Response time < 2s cho file < 5MB
- 99.9% mapping accuracy
- Support 7 stations đồng thời

---

## 3. Các Module chính

### Module A – Upload & Process
- **Mục đích:** Xử lý file Excel từ user
- **Ai dùng:** Nhân viên lập kế hoạch
- **Input:** File .xlsx/.xls
- **Output:** File Excel đã mapped, statistics

### Module B – Mapper Engine
- **Mục đích:** Core mapping logic
- **Ai dùng:** Module A gọi internal
- **Input:** DataFrame + Mapping dict
- **Output:** Mapped DataFrame + Stats

### Module C – Storage Service
- **Mục đích:** Quản lý file và mapping versions
- **Ai dùng:** Tất cả modules
- **Input/Output:** Files, JSON mappings

### Module D – Admin Management
- **Mục đích:** Import/Export/CRUD mappings
- **Ai dùng:** Admin/IT
- **Input:** CSV/JSON mapping files
- **Output:** Updated mapping versions

---

## 4. Flow người dùng chính

### Flow 1 – Upload & Process (End User)
```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│ Upload  │ → │ Preview  │ → │ Process │ → │ Download │
│  File   │    │  Sheet   │    │  Map    │    │  Result  │
└─────────┘    └──────────┘    └─────────┘    └──────────┘
```

1. User upload file Excel
2. Hệ thống hiển thị danh sách sheets
3. User chọn sheet, preview data
4. User chọn station (hoặc auto-detect)
5. Hệ thống apply mapping
6. User download file đã xử lý

### Flow 2 – Import Mappings (Admin)
```
┌─────────┐    ┌──────────┐    ┌─────────┐
│ Upload  │ → │ Validate │ → │  Save   │
│  CSV    │    │ Mappings │    │ Version │
└─────────┘    └──────────┘    └─────────┘
```

1. Admin upload CSV với columns: code, description
2. Hệ thống validate format và conflicts
3. Admin confirm import
4. Hệ thống lưu version mới

---

## 5. Intents / Slots / Actions

### 5.1. Intents (ý định chính)

| Intent | Mô tả |
|--------|-------|
| `upload_roster` | User muốn upload file roster |
| `process_mapping` | User muốn áp dụng mapping |
| `download_result` | User muốn tải file kết quả |
| `import_mappings` | Admin muốn import bộ mapping mới |
| `view_mappings` | User/Admin muốn xem mapping hiện tại |

### 5.2. Slots (thông tin cần thiết)

| Slot | Type | Required | Mô tả |
|------|------|----------|-------|
| `file` | File | ✅ | File Excel upload |
| `sheet_name` | string | ✅ | Tên sheet cần xử lý |
| `station` | enum | ❌ | Station code (auto-detect nếu không có) |
| `columns` | string[] | ❌ | Columns cần map (auto-detect nếu không có) |

### 5.3. Actions (operations)

```python
# Upload & Process
save_uploaded_file(file) -> (file_id, path)
get_sheet_names(file_path) -> List[str]
preview_sheet(file_path, sheet, rows) -> PreviewData
detect_station(file_path) -> Optional[str]
map_dataframe(df, columns, station) -> (DataFrame, Stats)
save_processed_file(file_id, df) -> path

# Mapping Management
load_mapping(station, version) -> Dict[str, str]
save_mapping(station, mappings) -> version
validate_mappings(mappings) -> ValidationResult
list_mapping_versions(station) -> List[VersionInfo]
```

---

## 6. Dữ liệu & Tích hợp

### Nguồn dữ liệu chính:
- **File uploads:** Local filesystem (./uploads/)
- **Mappings:** JSON files (./mappings/{station}/)
- **Metadata:** PostgreSQL database

### Bảng/Collection quan trọng:

#### PostgreSQL Tables:
```sql
-- Mapping versions
mapping_versions (id, station, version, mappings, entry_count, is_active, created_at)

-- Upload metadata  
upload_meta (id, file_id, filename, station, status, processed_at)

-- Audit log
audit_logs (id, timestamp, action, station, user, details)
```

### Tích hợp:
- **Không cần tích hợp bên ngoài** trong Phase 1
- Phase 2: Có thể tích hợp với AMOS (Aircraft Maintenance System)

---

## 7. Kiến trúc kỹ thuật

### Tech Stack:
```
┌─────────────────────────────────────────┐
│           Frontend (Optional)           │
│         Jinja2 Templates + HTMX         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│              FastAPI Backend            │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │ Upload  │ │ Mapper  │ │  Admin   │  │
│  │   API   │ │ Service │ │   API    │  │
│  └─────────┘ └─────────┘ └──────────┘  │
│  ┌─────────────────────────────────┐   │
│  │         Storage Service         │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐      ┌───────────────┐
│  PostgreSQL   │      │  File System  │
│   (Metadata)  │      │   (Uploads)   │
└───────────────┘      └───────────────┘
```

### Components:
- **Backend:** FastAPI + Python 3.11
- **Database:** PostgreSQL 15 + SQLAlchemy async
- **File Processing:** pandas + openpyxl
- **Deployment:** Docker + docker-compose
- **Server:** Gunicorn + UvicornWorker

---

## 8. Phase & Gates

### Phase 1 – MVP (2 tuần)

**Mục tiêu:** Core functionality hoạt động end-to-end

**Modules cần có:**
- Upload API ✅
- Mapper Engine ✅  
- Storage Service ✅
- Admin API (basic) ✅

**Gates:**

| Gate | Tên | Tiêu chí |
|------|-----|----------|
| G1 | Project Setup | Cấu trúc project, Docker build thành công |
| G2 | Upload Flow | Upload → Preview → Download hoạt động |
| G3 | Mapping Engine | B1/B19 test pass, multi-code test pass |
| G4 | Admin Import | Import CSV mapping thành công |
| G5 | Integration Test | End-to-end flow với real data |

### Phase 2 – Enhancement (2 tuần)

**Mục tiêu:** Production-ready với monitoring

- [ ] Web UI (Jinja2 + Tailwind)
- [ ] User authentication
- [ ] Dashboard & statistics
- [ ] Batch processing
- [ ] API documentation (Swagger)

### Phase 3 – Scale (TBD)

- [ ] Multi-tenant support
- [ ] AMOS integration
- [ ] Automated mapping suggestions (AI)

