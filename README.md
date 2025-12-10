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
- PostgreSQL 15+
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

**Lỗi "Port 5432 already in use":**
```bash
# PostgreSQL port bị conflict, sửa docker-compose.yml
# Comment dòng ports của service db (không cần expose ra ngoài)
```

#### Bước 4: Dừng services

```bash
# Dừng
docker-compose down

# Dừng và xóa volumes (reset database)
docker-compose down -v
```

Truy cập:
- Web UI: http://localhost:8000/upload
- API Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin
- Dashboard: http://localhost:8000/dashboard
- Adminer (DB Admin): http://localhost:8080 (chỉ với profile: dev)

## ⚙️ Cấu hình Environment

| Biến | Mô tả | Mặc định |
|------|-------|----------|
| `APP_NAME` | Tên ứng dụng | roster-mapper |
| `APP_ENV` | Môi trường (development/production) | development |
| `DEBUG` | Bật chế độ debug | true |
| `LOG_LEVEL` | Mức log (DEBUG/INFO/WARNING/ERROR) | INFO |
| `DATABASE_URL` | Connection string PostgreSQL | postgresql+asyncpg://... |
| `MAPPING_DIR` | Thư mục chứa file mapping | ./mappings |
| `STORAGE_DIR` | Thư mục lưu file upload | ./uploads |
| `AUTO_DETECT_STATION` | Tự động detect station từ filename | true |
| `SECRET_KEY` | Secret key cho security | change-me-in-production |
| `CORS_ORIGINS` | Danh sách origins cho CORS | ["http://localhost:3000"] |

## 📁 Cấu trúc Project

```
roster-mapper/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── upload.py      # Upload & process endpoints
│   │       └── admin.py       # Admin mapping endpoints
│   ├── core/
│   │   ├── config.py          # Pydantic settings
│   │   └── logging.py         # Structured logging
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── database.py        # DB connection
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

### Upload & Process

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/v1/upload` | Upload file Excel |
| GET | `/api/v1/preview/{file_id}` | Preview sheet |
| POST | `/api/v1/process/{file_id}` | Process với mapping |
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

### Upload và process file

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

### Deploy lên server mới

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

### Cập nhật phiên bản mới

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

**Version**: 1.0.2  
**Last Updated**: December 8, 2025

