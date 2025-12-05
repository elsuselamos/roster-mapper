# DEPLOY - Deployment Guide

---

## 🐳 Docker Deployment

### Build & Run

```bash
cd /home/tiendat/Desktop/roster-mapper

# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Access URLs

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Adminer | http://localhost:8080 (dev profile) |

### With Dev Profile (Adminer)

```bash
docker-compose --profile dev up -d
```

---

## 💻 Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
cd /home/tiendat/Desktop/roster-mapper

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env as needed
```

### Run Development Server

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m app.main
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | roster-mapper | Application name |
| `APP_ENV` | development | Environment (development/production) |
| `DEBUG` | true | Enable debug mode |
| `LOG_LEVEL` | INFO | Logging level |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `DATABASE_URL` | postgresql+asyncpg://... | Database connection |
| `MAPPING_DIR` | ./mappings | Mapping files directory |
| `STORAGE_DIR` | ./uploads | Upload storage directory |
| `TEMP_DIR` | ./temp | Temporary files directory |
| `AUTO_DETECT_STATION` | true | Auto-detect station from filename |
| `SECRET_KEY` | change-me | Secret key for security |

---

## 📁 Volume Mounts

### Docker Compose

```yaml
volumes:
  - ./mappings:/app/mappings    # Mapping files
  - ./uploads:/app/uploads      # Uploaded files
```

### Important Directories

| Directory | Purpose |
|-----------|---------|
| `mappings/` | Station mapping JSON files |
| `uploads/` | Uploaded and processed files |
| `temp/` | Temporary session files |
| `templates/` | Jinja2 HTML templates |
| `static/` | Static assets (CSS, JS) |

---

## 🏥 Health Check

### Endpoint

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "roster-mapper",
  "version": "1.0.0"
}
```

### Docker Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 🔄 Updates

### Update Mappings

1. Prepare CSV/JSON file
2. Go to Admin page: `/admin`
3. Select station tab
4. Click "Import" and upload file

### Update Code

```bash
# Pull latest
git pull

# Rebuild Docker
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 Monitoring

### Logs

```bash
# Docker logs
docker-compose logs -f web

# Local logs (stdout)
uvicorn app.main:app 2>&1 | tee app.log
```

### Dashboard

Access `/dashboard` for:
- Mapping counts per station
- Activity charts
- Recent actions

---

## ⚠️ Production Checklist

- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Change `SECRET_KEY`
- [ ] Configure proper `DATABASE_URL`
- [ ] Set up SSL/TLS (nginx reverse proxy)
- [ ] Configure backup for mappings/
- [ ] Set up log rotation
- [ ] Configure monitoring alerts

---

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Error

```bash
# Check PostgreSQL
docker-compose ps db

# Restart database
docker-compose restart db
```

### Import Error

- Check file format (CSV: from,to columns)
- Check encoding (UTF-8)
- Check for duplicate codes

### Missing Mappings

- Verify mapping file exists: `mappings/{station}/latest.json`
- Check file format and JSON validity
- Reload station in Admin page

