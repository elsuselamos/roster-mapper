# CONTRACT – Roster Mapper Phase 1
**Thỏa thuận phạm vi & tiêu chuẩn**

---

## 1. Scope – Những gì sẽ làm trong Phase 1

### Tính năng / Module:

| Module | Tính năng | Priority |
|--------|-----------|----------|
| Upload API | Upload file Excel (.xlsx, .xls) | P0 |
| Upload API | Get sheet names | P0 |
| Upload API | Preview sheet (headers + sample rows) | P0 |
| Upload API | Process file with mapping | P0 |
| Upload API | Download processed file | P0 |
| Mapper | Longest-key-first matching | P0 |
| Mapper | Multi-code cell handling (B1/B19) | P0 |
| Mapper | Station-specific mappings | P0 |
| Mapper | Auto-detect station from filename | P1 |
| Admin API | Import mappings (JSON) | P0 |
| Admin API | Import mappings (CSV) | P1 |
| Admin API | Get/List mappings | P0 |
| Admin API | Delete mappings | P1 |
| Storage | File upload/download | P0 |
| Storage | Mapping versioning | P0 |
| Storage | Audit logging | P1 |

### Tài liệu cần tạo:
- [x] README.md với hướng dẫn cài đặt
- [x] .env.example
- [x] API documentation (FastAPI auto-docs)
- [x] INTAKE.md, BLUEPRINT.md, CONTRACT.md

---

## 2. Out-of-scope – KHÔNG làm trong Phase 1

### Tính năng để Phase 2+:
- ❌ Web UI (chỉ có API trong Phase 1)
- ❌ User authentication / authorization
- ❌ Dashboard thống kê
- ❌ Scheduled batch processing
- ❌ Email notifications
- ❌ Multi-language support
- ❌ Mobile app

### Tích hợp để sau:
- ❌ AMOS integration
- ❌ SSO / LDAP
- ❌ Cloud storage (GCS/S3)

### Quy tắc khi có yêu cầu mới:
1. Ghi vào backlog trong `docs/BACKLOG.md`
2. KHÔNG tự ý thêm vào Phase 1
3. Đánh giá lại khi bắt đầu Phase 2

---

## 3. Definition of Done (DoD)

Phase 1 được coi là **"XONG"** khi:

### Functional:
- [ ] Upload file Excel → nhận file_id và danh sách sheets
- [ ] Preview sheet → nhận headers và sample data
- [ ] Process file → nhận file đã mapped
- [ ] Download → file Excel hoàn chỉnh
- [ ] Import mapping CSV/JSON → tạo version mới
- [ ] Get mappings → trả về dict mapping

### Quality:
- [ ] Tất cả unit tests PASS (pytest)
- [ ] B1/B19 test case PASS (longest-key-first)
- [ ] Multi-code test cases PASS (B1/B19, B1,B2)
- [ ] Docker build thành công
- [ ] Docker-compose up không lỗi

### Documentation:
- [ ] README có đủ hướng dẫn run local và Docker
- [ ] API docs accessible tại /docs
- [ ] Sample mapping files trong mappings/

---

## 4. Yêu cầu chất lượng

### Về API:
- Response time < 2s cho file < 5MB
- Proper error handling với status codes
- JSON responses với format nhất quán

### Về Code:
- Python 3.11 compatible
- Type annotations cho public functions
- Docstrings cho classes và core functions
- Follow PEP 8 (enforced by ruff/black)

### Về Security:
- Không hardcode secrets (dùng .env)
- File upload validation (extension, size)
- SQL injection prevention (SQLAlchemy ORM)

### Về Testing:
- Unit tests cho Mapper service
- Minimum 80% coverage cho core logic
- pytest as test runner

---

## 5. GATES & Tiêu chí

### Gate 1 – Project Setup ✅
**Tiêu chí qua:**
- Cấu trúc thư mục đúng chuẩn
- requirements.txt đầy đủ
- Docker build không lỗi
- FastAPI app start được

### Gate 2 – Upload Flow
**Tiêu chí qua:**
- POST /api/v1/upload → 200 + file_id
- GET /api/v1/preview/{file_id} → headers + rows
- File lưu đúng vị trí

### Gate 3 – Mapper Engine
**Tiêu chí qua:**
- test_mapper.py ALL PASS
- B1 → "Nghỉ phép"
- B19 → "Đào tạo chuyên sâu" (không bị map thành B1)
- B1/B19 → "Nghỉ phép/Đào tạo chuyên sâu"

### Gate 4 – Admin Import
**Tiêu chí qua:**
- POST /api/v1/admin/mappings/import → 200
- POST /api/v1/admin/mappings/import-csv → 200
- Mapping được lưu với version

### Gate 5 – Integration
**Tiêu chí qua:**
- End-to-end: Upload → Process → Download
- File output đúng format
- Audit log ghi nhận actions

---

## 6. Quy tắc thay đổi

### Nếu cần đổi scope:
1. Cập nhật CONTRACT.md
2. Thêm `[v2]` vào tiêu đề section thay đổi
3. Ghi lý do và ngày thay đổi

### Nếu cần đổi kiến trúc:
1. Cập nhật BLUEPRINT.md
2. Tạo ADR (Architecture Decision Record) trong docs/adr/
3. Thông báo stakeholders

### Version history:
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-05 | Initial contract |

---

## 7. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Owner | datnguyentien@vietjetair.com | 2024-12-05 | ✅ |
| Developer | Claude Code | 2024-12-05 | ✅ |

