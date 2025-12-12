# 🚀 HƯỚNG DẪN TRIỂN KHAI - Roster Mapper

> **Bộ phận**: Quản lý Bảo dưỡng (Maintenance Ops)  
> **Trạng thái**: Phase 2 - HOÀN THÀNH  
> **Phiên bản**: v1.2.0  
> **⚠️ LƯU Ý**: File này dành cho local/Docker deployment. Để deploy lên Cloud Run, xem `README.md` - Section "🚀 Production Deployment"

---

## 📋 MỤC LỤC

1. [Chạy Local (Dev Mode)](#1-chạy-local-dev-mode)
2. [Chạy bằng Docker](#2-chạy-bằng-docker)
3. [CI/CD với Docker Hub](#3-cicd-với-docker-hub)
4. [Triển khai Server nội bộ](#4-triển-khai-server-nội-bộ)
5. [Cấu hình Environment](#5-cấu-hình-environment)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. CHẠY LOCAL (DEV MODE)

### Yêu cầu
- Python 3.11+
- pip

### Các bước

```bash
# Clone repo
git clone https://github.com/elsuselamos/roster-mapper.git
cd roster-mapper

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc: .venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy tests
pytest -q

# Khởi động server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### URLs

| Chức năng | URL |
|-----------|-----|
| Upload | http://localhost:8000/upload |
| Select Sheets | http://localhost:8000/select-sheets |
| Preview | http://localhost:8000/preview |
| Admin Mapping | http://localhost:8000/admin |
| Dashboard | http://localhost:8000/dashboard |
| API Docs | http://localhost:8000/docs |

---

## 2. CHẠY BẰNG DOCKER

### Build image

```bash
# Build từ source
docker build -f docker/Dockerfile -t roster-mapper:local .
```

### Chạy container

```bash
# Tạo folders cho volumes
mkdir -p mappings uploads

# Chạy với volumes
docker run --rm -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/mappings":/data/mappings \
  -v "$(pwd)/uploads":/data/uploads \
  --name roster-mapper \
  roster-mapper:local
```

### Docker Compose (Khuyến nghị)

```bash
# Khởi động tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f web

# Dừng
docker-compose down
```

---

## 3. CI/CD VỚI DOCKER HUB

### Cấu hình GitHub Secrets

Vào repo GitHub → Settings → Secrets and variables → Actions

| Secret | Giá trị |
|--------|---------|
| `DOCKERHUB_USERNAME` | Tên tài khoản Docker Hub |
| `DOCKERHUB_TOKEN` | Access Token từ Docker Hub |

### Tạo Docker Hub Token

1. Đăng nhập https://hub.docker.com
2. Account Settings → Security → New Access Token
3. Đặt tên: `roster-mapper-ci`
4. Copy token và lưu vào GitHub Secrets

### Workflow tự động

File `.github/workflows/ci-dockerhub.yml` sẽ:

1. ✅ Chạy tests khi có PR hoặc push
2. ✅ Build Docker image
3. ✅ Push lên Docker Hub với tags:
   - `latest` (từ main/master)
   - `<commit-sha>`
   - `v0.2.0` (từ tag)

### Trigger build

```bash
# Push code → tự động build
git push origin main

# Tạo release → build với version tag
git tag v0.2.0
git push origin v0.2.0
```

---

## 4. TRIỂN KHAI SERVER NỘI BỘ

### Option A: Pull từ Docker Hub

```bash
# Pull image mới nhất
docker pull YOUR_DOCKERHUB_USERNAME/roster-mapper:latest

# Chạy
docker run -d -p 8000:8000 \
  --env-file .env \
  -v /path/to/mappings:/data/mappings \
  -v /path/to/uploads:/data/uploads \
  --restart unless-stopped \
  --name roster-mapper \
  YOUR_DOCKERHUB_USERNAME/roster-mapper:latest
```

### Option B: Build trực tiếp trên server

```bash
git clone https://github.com/elsuselamos/roster-mapper.git
cd roster-mapper
docker-compose up -d --build
```

### Systemd Service (Linux)

Tạo file `/etc/systemd/system/roster-mapper.service`:

```ini
[Unit]
Description=Roster Mapper Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/roster-mapper
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable roster-mapper
sudo systemctl start roster-mapper
```

---

## 5. CẤU HÌNH ENVIRONMENT

### File `.env`

```bash
# App Settings
APP_NAME=roster-mapper
APP_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Paths
MAPPING_DIR=/data/mappings
STORAGE_DIR=/data/uploads
TEMP_DIR=/data/temp

# Database (optional - dùng SQLite mặc định)
# DATABASE_URL=postgresql://user:pass@localhost:5432/roster_mapper

# CORS
CORS_ORIGINS=["http://localhost:8000","http://your-server-ip:8000"]

# Auto-detect station từ filename
AUTO_DETECT_STATION=true
```

### Volumes quan trọng

| Volume | Mục đích |
|--------|----------|
| `/data/mappings` | Chứa JSON mapping files |
| `/data/uploads` | Chứa uploaded & processed files |
| `/data/temp` | Session data tạm thời |

---

## 6. TROUBLESHOOTING

### Lỗi thường gặp

#### Container không start
```bash
# Kiểm tra logs
docker logs roster-mapper

# Kiểm tra port đã dùng chưa
lsof -i :8000
```

#### Permission denied với volumes
```bash
# Fix permissions
sudo chown -R 1000:1000 mappings uploads
```

#### Tests fail
```bash
# Chạy với verbose
pytest -v --tb=long

# Chạy test cụ thể
pytest tests/test_mapper.py -v
```

#### Import mapping lỗi
- Kiểm tra JSON format đúng chuẩn
- Đảm bảo encoding UTF-8
- Xem logs: `docker logs roster-mapper`

---

## 📝 LƯU Ý QUAN TRỌNG

1. **KHÔNG CÓ AUTHENTICATION** - Tất cả users đều truy cập được
2. **Mapping versioning** - Mọi thay đổi mapping được lưu lịch sử
3. **User = "anonymous"** - Chờ Phase 3 để thêm auth
4. **Backup định kỳ** - Backup folder `mappings/` và `uploads/`

---

## 🔗 Links

- **Repo**: https://github.com/elsuselamos/roster-mapper
- **Docker Hub**: (sau khi setup) https://hub.docker.com/r/YOUR_USERNAME/roster-mapper
- **API Docs**: http://localhost:8000/docs

---

---

## 🔗 Related Documentation

- **Cloud Run Deployment**: `README.md` - Section "🚀 Production Deployment" - Hướng dẫn đầy đủ deploy Cloud Run
- **No-DB Deployment**: `docs/NO_DB_DEPLOYMENT.md` - Deploy không cần database (Pilot/MVP)
- **Database Migration**: `docs/DB_MIGRATION.md` - Cloud SQL setup & migrations
- **File Lifecycle**: `docs/FILE_LIFECYCLE.md` - Ephemeral file management
- **API Specification**: `docs/API_SPEC.md` - Complete API documentation
- **Deployment Context**: `docs/CONTEXT_SESSION.md` - Quick reference deployment

---

*Last updated: December 13, 2025 - v1.2.0 (Ephemeral File Lifecycle - No-DB)*
