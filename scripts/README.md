# Scripts

Thư mục chứa các utility scripts để test và debug.

## test_download.py

Script để test download functionality và status check API.

### Cách sử dụng:

**1. Test với session_id (sau khi đã process file):**

```bash
# Start server trước
uvicorn app.main:app --reload

# Trong terminal khác, chạy:
python scripts/test_download.py session_1234567890
```

Script sẽ:
- Test status check API
- Test download styled format
- Test download plain format
- Hiển thị kết quả và lưu test files

**2. Test full flow (cần manual interaction):**

```bash
python scripts/test_download.py
```

Script sẽ hướng dẫn các bước cần làm thủ công.

### Requirements:

```bash
pip install requests
```

### Output:

Script sẽ tạo các file test:
- `test_download_{file_id}_styled.xlsx`
- `test_download_{file_id}_plain.xlsx`

---

**Last Updated:** 2025-12-10


