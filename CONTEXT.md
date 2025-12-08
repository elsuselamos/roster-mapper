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
| **Phase 3** | ⏸️ 0% | Authentication (chưa yêu cầu) |

**Current Version**: `v1.0.0`

---

## 🏗️ Kiến trúc dự án

```
roster-mapper/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── upload.py     # Upload file API + Download (styled/plain)
│   │   ├── admin.py      # Admin API
│   │   ├── batch.py      # Batch processing API
│   │   └── dashboard.py  # Dashboard stats API
│   ├── ui/
│   │   └── routes.py     # Web UI routes (Jinja2)
│   ├── services/
│   │   ├── mapper.py     # Core mapping engine
│   │   ├── excel_processor.py  # Excel read/write + Style preservation
│   │   └── storage.py    # File storage service
│   ├── core/
│   │   ├── config.py     # Pydantic settings
│   │   └── logging.py    # Structured logging
│   ├── db/
│   │   ├── database.py   # DB connection
│   │   └── models.py     # SQLAlchemy models
│   └── main.py           # FastAPI app entry
├── templates/            # Jinja2 HTML templates
├── static/               # CSS, JS, favicon
├── mappings/             # JSON mapping files per station
├── tests/                # Pytest test files
├── docs/                 # Documentation
├── docker/               # Dockerfile
└── requirements.txt      # Python dependencies
```

---

## 🔧 Core Features

### 1. Mapper Engine (`app/services/mapper.py`)

- **Longest-key-first matching**: Ưu tiên match key dài nhất (B19 trước B1)
- **Case-insensitive**: Không phân biệt hoa/thường
- **Multi-code cells**: Hỗ trợ cell có nhiều code (phân cách bởi `/`, `,`, `;`, space)
- **Regex patterns**: Hỗ trợ wildcard và regex trong mapping

```python
mapper = Mapper(station="HAN")
result = mapper.map_cell("B1/TR")  # -> "NP/TR"
```

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

### Access

- Web UI: http://localhost:8000/upload
- API Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin
- Dashboard: http://localhost:8000/dashboard

---

## 📝 Important Notes

1. **Python 3.11+** required (tested with 3.12, 3.13)
2. **Mapping logic**: Code → Code (NOT code → description)
3. **Missing codes**: Giữ nguyên, không tự động thêm
4. **Multi-sheet**: Output file giữ nguyên tên sheets gốc
5. **Style preservation**: Chỉ thay đổi value, giữ nguyên tất cả formatting
6. **Session data**: Stored in `uploads/temp/session_*.json`

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

---

## 📁 Key Files to Review

| File | Purpose |
|------|---------|
| `app/services/mapper.py` | Core mapping logic |
| `app/services/excel_processor.py` | Excel read/write + Style preservation |
| `app/services/storage.py` | File storage (styled/plain support) |
| `app/ui/routes.py` | Web UI routes |
| `app/api/v1/upload.py` | Upload & Download API |
| `mappings/HAN/latest.json` | HAN station mappings |
| `templates/*.html` | Jinja2 templates |

---

## 🐛 Known Issues / TODO

- [ ] Add authentication (currently NO-AUTH)
- [ ] Implement mapping diff viewer in admin
- [ ] Add batch download as ZIP
- [ ] Database persistence for audit logs
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

**Phase 3**: Authentication (chưa yêu cầu, tạm dừng)

---

*Last updated: December 5, 2025*
*Version: 1.0.0*
