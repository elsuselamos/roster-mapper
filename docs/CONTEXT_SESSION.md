# Deployment Context & Quick Reference

**Last Updated:** 2025-12-13  
**Version:** 1.2.0 (No-DB + Empty Mapping Support)  
**Status:** Production Ready

---

## 📋 Tổng quan Deployment Options

### 1. Cloud Run với Cloud SQL (Production) ⭐

**Phù hợp khi:**
- Production environment
- Cần audit trail
- Multi-instance deployment
- Cần persistent metadata

**Hướng dẫn:** Xem `README.md` - Section "🚀 Production Deployment" → "Option 1: Deploy với Cloud SQL"

**Tài liệu chi tiết:**
- `docs/DB_MIGRATION.md` - Database setup & migrations
- `docs/CLOUD_SQL_SETUP.md` - Quick reference

---

### 2. Cloud Run No-DB (Pilot/MVP)

**Phù hợp khi:**
- Pilot / Demo / MVP
- Single-instance deployment
- Không cần audit trail lâu dài
- Muốn đơn giản hóa setup

**Hướng dẫn:** Xem `docs/NO_DB_DEPLOYMENT.md`

**Endpoints:** `/api/v1/no-db-files/*`

---

### 3. Docker Compose (Local/On-premise)

**Phù hợp khi:**
- Development
- On-premise deployment
- Local testing

**Hướng dẫn:** Xem `README.md` - Section "🚀 Production Deployment" → "Option 3: Deploy với Docker Compose"

---

## 🔧 Environment Variables Reference

### Cloud Run (với DB)

| Variable | Required | Default | Mô tả |
|----------|----------|---------|-------|
| `STORAGE_DIR` | ✅ | `/tmp/uploads` | Upload directory |
| `OUTPUT_DIR` | ✅ | `/tmp/output` | Output directory |
| `TEMP_DIR` | ✅ | `/tmp/temp` | Temp directory |
| `INSTANCE_CONNECTION_NAME` | ✅ | - | Cloud SQL connection |
| `DB_USER` | ✅ | - | Database user |
| `DB_PASS` | ✅ | - | Database password (Secret Manager) |
| `DB_NAME` | ✅ | `roster` | Database name |
| `DB_POOL_SIZE` | ⚠️ | `3` | Connection pool size |
| `DB_MAX_OVERFLOW` | ⚠️ | `10` | Max overflow connections |
| `APP_ENV` | ✅ | `production` | Environment |
| `LOG_LEVEL` | ⚠️ | `INFO` | Log level |

### Cloud Run (No-DB)

| Variable | Required | Default | Mô tả |
|----------|----------|---------|-------|
| `STORAGE_DIR` | ✅ | `/tmp/uploads` | Upload directory |
| `OUTPUT_DIR` | ✅ | `/tmp/output` | Output directory |
| `META_DIR` | ✅ | `/tmp/meta` | Metadata JSON directory |
| `MAX_UPLOAD_SIZE` | ⚠️ | `52428800` (50MB) | Max upload size |
| `FILE_TTL_SECONDS` | ⚠️ | `3600` (1h) | File TTL |
| `APP_ENV` | ✅ | `production` | Environment |
| `LOG_LEVEL` | ⚠️ | `INFO` | Log level |

---

## 📡 API Endpoints

### Với Database (`/api/v1/files/*`)

- `POST /api/v1/files/upload` - Upload file
- `POST /api/v1/files/map` - Run mapping
- `GET /api/v1/files/download/{file_id}` - Download file
- `GET /api/v1/files/status/{file_id}` - Check status

### No-DB (`/api/v1/no-db-files/*`)

- `POST /api/v1/no-db-files/upload` - Upload file
- `POST /api/v1/no-db-files/map` - Run mapping
- `GET /api/v1/no-db-files/download/{file_id}` - Download file (auto-delete)
- `GET /api/v1/no-db-files/status/{file_id}` - Check status

---

## 🏗️ Kiến trúc Files

### Với Database

```
Upload → /tmp/uploads/<upload_id>_<filename>
  ↓
Mapping → /tmp/output/<file_id>_mapped.xlsx
  ↓
Metadata → Database (Postgres)
  ↓
Download → Stream file → Update DB status
```

### No-DB

```
Upload → /tmp/uploads/<upload_id>_<filename>
  ↓
Mapping → /tmp/output/<file_id>_mapped.xlsx
  ↓
Metadata → /tmp/meta/<file_id>.json
  ↓
Download → Stream file → Delete files + metadata
```

---

## ✅ Deployment Checklist

### Pre-deploy
- [ ] Code đã được test local
- [ ] Tests pass (`pytest -q`)
- [ ] `requirements.txt` đã commit và push
- [ ] Dockerfile.cloudrun build OK
- [ ] Environment variables configured
- [ ] (Nếu dùng DB) Cloud SQL instance created
- [ ] (Nếu dùng DB) Migrations run thành công
- [ ] (Nếu dùng DB) Service accounts created với đúng roles

### Post-deploy
- [ ] Service URL accessible
- [ ] `/health` returns 200
- [ ] Upload endpoint works
- [ ] Map endpoint works
- [ ] Download endpoint works
- [ ] Files được lưu đúng path
- [ ] (Nếu dùng DB) Database writes successful
- [ ] Logs visible in Cloud Logging

---

## 🐛 Troubleshooting

### Health Check Failed

**Kiểm tra:**
```bash
# Check service status
gcloud run services describe roster-mapper --region asia-southeast1

# Check logs
gcloud run logs read roster-mapper --region asia-southeast1 --limit 50
```

### Database Connection Failed

**Kiểm tra:**
1. Service account có role `roles/cloudsql.client`
2. Cloud SQL instance đã được add vào `--add-cloudsql-instances`
3. `INSTANCE_CONNECTION_NAME` đúng format
4. Secret `DB_PASS` accessible

### Files Not Found (No-DB)

**Kiểm tra:**
1. Files có được lưu vào `/tmp/output/` không?
2. Metadata JSON có trong `/tmp/meta/` không?
3. TTL chưa expire?
4. Instance có bị restart không? (files sẽ mất)

---

## 📚 Tài liệu liên quan

- **README.md** - Hướng dẫn đầy đủ deployment
- **docs/DB_MIGRATION.md** - Database setup & migrations
- **docs/NO_DB_DEPLOYMENT.md** - No-DB deployment guide
- **docs/CLOUD_SQL_SETUP.md** - Quick reference Cloud SQL
- **CONTEXT.md** - Project context tổng thể

---

## 💡 Best Practices

1. **Production:** Luôn dùng Cloud SQL cho audit và durability
2. **Pilot/MVP:** Có thể dùng No-DB để đơn giản hóa
3. **Multi-instance:** Phải dùng DB hoặc GCS, không dùng local files
4. **Monitoring:** Check logs thường xuyên, setup alerts
5. **Backup:** Enable automated backups cho Cloud SQL

---

**Last Updated:** 2025-12-13  
**Version:** 1.2.0 (No-DB + Empty Mapping Support)  
**Maintained by:** Vietjet AMO IT Department
