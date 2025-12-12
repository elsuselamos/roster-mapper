# Test Checklist - Fix Download File trên Cloud Run

**Ngày tạo:** 2025-12-10  
**Mục đích:** Verify các fix cho lỗi "Không trả về file download cho user"

---

## ✅ Pre-deployment Tests (Local)

### 1. Test File Paths và Directories

```bash
# Start server locally
cd roster-mapper
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Checklist:**
- [ ] `OUTPUT_DIR/results` directory được tạo tự động khi start server
- [ ] Upload file → check `STORAGE_DIR/uploads/{file_id}.xlsx` tồn tại
- [ ] Process file → check files được lưu vào `OUTPUT_DIR/`:
  - [ ] `{file_id}_mapped.xlsx` (styled format)
  - [ ] `{file_id}_mapped_plain.xlsx` (plain format)
  - [ ] `results/{session_id}.json` (results file)

### 2. Test Processing Flow

**Test Case 1: Single File, Single Sheet**
- [ ] Upload file Excel
- [ ] Select sheets
- [ ] Preview mapping
- [ ] Click "Start Mapping"
- [ ] Verify:
  - [ ] Loading screen hiển thị
  - [ ] AJAX request với `Accept: application/json`
  - [ ] Response có `session_id`
  - [ ] Polling status hoạt động
  - [ ] Redirect đến `/results?session_id=...`
  - [ ] Results page hiển thị đúng
  - [ ] Download buttons hiển thị (styled và plain)

**Test Case 2: Single File, Multiple Sheets**
- [ ] Upload file Excel có nhiều sheets
- [ ] Select multiple sheets
- [ ] Process và verify:
  - [ ] Tất cả sheets được process
  - [ ] Stats hiển thị đúng cho từng sheet
  - [ ] Download files chứa tất cả sheets

**Test Case 3: Multiple Files**
- [ ] Upload nhiều files
- [ ] Process tất cả
- [ ] Verify:
  - [ ] Mỗi file có download buttons riêng
  - [ ] Stats đúng cho từng file

### 3. Test Download Endpoints

**Test Styled Format:**
```bash
# Get file_id từ results page
curl "http://localhost:8000/api/v1/download/{file_id}?format=styled" \
  -o test_styled.xlsx

# Verify:
# - File được download thành công
# - File có formatting (colors, fonts, etc.)
# - File có đúng sheets
```

**Test Plain Format:**
```bash
curl "http://localhost:8000/api/v1/download/{file_id}?format=plain" \
  -o test_plain.xlsx

# Verify:
# - File được download thành công
# - File không có formatting (text only)
# - File có đúng sheets
```

**Checklist:**
- [ ] Styled format download thành công
- [ ] Plain format download thành công
- [ ] Files có đúng nội dung
- [ ] Files có đúng số sheets
- [ ] Logs hiển thị: `Serving file: ..., size: ... bytes`

### 4. Test Status Check API

```bash
# 1. Process file và lấy session_id
curl -X POST "http://localhost:8000/process" \
  -H "Accept: application/json" \
  -F "..."

# Response: {"success": true, "session_id": "session_1234567890", ...}

# 2. Check status
curl "http://localhost:8000/api/v1/results/status?session_id=session_1234567890"

# Expected response:
# {
#   "status": "completed",
#   "session_id": "session_1234567890",
#   "message": "Processing completed. 1 file(s) processed.",
#   "results": {"files": [...]}
# }
```

**Checklist:**
- [ ] Status check trả về `"status": "completed"` sau khi process xong
- [ ] Results chứa đúng thông tin files
- [ ] Download URLs đúng format

### 5. Test Error Handling

**Test Case: File Not Found**
```bash
curl "http://localhost:8000/api/v1/download/invalid-file-id?format=styled"
# Expected: 404 với message rõ ràng
```

**Test Case: Invalid Session ID**
```bash
curl "http://localhost:8000/api/v1/results/status?session_id=invalid"
# Expected: {"status": "not_found", ...}
```

**Checklist:**
- [ ] 404 errors có message rõ ràng
- [ ] Logs hiển thị warning khi file không tìm thấy
- [ ] Frontend xử lý errors gracefully

---

## ✅ Cloud Run Deployment Tests

### 1. Pre-deployment Checklist

- [ ] Code đã được commit và push
- [ ] Dockerfile.cloudrun đã được update (nếu cần)
- [ ] Environment variables đã được set:
  - [ ] `STORAGE_DIR=/tmp/uploads`
  - [ ] `OUTPUT_DIR=/tmp/output`
  - [ ] `TEMP_DIR=/tmp/temp`

### 2. Deploy

```bash
# Build image
gcloud builds submit --tag gcr.io/PROJECT_ID/roster-mapper:latest \
  -f docker/Dockerfile.cloudrun .

# Deploy
gcloud run deploy roster-mapper \
  --image gcr.io/PROJECT_ID/roster-mapper:latest \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars STORAGE_DIR=/tmp/uploads,OUTPUT_DIR=/tmp/output,TEMP_DIR=/tmp/temp
```

### 3. Post-deployment Tests

**Test 1: Health Check**
```bash
curl https://YOUR-SERVICE-URL/health
# Expected: 200 OK
```

**Test 2: Full Flow Test**
- [ ] Upload file qua web UI
- [ ] Select sheets
- [ ] Preview mapping
- [ ] Start processing
- [ ] Verify:
  - [ ] Loading screen hiển thị
  - [ ] Polling status hoạt động
  - [ ] Redirect đến results page
  - [ ] Results hiển thị đúng
  - [ ] Download buttons hoạt động

**Test 3: Download Files**
- [ ] Click "Download Styled Format"
  - [ ] File download thành công
  - [ ] File có đúng nội dung
  - [ ] File có formatting
- [ ] Click "Download Plain Format"
  - [ ] File download thành công
  - [ ] File có đúng nội dung
  - [ ] File không có formatting

**Test 4: Check Logs**

```bash
# View logs
gcloud run services logs read roster-mapper --region asia-southeast1 --limit 100
```

**Verify logs có:**
- [ ] `POST /process called` với accept header
- [ ] `Processing styled format for file_id: ...`
- [ ] `Styled file saved: /tmp/output/..., exists: True`
- [ ] `Plain format file saved: /tmp/output/..., exists: True`
- [ ] `Results saved successfully: /tmp/output/results/session_...json`
- [ ] `Download request: file_id=..., format=...`
- [ ] `Serving file: ..., size: ... bytes`

**Test 5: Multi-instance Test**

Cloud Run có thể tạo nhiều instances. Test để đảm bảo:
- [ ] Results file có thể được đọc từ instance khác (qua session_id)
- [ ] Download files có thể được serve từ instance khác
- [ ] Status check hoạt động cross-instance

**Cách test:**
1. Process file → lấy session_id
2. Wait vài phút (để instance có thể thay đổi)
3. Check status và download → verify vẫn hoạt động

---

## 🐛 Debug Checklist (Nếu có lỗi)

### Lỗi: Files không được lưu

**Check:**
- [ ] `OUTPUT_DIR` có được tạo không?
  ```bash
  # Trong Cloud Run logs, tìm:
  # "Results saved successfully: /tmp/output/results/..."
  ```
- [ ] Permissions đúng không?
  ```bash
  # Cloud Run default user có quyền write vào /tmp
  ```
- [ ] Disk space đủ không?
  ```bash
  # Cloud Run có giới hạn 32GB ephemeral storage
  ```

### Lỗi: Download 404

**Check:**
- [ ] File path đúng không?
  ```bash
  # Logs phải có: "Download file path: /tmp/output/{file_id}_mapped.xlsx"
  ```
- [ ] File có tồn tại không?
  ```bash
  # Logs phải có: "exists: True"
  ```
- [ ] Format parameter đúng không?
  ```bash
  # Styled: {file_id}_mapped.xlsx
  # Plain: {file_id}_mapped_plain.xlsx
  ```

### Lỗi: Results không hiển thị

**Check:**
- [ ] Session ID có được pass qua URL không?
  ```bash
  # URL phải có: /results?session_id=session_1234567890
  ```
- [ ] Results file có tồn tại không?
  ```bash
  # Check logs: "Looking for results with session_id: ..."
  ```
- [ ] Fallback path có hoạt động không?
  ```bash
  # Nếu OUTPUT_DIR không tìm thấy, check TEMP_DIR
  ```

### Lỗi: Status Check trả về "not_found"

**Check:**
- [ ] Session ID đúng không?
- [ ] Results file có được lưu không?
- [ ] Timing: Có thể processing chưa xong?

---

## 📊 Success Criteria

Tất cả tests pass nếu:

1. ✅ Upload → Process → Download flow hoạt động end-to-end
2. ✅ Cả styled và plain format download được
3. ✅ Results page hiển thị đúng với session_id
4. ✅ Status check API hoạt động
5. ✅ Logs hiển thị đầy đủ thông tin
6. ✅ Multi-instance support hoạt động (results accessible cross-instance)

---

## 📝 Test Results Template

```
Date: YYYY-MM-DD
Tester: [Name]
Environment: [Local/Cloud Run]
Version: [Git commit hash]

Results:
- [ ] Pre-deployment tests: PASS/FAIL
- [ ] Cloud Run deployment: PASS/FAIL
- [ ] Full flow test: PASS/FAIL
- [ ] Download test: PASS/FAIL
- [ ] Logs verification: PASS/FAIL
- [ ] Multi-instance test: PASS/FAIL

Issues Found:
1. [Issue description]
   - Severity: [Critical/High/Medium/Low]
   - Status: [Open/Fixed]

Notes:
[Any additional notes]
```

---

**Last Updated:** 2025-12-10  
**Status:** Ready for testing


