# 🚀 Deploy to Google Cloud Run

## Hướng dẫn triển khai Roster Mapper v1.1.0 lên Google Cloud Run

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

### 0. Kiểm tra Files trong Repo (QUAN TRỌNG) ⚠️

**Trước khi deploy, đảm bảo các file sau đã được commit và push:**

```bash
# Bước 1: Kiểm tra files có trong git không
git ls-files | grep -E "(requirements.txt|pyproject.toml|docker/Dockerfile.cloudrun)"

# Bước 2: Nếu thiếu, thêm vào git
git add requirements.txt
git add pyproject.toml
git add docker/Dockerfile.cloudrun
git add cloudbuild.yaml
git add app/
git add mappings/

# Bước 3: Commit và push
git commit -m "Add files for Cloud Run deployment v1.1.0"
git push origin main

# Bước 4: Verify lại trên GitHub
# Mở https://github.com/elsuselamos/roster-mapper/blob/main/requirements.txt
# Đảm bảo file hiển thị đúng
```

**Files bắt buộc phải có trong repo:**
- ✅ `requirements.txt` - **BẮT BUỘC** - Python dependencies
- ✅ `docker/Dockerfile.cloudrun` - Dockerfile cho Cloud Run
- ✅ `cloudbuild.yaml` - Cloud Build config (nếu dùng)
- ✅ `app/` - Application code
- ✅ `mappings/` - Mapping files (nếu cần)
- ✅ `pyproject.toml` - Project metadata

> ⚠️ **QUAN TRỌNG**: Nếu `requirements.txt` không có trong repo, Cloud Build sẽ **KHÔNG THỂ** build image!

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

### Option 0: Deploy từ Google Cloud Console (UI)

> ⚠️ **LƯU Ý**: Deploy từ Cloud Console có thể gặp vấn đề với build context.  
> **Khuyến nghị**: Dùng **Option 1 (Cloud Build với cloudbuild.yaml)** hoặc **Option 2 (CLI)** để đảm bảo build context đúng.

**Khi deploy từ Cloud Console, cần chỉ định đúng đường dẫn Dockerfile:**

1. **Truy cập Cloud Run Console:**
   - Mở [Cloud Run Console](https://console.cloud.google.com/run)
   - Click **"Create Service"**

2. **Cấu hình Source:**
   - Chọn **"Set up with Cloud Build"**
   - Chọn repository (GitHub, Cloud Source Repositories, etc.)
   - Chọn branch: `main` ⚠️ **Đảm bảo branch này có `requirements.txt`**
   - **Commit**: Chọn commit mới nhất (hoặc để trống để dùng HEAD)
   
   > 💡 **Tip**: Click vào commit để verify xem `requirements.txt` có trong commit đó không

3. **Build Configuration:**
   - **Build Type**: Chọn `Dockerfile`
   - **Source location**: ⚠️ **QUAN TRỌNG** - Thay đổi từ `/Dockerfile` thành:
     ```
     docker/Dockerfile.cloudrun
     ```
   - **Build context**: ⚠️ **QUAN TRỌNG** - Phải là root của repo:
     ```
     /
     ```
     hoặc để trống (mặc định là root)
   
   > ⚠️ **LƯU Ý QUAN TRỌNG**: 
   > - Build context phải là **root của repo** (`/`) để `requirements.txt` có thể được tìm thấy
   > - Nếu build context là `docker/`, thì `requirements.txt` sẽ không tìm thấy
   > - Đảm bảo các file sau đã được commit và push vào repo:
   >   - `requirements.txt` (bắt buộc - phải ở root)
   >   - `pyproject.toml` (nếu có)
   >   - `mappings/` directory (nếu cần)
   >   - Tất cả code trong `app/`

4. **Service Configuration:**
   - Service name: `roster-mapper`
   - Region: `asia-southeast1`
   - Authentication: `Allow unauthenticated invocations`

5. **Environment Variables:**
   - Click **"Variables & Secrets"** → **"Add Variable"**
   - Thêm các biến sau:
     ```
     STORAGE_TYPE=local
     STORAGE_DIR=/tmp/uploads
     OUTPUT_DIR=/tmp/output
     AUTO_DETECT_STATION=true
     APP_ENV=production
     LOG_LEVEL=INFO
     ```

6. **Resource Settings:**
   - Memory: `1 GiB`
   - CPU: `1`
   - Timeout: `300 seconds`
   - Min instances: `0`
   - Max instances: `10`

7. **Click "Create"** và đợi build + deploy hoàn tất.

> ⚠️ **Lưu ý**: Nếu không chỉ định đúng `docker/Dockerfile.cloudrun`, build sẽ fail với lỗi "Dockerfile not found".

**💡 Mẹo**: Nếu muốn đơn giản hóa, có thể tạo symlink hoặc copy:
```bash
# Trong repo, tạo symlink (Linux/Mac)
ln -s docker/Dockerfile.cloudrun Dockerfile

# Hoặc copy (Windows/Linux/Mac)
cp docker/Dockerfile.cloudrun Dockerfile
```
Sau đó trong Cloud Console, dùng `/Dockerfile` (mặc định).

---

### Option 1: Dùng Cloud Build với cloudbuild.yaml (Khuyến nghị ⭐)

**Cách này đảm bảo build context đúng và tránh lỗi `requirements.txt not found`:**

```bash
cd roster-mapper

# ⚠️ QUAN TRỌNG: Pull code mới nhất từ GitHub trước khi build
git pull origin main

# Verify cloudbuild.yaml đã được cập nhật
cat cloudbuild.yaml | grep "_SHORT_SHA"
# Phải thấy: _SHORT_SHA (có dấu _ ở đầu)

# Build với cloudbuild.yaml (đã config sẵn build context đúng)
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _SHORT_SHA=$(git rev-parse --short HEAD)

# Sau khi build xong, deploy
gcloud run deploy roster-mapper \
    --image gcr.io/$(gcloud config get-value project)/roster-mapper:$(git rev-parse --short HEAD) \
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

**Ưu điểm:**
- ✅ Build context tự động đúng (root của repo)
- ✅ Không cần chỉnh trong Console
- ✅ Có thể script hóa và tự động hóa

---

### Option 1b: Dùng Cloud Build trực tiếp (CLI - Alternative)

```bash
cd roster-mapper

# Build image với Cloud Build (sử dụng cloudbuild.yaml)
# cloudbuild.yaml tự động chỉ định docker/Dockerfile.cloudrun
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _SHORT_SHA=$(git rev-parse --short HEAD)

# Hoặc build trực tiếp với tag (không dùng cloudbuild.yaml)
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

### Option 2: Build local + Push (CLI - Local build)

```bash
# Build local
docker build -f docker/Dockerfile.cloudrun -t roster-mapper:1.1.0 .

# Tag for GCR
docker tag roster-mapper:1.1.0 gcr.io/$(gcloud config get-value project)/roster-mapper:1.1.0

# Push to GCR
docker push gcr.io/$(gcloud config get-value project)/roster-mapper:1.1.0

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

### ⚡ Quick Fix: Substitution key format error

**Nếu gặp lỗi `substitution key SHORT_SHA does not respect format ^_[A-Z0-9_]+$`:**

```bash
# Bước 1: Pull code mới nhất từ GitHub
cd roster-mapper
git pull origin main

# Bước 2: Verify cloudbuild.yaml đã được cập nhật
cat cloudbuild.yaml | grep "_SHORT_SHA"
# Phải thấy: _SHORT_SHA (có dấu _ ở đầu)
# Nếu thấy: SHORT_SHA (không có _) → file chưa được cập nhật

# Bước 3: Nếu file chưa cập nhật, commit và push
git add cloudbuild.yaml
git commit -m "Fix cloudbuild.yaml: use _SHORT_SHA format"
git push origin main

# Bước 4: Pull lại và build
git pull origin main
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _SHORT_SHA=$(git rev-parse --short HEAD)
```

> ⚠️ **Lưu ý**: Cloud Build yêu cầu substitution keys phải bắt đầu bằng `_` và chỉ chứa chữ hoa, số, gạch dưới.

### ⚡ Quick Fix: requirements.txt not found

**Nếu gặp lỗi `COPY failed: file not found: stat requirements.txt`:**

**Nguyên nhân thường gặp:**
1. File chưa được commit/push vào GitHub
2. **Build context không đúng** (Cloud Console set sai)
3. Chọn sai commit/branch

**Giải pháp:**

```bash
# Bước 1: Kiểm tra file có trong git không
cd roster-mapper
git ls-files requirements.txt

# Bước 2: Nếu không có output, file chưa được track
# Thêm vào git:
git add requirements.txt
git commit -m "Add requirements.txt for Cloud Run deployment"
git push origin main

# Bước 3: Verify trên GitHub
# Mở: https://github.com/elsuselamos/roster-mapper/blob/main/requirements.txt
# File phải hiển thị được

# Bước 4: Deploy lại từ Cloud Console
# - Chọn commit mới nhất (có requirements.txt)
# - Source location: docker/Dockerfile.cloudrun
# - ⚠️ Build context: Phải là "/" (root) hoặc để trống
```

**Nếu vẫn lỗi sau khi verify file có trên GitHub:**

1. **Kiểm tra Build Context trong Cloud Console:**
   - Trong phần "Build Configuration"
   - Tìm field "Build context" hoặc "Working directory"
   - Phải là `/` hoặc để trống (không phải `docker/`)

2. **Hoặc dùng Cloud Build config file (Khuyến nghị):**
   ```bash
   # Thay vì deploy từ Console, dùng CLI với cloudbuild.yaml
   gcloud builds submit --config cloudbuild.yaml
   ```

3. **Verify build context:**
   - Trong Cloud Build logs, check xem working directory là gì
   - Nếu là `/workspace/docker/` thì sai → phải là `/workspace/`

### Lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `substitution key SHORT_SHA does not respect format ^_[A-Z0-9_]+$` | Substitution key sai format hoặc file chưa cập nhật | **1. Pull code mới nhất:** `git pull origin main`<br>**2. Verify:** `cat cloudbuild.yaml \| grep "_SHORT_SHA"` (phải có `_` ở đầu)<br>**3. Dùng:** `--substitutions _SHORT_SHA=$(git rev-parse --short HEAD)` |
| `unable to evaluate symlinks in Dockerfile path: lstat /workspace/Dockerfile: no such file or directory` | Cloud Build tìm Dockerfile ở root | **Dùng `cloudbuild.yaml`** hoặc chỉ định `-f docker/Dockerfile.cloudrun` |
| `COPY failed: file not found: stat requirements.txt: file does not exist` | `requirements.txt` không có trong build context | **1. Kiểm tra file có trong repo:** `git ls-files requirements.txt`<br>**2. Nếu không có:** `git add requirements.txt && git commit -m "Add requirements.txt" && git push`<br>**3. Verify trên GitHub:** Mở file trên web để confirm<br>**4. Chọn lại commit mới nhất trong Cloud Console** |
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
- [ ] **`requirements.txt` đã được commit và push vào repo** ⚠️
- [ ] **Tất cả code đã được commit và push** ⚠️
- [ ] Dockerfile.cloudrun build OK (test local: `docker build -f docker/Dockerfile.cloudrun -t test .`)
- [ ] GitHub secrets configured (nếu dùng CI/CD)
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
