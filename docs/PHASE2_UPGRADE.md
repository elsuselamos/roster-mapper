# PHASE 2 UPGRADE - Roster Mapper
**Web UI + Batch Processing + Dashboard + Multi-station**

---

## 🚀 What's New in Phase 2

### 1. Web UI (Jinja2 + Tailwind + HTMX)

| Page | URL | Description |
|------|-----|-------------|
| Upload | `/upload` | Multi-file upload với station selection |
| Preview | `/preview` | Before/after comparison với highlight |
| Results | `/results` | Processing results với download links |
| Admin | `/admin` | Mapping management per station |
| Dashboard | `/dashboard` | Statistics và charts |

### 2. Batch Processing

- Upload nhiều files cùng lúc
- Auto-detect station từ filename
- ZIP download cho all mapped files
- Per-file station override

### 3. Dashboard

- Stats per station (mapping count, status)
- Activity charts (Chart.js)
- Recent activity log
- Time series data

### 4. Multi-Station Support

Tất cả 7 stations đều có sample mappings:
- SGN (Tân Sơn Nhất)
- HAN (Nội Bài) - Full mappings
- DAD (Đà Nẵng)
- CXR (Cam Ranh)
- HPH (Cát Bi)
- VCA (Cần Thơ)
- VII (Vinh)

---

## 📁 New Files

```
app/
├── ui/
│   ├── __init__.py
│   └── routes.py          # Web UI routes
├── api/v1/
│   ├── batch.py           # Batch processing endpoints
│   └── dashboard.py       # Dashboard statistics API

templates/
├── base.html              # Updated with navigation
├── upload.html            # Multi-file upload
├── preview.html           # Before/after comparison
├── results.html           # Download results
├── admin.html             # Mapping management
└── dashboard.html         # Statistics charts

static/
├── css/
└── js/

tests/
├── test_ui_routes.py
├── test_batch_processing.py
├── test_dashboard_queries.py
└── test_multi_station.py

mappings/
├── SGN/latest.json        # Updated
├── HAN/latest.json        # Full mappings
├── DAD/latest.json        # New
├── CXR/latest.json        # New
├── HPH/latest.json        # New
├── VCA/latest.json        # New
└── VII/latest.json        # New

docs/
├── PHASE2_UPGRADE.md      # This file
├── UI_FLOW.md             # UI wireframes
├── API_BATCH.md           # Batch API spec
└── DEPLOY.md              # Deployment guide
```

---

## 🔧 Modified Files

| File | Changes |
|------|---------|
| `app/main.py` | Added UI router, batch, dashboard routes |
| `app/api/v1/__init__.py` | Added batch, dashboard imports |

---

## 🚀 How to Run Phase 2

### Option 1: Local Development

```bash
cd /home/tiendat/Desktop/roster-mapper

# Create venv (if not exists)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access:
- Web UI: http://localhost:8000/upload
- Admin: http://localhost:8000/admin
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs

### Option 2: Docker

```bash
docker-compose up -d --build
```

---

## 📊 API Endpoints (New)

### Batch Processing

```
POST /api/v1/batch-upload
POST /api/v1/batch-map
GET  /api/v1/batch-download
```

### Dashboard

```
GET /api/v1/dashboard/stats
GET /api/v1/dashboard/stats/station/{station}
GET /api/v1/dashboard/stats/actions
GET /api/v1/dashboard/stats/timeline
```

---

## 🧪 Running Tests

```bash
# All tests
pytest tests/ -v

# Phase 2 specific tests
pytest tests/test_ui_routes.py -v
pytest tests/test_batch_processing.py -v
pytest tests/test_dashboard_queries.py -v
pytest tests/test_multi_station.py -v
```

---

## ⚠️ Notes

- **No Authentication** - Phase 2 không có auth (sẽ thêm ở Phase 3)
- **Session Storage** - Sử dụng temp files cho session (simple approach)
- **Charts** - Sử dụng Chart.js CDN
- **CSS** - Tailwind CSS CDN (không cần build)

---

## 🔜 Next: Phase 3

- User authentication
- Role-based access control
- File expiration
- Advanced analytics

