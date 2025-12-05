# Roster Mapper

**Vietjet — Bộ phận Quản lý Bảo dưỡng**

Ứng dụng chuyển đổi mã roster của các stattion trong file Excel thành code của HR.

## 📋 Mô tả

Roster Mapper là công cụ hỗ trợ việc dịch các mã hoạt động (roster codes) trong bảng phân công nhân sự thành các mô tả có ý nghĩa. Hệ thống hỗ trợ:

- ✅ Upload file Excel (.xlsx, .xls)
- ✅ Mapping mã theo từng station (SGN, HAN, DAD, ...)
- ✅ Xử lý multi-code cells (B1/B19 → Nghỉ phép/Đào tạo)
- ✅ Longest-key-first matching (B19 được match trước B1)
- ✅ Quản lý phiên bản mapping
- ✅ API RESTful

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

```bash
# Build và khởi động
docker-compose up -d --build

# Xem logs
docker-compose logs -f web

# Dừng services
docker-compose down
```

Truy cập:
- API: http://localhost:8000
- Adminer (DB Admin): http://localhost:8080 (profile: dev)

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

## 👤 Author

**Dat Nguyen Tien**  
Email: datnguyentien@vietjetair.com

## 📄 License

Internal use only - Vietjet Aviation Joint Stock Company

