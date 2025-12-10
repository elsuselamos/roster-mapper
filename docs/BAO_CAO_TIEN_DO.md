# 📊 BÁO CÁO TIẾN ĐỘ DỰ ÁN – PHIÊN BẢN ÔNG THẦU

## VIETJET AMO – ROSTER MAPPER

---

| Thông tin | Chi tiết |
|-----------|----------|
| **Dự án** | Roster Mapper - Công cụ chuyển đổi mã roster |
| **Bộ phận** | Quản lý Bảo dưỡng (Maintenance Ops) |
| **Phiên bản** | v1.1.0 |
| **Ngày báo cáo** | 05/12/2025 (cập nhật 08/12/2025) |
| **Trạng thái** | ✅ **PHASE 2 - HOÀN THÀNH** |
| **Website** | vietjetair.com |

---

## I. TÓM TẮT DỰ ÁN

Dự án **Roster Mapper** nhằm tự động chuyển đổi mã roster từ các station (SGN, HAN, DAD, CXR, HPH, VCA, VII) sang mã chuẩn HR.

Đến thời điểm báo cáo, hệ thống đã **hoàn thành Phase 2**, vận hành ổn định, chạy qua Docker, môi trường local, và **Google Cloud Run**. Sẵn sàng đưa vào thử nghiệm nội bộ và production deployment.

---

## II. TRẠNG THÁI TỔNG THỂ

| Hạng mục | Trạng thái |
|----------|------------|
| Phase 1 – Core Engine | ✅ 100% |
| Phase 2 – Web UI, Batch, Multi-station | ✅ 100% |
| Phase 3 – Authentication (tạm dừng) | ⏸ Chưa yêu cầu |
| **Tiến độ tổng thể** | **100%** |

---

## III. TÍNH NĂNG ĐÃ HOÀN THÀNH (PHASE 2)

### 1. Web UI – Jinja2 + Tailwind + HTMX

| Tính năng | Trạng thái | Mô tả |
|-----------|------------|-------|
| Upload nhiều file | ✅ Done | Drag & drop, chọn nhiều file cùng lúc |
| Chọn station | ✅ Done | Dropdown hoặc auto-detect từ tên file |
| Chọn sheets | ✅ Done | Chọn tất cả hoặc sheets cụ thể |
| Preview | ✅ Done | 15-20 dòng đầu, highlight xanh/đỏ |
| Trang Admin | ✅ Done | Nhập mapping (KHÔNG yêu cầu đăng nhập) |
| Trang Dashboard | ✅ Done | Thống kê cơ bản |
| **2 tùy chọn Download** | ✅ **MỚI** | Giữ format gốc HOẶC text thuần |
| **Loading Spinner** | ✅ **MỚI** | Hiển thị trạng thái đang xử lý (upload, preview, mapping) |

### 2. Mapping Engine – Production Ready

| Tính năng | Trạng thái | Mô tả |
|-----------|------------|-------|
| Longest-key-first | ✅ Done | Đảm bảo B19 ≠ B1 |
| Regex boundary | ✅ Done | Tránh match nhầm |
| Multi-code | ✅ Done | A/B, A B, A,B, xuống dòng |
| Multi-sheet | ✅ Done | Xử lý nhiều sheets |
| Case-insensitive | ✅ Done | Không phân biệt hoa/thường |
| **Style Preservation** | ✅ **MỚI** | Giữ nguyên màu, font, border của file gốc |
| **Empty Mapping** | ✅ **MỚI** | Hỗ trợ map code sang rỗng `{"OT": ""}` |
| **Unmapped → Empty** | ✅ **MỚI** | Code không có mapping sẽ thành rỗng |

### 2.1. Bảng Mapping Behavior (MỚI)

| Cell gốc | Mapping định nghĩa | Kết quả | Ghi chú |
|----------|-------------------|---------|---------|
| `B1` | `{"B1": "NP"}` | `NP` | ✅ Exact match |
| `B19` | `{"B1": "NP", "B19": "TR"}` | `TR` | ✅ Longest-key-first |
| `b1` | `{"B1": "NP"}` | `NP` | ✅ Case-insensitive |
| `OT` | `{"OT": ""}` | *(rỗng)* | ✅ Map sang empty |
| `XYZ` | *(không có)* | *(rỗng)* | ⚠️ Unmapped → empty |
| `B1/B2` | `{"B1": "NP", "B2": "SB"}` | `NP/SB` | ✅ Multi-code |
| `B1/XYZ` | `{"B1": "NP"}` | `NP/` | ⚠️ XYZ unmapped |
| `ABC/DEF` | *(không có)* | `/` | ⚠️ Cả 2 unmapped |

> ⚠️ **LƯU Ý QUAN TRỌNG**: Cần định nghĩa đầy đủ **TẤT CẢ** code trong mapping. Code không có sẽ bị xóa (thành rỗng)!

### 3. Tùy chọn Download (MỚI)

| Option | Mô tả |
|--------|-------|
| 🎨 **Giữ Format** | Giữ nguyên toàn bộ định dạng gốc: màu sắc, font, border, merge cells, chiều rộng cột. Chỉ thay đổi nội dung text. |
| 📄 **Text Only** | Chỉ giữ nội dung text thuần, không có định dạng. Phù hợp để import vào hệ thống khác hoặc xử lý tiếp. |

### 4. Multi-station

| Station | Mapping | Trạng thái |
|---------|---------|------------|
| HAN | 74 codes | ✅ Production Ready |
| SGN | 5 codes (sample) | ⚠️ Cần bổ sung dữ liệu thực tế |
| DAD | 5 codes (sample) | ⚠️ Cần bổ sung dữ liệu thực tế |
| CXR | 5 codes (sample) | ⚠️ Cần bổ sung dữ liệu thực tế |
| HPH | 5 codes (sample) | ⚠️ Cần bổ sung dữ liệu thực tế |
| VCA | 5 codes (sample) | ⚠️ Cần bổ sung dữ liệu thực tế |
| VII | 5 codes (sample) | ⚠️ Cần bổ sung dữ liệu thực tế |

### 5. Hạ tầng & Công cụ

| Hạng mục | Trạng thái | Chi tiết |
|----------|------------|----------|
| Source Code | ✅ Done | GitHub: elsuselamos/roster-mapper |
| Docker | ✅ Done | Multi-stage Dockerfile |
| Docker Hub CI/CD | ✅ Done | GitHub Actions |
| **Cloud Run Deployment** | ✅ **MỚI** | Google Cloud Run với ephemeral storage |
| **CI/CD Pipeline** | ✅ **MỚI** | Auto build & deploy qua GitHub Actions |
| Tests | ✅ Done | 79 tests PASS |
| Documentation | ✅ Done | CONTEXT.md, DEPLOY_CLOUDRUN.md, API specs |

---

## IV. KẾT QUẢ KIỂM THỬ

### ✔ Unit Tests

```
============================= test session starts ==============================
collected 79 items

tests/test_batch_processing.py ...........     [ 13%]
tests/test_dashboard_queries.py ........       [ 24%]
tests/test_mapper.py ........................  [ 54%]
tests/test_multi_station.py ...........................  [ 88%]
tests/test_ui_routes.py .........              [100%]

============================== 79 passed ==============================
```

**Tổng số bài test: 79 → 79/79 passed ✅**

### ✔ Performance Test (HAN)

| Metric | Kết quả |
|--------|---------|
| File test | HAN ENG ROSTER DEC 2025.xlsx |
| Số rows | 260+ |
| Số columns | 64 |
| Tổng cells | ~16,000+ |
| Thời gian xử lý | < 10 giây |
| **Kết quả** | ✅ **PASS** |

→ **Đạt yêu cầu vận hành thực tế**

---

## V. LINKS QUAN TRỌNG

| Mục | Link |
|-----|------|
| GitHub Repo | https://github.com/elsuselamos/roster-mapper |
| Release v1.0.0 | https://github.com/elsuselamos/roster-mapper/releases/tag/v1.0.0 |
| Local Demo | http://localhost:8000 |

---

## VI. HƯỚNG DẪN CHẠY HỆ THỐNG

### 1. Chạy Local

```bash
git clone https://github.com/elsuselamos/roster-mapper.git
cd roster-mapper

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest -q

uvicorn app.main:app --reload --port 8000
```

### 2. Chạy bằng Docker

```bash
docker build -f docker/Dockerfile -t roster-mapper:local .
docker run -p 8000:8000 roster-mapper:local
```

### 3. URLs

| Chức năng | URL |
|-----------|-----|
| Upload | http://localhost:8000/upload |
| Admin Mapping | http://localhost:8000/admin |
| Dashboard | http://localhost:8000/dashboard |
| API Docs | http://localhost:8000/docs |

---

## VII. LƯU Ý QUAN TRỌNG (THEO YÊU CẦU BAN ĐẦU)

### ❌ ĐÃ TẮT / KHÔNG TRIỂN KHAI:

- Authentication / Login / User Role
- Admin-only mode
- Cloud Run / GCP / Service Account

### ✔ VẪN GIỮ:

- Mapping versioning
- Audit log (created_by = "anonymous")
- **Style preservation** (giữ nguyên định dạng file gốc)

---

## VIII. ĐỀ XUẤT TIẾP THEO (NEXT STEPS)

| STT | Công việc | Ưu tiên | Ghi chú |
|-----|-----------|---------|---------|
| 1 | Thu thập file mapping thực tế từ SGN/DAD/CXR… | ⭐ Cao | Cần dữ liệu từ station |
| 2 | Test với file roster thật của từng station | ⭐ Cao | Quan trọng |
| 3 | Tạo Docker Hub CI/CD pipeline cho server nội bộ | Trung bình | Sẵn workflow |
| 4 | Chuẩn bị server nội bộ (Docker Compose) | Trung bình | Chạy offline |
| 5 | Training station admins | Thấp | Sau khi deploy |

---

## IX. TIẾN ĐỘ TỔNG THỂ

```
Phase 1: Project Setup & Core Engine     [██████████] 100%
Phase 2: Web UI & Multi-sheet            [██████████] 100%
Phase 3: Authentication (chưa yêu cầu)   [░░░░░░░░░░] 0%
```

**Tổng tiến độ Phase 1-2: 100%**

---

## X. KẾT LUẬN ÔNG THẦU

> **"Hệ thống Roster Mapper đã hoàn thành Phase 2, sẵn sàng đưa vào pilot thực tế và production deployment.**
> 
> **Các điểm nổi bật:**
> - ✅ Engine ổn định, xử lý 16,000+ cells < 10 giây
> - ✅ UI hoàn chỉnh, dễ sử dụng
> - ✅ **Loading spinner** khi upload/preview/mapping - UX chuyên nghiệp
> - ✅ **Giữ nguyên định dạng file gốc** (màu, font, border)
> - ✅ **2 tùy chọn download**: Styled vs Plain text
> - ✅ **Empty mapping**: Hỗ trợ xóa code không cần thiết
> - ✅ **Unmapped → Empty**: Code không có mapping sẽ thành rỗng
> - ✅ **Cloud Run Deployment** (v1.1.0): Hỗ trợ deploy lên Google Cloud Run với ephemeral storage
> - ✅ **CI/CD Pipeline**: Tự động build & deploy qua GitHub Actions
> - ✅ **LibreOffice Integration**: Hỗ trợ convert .xls → .xlsx
> - ✅ Batch hoạt động tốt
> - ✅ Mapping versioning đầy đủ
> - ✅ Không yêu cầu đăng nhập
> 
> **Tiếp theo cần dữ liệu thực từ các station để hoàn thiện production rollout."**

---

## PHỤ LỤC: SCREENSHOTS

### 1. Trang Upload
- Drag & drop files
- Chọn station hoặc auto-detect
- Hiển thị trạng thái mapping từng station
- **Loading spinner** khi upload files

### 2. Trang Chọn Sheets
- Chọn "Tất cả sheets" hoặc sheets cụ thể
- Hiển thị danh sách sheets trong file
- **Loading spinner** khi tạo preview

### 3. Trang Preview
- Tab view cho mỗi sheet
- Highlight ô đã map (xanh) / chưa map (đỏ)
- Thống kê số cells mapped/unmapped
- **Loading spinner** khi bắt đầu mapping

### 4. Trang Results
- **2 nút download**: 🎨 Giữ Format | 📄 Text Only
- Thống kê chi tiết per sheet

### 5. Loading Indicator (MỚI)
- ⏳ Vòng xoay (spinner) màu đỏ Vietjet
- Text mô tả hành động đang thực hiện
- Tự động hiện khi upload/preview/mapping
- Giúp user biết app đang xử lý

### 6. Cloud Run Deployment (v1.1.0 - MỚI)
- 🚀 **Google Cloud Run Support**: Deploy lên Cloud Run với ephemeral storage
- 📦 **LocalStorage Adapter**: Quản lý file tạm trong `/tmp` (ephemeral)
- 🔄 **LibreOffice Integration**: Tự động convert .xls → .xlsx
- ⚙️ **CI/CD Pipeline**: GitHub Actions tự động build & deploy
- 📊 **Enhanced Health Check**: Kiểm tra storage, Cloud Run detection
- 📖 **Deployment Guide**: Tài liệu chi tiết trong `docs/DEPLOY_CLOUDRUN.md`

---

## XI. CHANGELOG - VERSION 1.1.0

### Cloud Run Deployment Features

| Feature | Mô tả |
|---------|-------|
| **Ephemeral Storage** | Sử dụng `/tmp` cho file upload/output (Cloud Run) |
| **LibreOffice** | Convert .xls → .xlsx tự động |
| **Dockerfile.cloudrun** | Optimized Dockerfile cho Cloud Run (port 8080) |
| **CI/CD Pipeline** | GitHub Actions tự động deploy |
| **Health Endpoint** | Enhanced với storage check |
| **Documentation** | `DEPLOY_CLOUDRUN.md` với hướng dẫn đầy đủ |

---

**© 2025 Vietjet AMO - IT Department**

*Báo cáo được tạo ngày 05/12/2025 | Cập nhật: 12/12/2025 (v1.1.0)*
