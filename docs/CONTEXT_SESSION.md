# Deployment Context & Quick Reference

**Last Updated:** 2025-12-13  
**Version:** 1.2.4 (No-DB + Empty Mapping Support + Single-Instance Deployment)  
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

### 2. Cloud Run No-DB (Pilot/MVP) ⭐ **Recommended**

**Phù hợp khi:**
- Pilot / Demo / MVP
- **Single-instance deployment** (min-instances 1, max-instances 1) - **Giải quyết vấn đề multi-instance**
- Không cần audit trail lâu dài
- Muốn đơn giản hóa setup

**Hướng dẫn:** Xem `docs/NO_DB_DEPLOYMENT.md`

**Endpoints:** `/api/v1/no-db-files/*`

**Lưu ý quan trọng:**
- ✅ **UI routes đã chuyển sang dùng No-DB endpoints** để đảm bảo consistency
- ✅ **Single-instance** giải quyết vấn đề files không tìm thấy giữa các instances
- ⚠️ **CI/CD là optional** - không bắt buộc cho deployment

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

### No-DB (`/api/v1/no-db-files/*`) ⭐ **UI Routes đã chuyển sang dùng endpoints này**

- `POST /api/v1/no-db-files/upload` - Upload file
- `POST /api/v1/no-db-files/map` - Run mapping
- `GET /api/v1/no-db-files/download/{file_id}` - Download file (auto-delete sau khi download)
- `GET /api/v1/no-db-files/status/{file_id}` - Check status

**Logging:**
- `file_download_started` - Khi download bắt đầu
- `file_deleted_after_download` - Khi files đã được xóa (background task)

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
5. **Single-instance deployment** - Đảm bảo `--min-instances 1 --max-instances 1` để tránh multi-instance issues

### Image Path Invalid (SHORT_SHA empty)

**Lỗi:** `expected a container image path in the form [hostname/]repo-path[:tag and/or @digest]`

**Nguyên nhân:** Biến `$SHORT_SHA` hoặc `$IMAGE_TAG` chưa được set

**Giải pháp:**
```bash
# Set biến trước khi deploy
PROJECT=$(gcloud config get-value project)
SHORT_SHA=$(git rev-parse --short HEAD)
IMAGE_TAG="$SHORT_SHA"  # Hoặc dùng "latest"
SA_RUNNER_EMAIL="roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Verify
echo "SHORT_SHA: $SHORT_SHA"
echo "IMAGE_TAG: $IMAGE_TAG"

# Deploy với image tag đã verify
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:$IMAGE_TAG" \
    ...
```

### Service Account Already Exists

**Lỗi:** `Service account roster-mapper-runner already exists`

**Giải pháp:**
```bash
# Option 1: Sử dụng service account hiện có (khuyến nghị)
PROJECT=$(gcloud config get-value project)
SA_RUNNER_EMAIL="roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Kiểm tra roles
gcloud projects get-iam-policy $PROJECT \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SA_RUNNER_EMAIL" \
    --format="table(bindings.role)"

# Nếu thiếu role, thêm vào
gcloud projects add-iam-policy-binding $PROJECT \
    --member="serviceAccount:$SA_RUNNER_EMAIL" \
    --role="roles/logging.logWriter"

# Option 2: Xóa và tạo lại (nếu cần reset)
# gcloud iam service-accounts delete $SA_RUNNER_EMAIL --quiet
# gcloud iam service-accounts create roster-mapper-runner ...
```

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
3. **Single-instance deployment:** Dùng `--min-instances 1 --max-instances 1` để giải quyết vấn đề multi-instance với No-DB
4. **UI Routes:** Đã chuyển sang dùng No-DB endpoints (`/api/v1/no-db-files/*`) để đảm bảo consistency
5. **CI/CD:** Optional - chỉ khi cần tự động build & deploy
6. **Logging:** File deletion được log với `file_deleted_after_download` event
7. **Monitoring:** Check logs thường xuyên, setup alerts
8. **Backup:** Enable automated backups cho Cloud SQL (nếu dùng DB)

## 🔄 Recent Changes (v1.2.4)

### Single-Instance Deployment
- ✅ Deploy với `--min-instances 1 --max-instances 1` để giải quyết vấn đề multi-instance
- ✅ Tất cả requests (upload, process, download) đến cùng 1 instance
- ✅ Files luôn tìm thấy trên cùng instance

### UI Routes Updated
- ✅ UI routes (`/upload`, `/process`, `/results`) đã chuyển sang dùng No-DB endpoints internally
- ✅ Đảm bảo consistency và giải quyết vấn đề multi-instance

### CI/CD Optional
- ✅ CI/CD được di chuyển ra khỏi bước deploy chính
- ✅ Chỉ cần khi muốn tự động build & deploy khi push code

### Logging Improvements
- ✅ Thêm detailed logging cho file deletion (`file_deleted_after_download`)
- ✅ Log summary với thông tin: deleted_files, deleted_metadata, total_files_deleted
- ✅ Logs hiển thị rõ ràng trong Cloud Logging

### Documentation Updates
- ✅ Hướng dẫn deploy cho cả Linux/Mac và PowerShell
- ✅ Troubleshooting cho SHORT_SHA và service account đã tồn tại
- ✅ Tất cả tài liệu đã được cập nhật lên v1.2.4

---

**Last Updated:** 2025-12-13  
**Version:** 1.2.4 (No-DB + Empty Mapping Support + Single-Instance Deployment + UI Routes Updated + Logging Improvements)  
**Maintained by:** Vietjet AMO IT Department

---

## 📝 Deployment Commands Quick Reference

### Build & Deploy (Single Instance)

**Linux/Mac:**
```bash
PROJECT=$(gcloud config get-value project)
SHORT_SHA=$(git rev-parse --short HEAD)
SA_RUNNER_EMAIL="roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Build
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions "_SHORT_SHA=$SHORT_SHA"

# Deploy
gcloud run deploy roster-mapper \
    --image "gcr.io/$PROJECT/roster-mapper:$SHORT_SHA" \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account "$SA_RUNNER_EMAIL" \
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
    --min-instances 1 \
    --max-instances 1 \
    --concurrency 80
```

**PowerShell (Windows):**
```powershell
$PROJECT = gcloud config get-value project
$SHORT_SHA = git rev-parse --short HEAD
$SA_RUNNER_EMAIL = "roster-mapper-runner@$PROJECT.iam.gserviceaccount.com"

# Build
gcloud builds submit `
    --config cloudbuild.yaml `
    --substitutions "_SHORT_SHA=$SHORT_SHA"

# Deploy
gcloud run deploy roster-mapper `
    --image "gcr.io/$PROJECT/roster-mapper:$SHORT_SHA" `
    --region asia-southeast1 `
    --platform managed `
    --allow-unauthenticated `
    --service-account $SA_RUNNER_EMAIL `
    --set-env-vars "STORAGE_TYPE=local" `
    --set-env-vars "STORAGE_DIR=/tmp/uploads" `
    --set-env-vars "OUTPUT_DIR=/tmp/output" `
    --set-env-vars "TEMP_DIR=/tmp/temp" `
    --set-env-vars "META_DIR=/tmp/meta" `
    --set-env-vars "APP_ENV=production" `
    --set-env-vars "LOG_LEVEL=INFO" `
    --set-env-vars "DEBUG=false" `
    --set-env-vars "AUTO_DETECT_STATION=true" `
    --set-env-vars "MAX_UPLOAD_SIZE=52428800" `
    --set-env-vars "FILE_TTL_SECONDS=3600" `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --min-instances 1 `
    --max-instances 1 `
    --concurrency 80
```
