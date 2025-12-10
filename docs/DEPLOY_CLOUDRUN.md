# 🚀 Deploy to Google Cloud Run

## Hướng dẫn triển khai Roster Mapper v1.0.2 lên Google Cloud Run

---

## 📋 Tổng quan

| Thông tin | Chi tiết |
|-----------|----------|
| **Platform** | Google Cloud Run (managed) |
| **Storage** | Ephemeral `/tmp` (không dùng GCS) |
| **Port** | 8080 (Cloud Run default) |
| **Region** | asia-southeast1 (khuyến nghị) |
| **Version** | 1.1.0 |

---

## 📦 Yêu cầu trước khi deploy

### 1. Google Cloud Project

```bash
# Tạo project mới hoặc chọn project có sẵn
gcloud projects create roster-mapper-prod --name="Roster Mapper Production"
gcloud config set project roster-mapper-prod

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Service Account (cho CI/CD)

```bash
# Tạo Service Account
gcloud iam service-accounts create roster-mapper-ci \
    --display-name="Roster Mapper CI/CD"

# Gán roles
SA_EMAIL="roster-mapper-ci@$(gcloud config get-value project).iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# Tạo và download key
gcloud iam service-accounts keys create ~/roster-mapper-ci-key.json \
    --iam-account=$SA_EMAIL

echo "Key saved to ~/roster-mapper-ci-key.json"
```

### 3. GitHub Secrets

Thêm vào GitHub repo (Settings → Secrets and variables → Actions):

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT` | Google Cloud project ID |
| `GCP_SA_KEY` | Nội dung file JSON key (copy toàn bộ) |

---

## 🛠️ Deploy thủ công (Manual)

### Option 1: Dùng Cloud Build

```bash
cd roster-mapper

# Build image với Cloud Build
gcloud builds submit \
    --tag gcr.io/$(gcloud config get-value project)/roster-mapper:1.1.0 \
    -f docker/Dockerfile.cloudrun \
    .

# Deploy lên Cloud Run
gcloud run deploy roster-mapper \
    --image gcr.io/$(gcloud config get-value project)/roster-mapper:1.1.0 \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "STORAGE_TYPE=local,STORAGE_DIR=/tmp/uploads,OUTPUT_DIR=/tmp/output,AUTO_DETECT_STATION=true,APP_ENV=production,LOG_LEVEL=INFO"
```

### Option 2: Build local + Push

```bash
# Build local
docker build -f docker/Dockerfile.cloudrun -t roster-mapper:1.0.2 .

# Tag for GCR
docker tag roster-mapper:1.0.2 gcr.io/$(gcloud config get-value project)/roster-mapper:1.0.2

# Push to GCR
docker push gcr.io/$(gcloud config get-value project)/roster-mapper:1.0.2

# Deploy
gcloud run deploy roster-mapper \
    --image gcr.io/$(gcloud config get-value project)/roster-mapper:1.1.0 \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated
```

---

## 🔄 CI/CD Pipeline (Automatic)

### Workflow tự động

File `.github/workflows/cloudrun-deploy.yml` sẽ tự động:

1. **Test** - Chạy pytest
2. **Build** - Build Docker image
3. **Push** - Push lên Google Container Registry
4. **Deploy** - Deploy lên Cloud Run
5. **Health Check** - Kiểm tra service

### Trigger

- Push code lên branch `main`
- Manual trigger từ GitHub Actions tab

---

## ⚙️ Cấu hình Environment Variables

| Variable | Giá trị Cloud Run | Mô tả |
|----------|-------------------|-------|
| `STORAGE_TYPE` | `local` | Dùng local filesystem |
| `STORAGE_DIR` | `/tmp/uploads` | Thư mục upload (ephemeral) |
| `OUTPUT_DIR` | `/tmp/output` | Thư mục output (ephemeral) |
| `PORT` | `8080` | Cloud Run tự set |
| `APP_ENV` | `production` | Environment |
| `LOG_LEVEL` | `INFO` | Log level |
| `AUTO_DETECT_STATION` | `true` | Auto detect station từ filename |

---

## 🔍 Monitoring & Logging

### Xem logs

```bash
# Stream logs
gcloud run logs read roster-mapper --region asia-southeast1 --follow

# Filter logs
gcloud run logs read roster-mapper \
    --region asia-southeast1 \
    --format="table(timestamp,textPayload)"
```

### Cloud Logging Console

1. Mở [Cloud Logging](https://console.cloud.google.com/logs)
2. Filter: `resource.type="cloud_run_revision" AND resource.labels.service_name="roster-mapper"`

### Metrics

```bash
# Xem metrics
gcloud run services describe roster-mapper \
    --region asia-southeast1 \
    --format='yaml(status)'
```

---

## 🧪 Testing sau deploy

### 1. Health Check

```bash
SERVICE_URL=$(gcloud run services describe roster-mapper --region asia-southeast1 --format='value(status.url)')

curl "$SERVICE_URL/health"
# Expected: {"status":"ok","version":"1.1.0",...}
```

### 2. Test Upload API

```bash
# Upload file Excel
curl -X POST "$SERVICE_URL/api/v1/upload" \
    -F "file=@test_file.xlsx" \
    -F "station=HAN"
```

### 3. Test Web UI

Mở browser: `$SERVICE_URL/upload`

---

## 🐛 Troubleshooting

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `Container failed to start` | Dockerfile lỗi | Check build logs |
| `Permission denied /tmp` | User không có quyền | Verify non-root user setup |
| `LibreOffice not found` | Package chưa install | Check Dockerfile.cloudrun |
| `Health check failed` | App chưa start kịp | Tăng start-period |
| `Memory limit exceeded` | File quá lớn | Tăng memory limit |

### Debug container

```bash
# Chạy local để debug
docker run -it --rm \
    -p 8080:8080 \
    -e STORAGE_TYPE=local \
    -e STORAGE_DIR=/tmp/uploads \
    -e OUTPUT_DIR=/tmp/output \
    gcr.io/PROJECT/roster-mapper:1.1.0 \
    /bin/bash
```

### Xem container logs

```bash
gcloud run logs read roster-mapper \
    --region asia-southeast1 \
    --limit 100 \
    --format="table(timestamp,severity,textPayload)"
```

---

## 📊 Resource Recommendations

| Workload | Memory | CPU | Max Instances |
|----------|--------|-----|---------------|
| Light (< 5k cells) | 512Mi | 1 | 5 |
| Medium (5k-20k cells) | 1Gi | 1 | 10 |
| Heavy (> 20k cells) | 2Gi | 2 | 20 |

### Update resources

```bash
gcloud run services update roster-mapper \
    --region asia-southeast1 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 20
```

---

## 🔒 Security Recommendations

### 1. Restrict Access (Production)

```bash
# Remove public access
gcloud run services update roster-mapper \
    --region asia-southeast1 \
    --no-allow-unauthenticated

# Add IAM member
gcloud run services add-iam-policy-binding roster-mapper \
    --region asia-southeast1 \
    --member="user:admin@company.com" \
    --role="roles/run.invoker"
```

### 2. Custom Domain

```bash
gcloud run domain-mappings create \
    --service roster-mapper \
    --region asia-southeast1 \
    --domain mapper.company.com
```

### 3. Secret Manager (cho DB credentials)

```bash
# Tạo secret
echo -n "postgresql://..." | gcloud secrets create db-url --data-file=-

# Mount vào Cloud Run
gcloud run services update roster-mapper \
    --region asia-southeast1 \
    --set-secrets="DATABASE_URL=db-url:latest"
```

---

## 📝 Checklist Deploy

### Pre-deploy

- [ ] Tests pass (`pytest -q`)
- [ ] Dockerfile.cloudrun build OK
- [ ] GitHub secrets configured
- [ ] GCP APIs enabled

### Post-deploy

- [ ] Service URL accessible
- [ ] `/health` returns 200
- [ ] Upload .xlsx works
- [ ] Upload .xls (LibreOffice convert) works
- [ ] Mapping output correct
- [ ] Logs visible in Cloud Logging

---

## 🔗 Links

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [GitHub Repo](https://github.com/elsuselamos/roster-mapper)

---

**Version**: 1.1.0  
**Last Updated**: December 2025
