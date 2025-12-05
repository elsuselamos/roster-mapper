# INTAKE – Roster Mapper
**Vietjet – Bộ phận Quản lý Bảo dưỡng (AMO)**

---

## 1. Mục tiêu

- **Kết quả cuối cùng:** Ứng dụng web cho phép nhân viên AMO upload file Excel roster và tự động chuyển đổi các mã hoạt động (B1, B19, OFF...) thành mô tả tiếng Việt dễ hiểu.
- **6-12 tháng nữa:** 
  - Tất cả 7 trạm (SGN, HAN, DAD, CXR, HPH, VCA, VII) sử dụng hệ thống
  - Giảm 80% thời gian tra cứu mã roster thủ công
  - Chuẩn hóa mapping code toàn hệ thống AMO

---

## 2. Đối tượng

### Người dùng chính:
- **Nhân viên lập kế hoạch bảo dưỡng** – Upload roster hàng ngày/tuần
- **Quản lý trạm** – Xem báo cáo, quản lý mapping codes

### Vấn đề hiện tại:
- File Excel roster chứa các mã code khó hiểu (B1, B19, TR, AL...)
- Mỗi trạm có bộ mã riêng, không đồng nhất
- Phải tra cứu thủ công, tốn thời gian và dễ sai sót
- Không có lịch sử phiên bản mapping

---

## 3. Bối cảnh & Ràng buộc

### Thời gian:
- **Phase 1 (MVP):** 2 tuần
- **Phase 2 (Full features):** 1 tháng

### Công nghệ bắt buộc:
- Python 3.11 (chuẩn nội bộ AMO IT)
- PostgreSQL (đã có infrastructure)
- Docker deployment

### Ràng buộc:
- Chạy được offline trong mạng nội bộ
- Không yêu cầu internet cho xử lý file
- Tương thích Excel .xlsx và .xls

---

## 4. Phạm vi dự kiến (Draft Scope)

### Phase 1 – PHẢI CÓ:
- [x] Upload file Excel
- [x] Chọn sheet, preview dữ liệu
- [x] Áp dụng mapping theo station
- [x] Download file đã map
- [x] Admin import/export mappings

### Phase 2 – ƯU TIÊN THẤP:
- [ ] Dashboard thống kê
- [ ] Lịch sử upload/processing
- [ ] Multi-user authentication
- [ ] API cho tích hợp bên thứ 3
- [ ] Scheduled batch processing

---

## 5. Tài nguyên hiện có

### Dữ liệu:
- File Excel roster mẫu từ các trạm
- Bảng mapping codes hiện tại (Excel)

### Đội ngũ:
- **datnguyentien@vietjetair.com** – Project owner, AMO IT
- Infrastructure: Docker host nội bộ

### Công cụ:
- VS Code / Cursor
- Docker Desktop
- PostgreSQL server

---

## 6. Ưu tiên & Tiêu chí thành công

### Ưu tiên Phase 1:
1. **Accuracy** – Mapping chính xác 100% (B19 không bị nhầm thành B1)
2. **Speed** – Xử lý file < 10 giây
3. **Simplicity** – Upload → Process → Download trong 3 clicks

### Dự án thành công nếu:
- Nhân viên AMO có thể tự upload và xử lý file không cần hỗ trợ IT
- Mapping codes được version control, dễ cập nhật
- Tích hợp được vào quy trình làm việc hàng ngày

---

## 7. Ghi chú thêm

### Cảm hứng:
- Google Translate cho spreadsheet
- Notion import/export

### Rủi ro đã thấy:
- Multi-code cells (B1/B19) cần xử lý đặc biệt
- Mỗi trạm có thể có codes trùng tên nhưng nghĩa khác
- File Excel từ các version khác nhau (2010, 2016, 365)

### Benchmark:
- Hiện tại: 15-30 phút tra cứu thủ công/file
- Mục tiêu: < 1 phút/file (bao gồm upload + download)

