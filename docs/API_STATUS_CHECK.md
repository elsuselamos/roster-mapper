# API Status Check - Giải pháp tốt hơn Redirect

## 📊 So sánh: Redirect vs API Status Check

| Tiêu chí | Redirect (Hiện tại) | API Status Check (Mới) |
|----------|---------------------|------------------------|
| **Cloud Run Multi-instance** | ❌ Lỗi (session files không shared) | ✅ Hoạt động (check processed files) |
| **Progress Tracking** | ❌ Không có | ✅ Có thể thêm progress |
| **Error Handling** | ⚠️ Khó xử lý | ✅ Dễ xử lý lỗi |
| **User Experience** | ⚠️ Phải đợi redirect | ✅ Có thể hiển thị loading/status |
| **Timeout Handling** | ❌ User không biết | ✅ Frontend có thể retry |
| **Implementation** | ✅ Đơn giản | ⚠️ Cần thêm code frontend |

## ✅ Kết luận: **API Status Check tốt hơn** cho Cloud Run

---

## 🚀 Cách sử dụng

### 1. Endpoint mới: `GET /api/v1/results/status`

**Request:**
```bash
GET /api/v1/results/status?session_id=session_1234567890
```

**Response:**
```json
{
  "status": "completed",  // "processing", "completed", "failed", "not_found"
  "session_id": "session_1234567890",
  "message": "Processing completed. 1 file(s) processed.",
  "results": {
    "files": [
      {
        "file_id": "abc-123",
        "filename": "roster.xlsx",
        "station": "HAN",
        "stats": {...},
        "download_url_styled": "/api/v1/download/abc-123?format=styled",
        "download_url_plain": "/api/v1/download/abc-123?format=plain"
      }
    ]
  }
}
```

### 2. POST /process hỗ trợ JSON response

**Nếu request có header `Accept: application/json`:**
```json
{
  "success": true,
  "session_id": "session_1234567890",
  "message": "Processing completed. 1 file(s) processed.",
  "results_url": "/results?session_id=session_1234567890",
  "status_url": "/api/v1/results/status?session_id=session_1234567890",
  "files_count": 1
}
```

---

## 💻 Frontend Implementation (JavaScript)

### Option 1: AJAX với Polling (Khuyến nghị)

```javascript
// Submit form với AJAX
async function processFiles() {
    const form = document.querySelector('form[action="/process"]');
    const formData = new FormData(form);
    
    // Show loading
    showLoading('⚙️ Đang mapping...', 'Đang xử lý file của bạn');
    
    try {
        // Submit với AJAX
        const response = await fetch('/process', {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Processing failed');
        }
        
        const data = await response.json();
        const sessionId = data.session_id;
        
        // Poll for status
        await pollStatus(sessionId);
        
    } catch (error) {
        hideLoading();
        alert('Lỗi: ' + error.message);
    }
}

// Poll status until completed
async function pollStatus(sessionId, maxAttempts = 60) {
    let attempts = 0;
    
    const checkStatus = async () => {
        attempts++;
        
        try {
            const response = await fetch(`/api/v1/results/status?session_id=${sessionId}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
                hideLoading();
                // Redirect to results page
                window.location.href = `/results?session_id=${sessionId}`;
                return;
            }
            
            if (data.status === 'failed') {
                hideLoading();
                alert('Lỗi xử lý: ' + data.message);
                return;
            }
            
            // Still processing, poll again
            if (attempts < maxAttempts) {
                setTimeout(checkStatus, 2000); // Check every 2 seconds
            } else {
                hideLoading();
                alert('Timeout: Xử lý mất quá nhiều thời gian');
            }
            
        } catch (error) {
            console.error('Status check error:', error);
            if (attempts < maxAttempts) {
                setTimeout(checkStatus, 2000);
            } else {
                hideLoading();
                alert('Lỗi kiểm tra trạng thái');
            }
        }
    };
    
    // Start polling after 2 seconds
    setTimeout(checkStatus, 2000);
}
```

### Option 2: Form Submit + Polling (Giữ nguyên form, thêm polling)

```javascript
// Attach to form submit
document.querySelector('form[action="/process"]').addEventListener('submit', async (e) => {
    // Let form submit normally, but also start polling
    // Extract session_id from redirect URL
    const originalSubmit = e.target.submit;
    
    // Intercept redirect
    window.addEventListener('beforeunload', () => {
        // Try to get session_id from URL if redirected
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');
        if (sessionId) {
            pollStatus(sessionId);
        }
    });
});
```

---

## 🔧 Backend Implementation

### Đã thêm:

1. **`GET /api/v1/results/status`** - Check processing status
2. **POST `/process`** - Hỗ trợ JSON response nếu `Accept: application/json`

### Flow:

```
1. User submits form → POST /process
2. Backend processes files (sync, blocking)
3. Backend saves results to OUTPUT_DIR/results/{session_id}.json
4. Backend returns:
   - JSON (if Accept: application/json) → {session_id, status_url}
   - Redirect (default) → /results?session_id={session_id}
5. Frontend polls GET /api/v1/results/status?session_id={session_id}
6. When status === "completed" → Show results or redirect
```

---

## 📝 Lưu ý

### Ưu điểm:
- ✅ Hoạt động tốt với Cloud Run multi-instance
- ✅ Có thể thêm progress tracking trong tương lai
- ✅ Better error handling
- ✅ Frontend có control tốt hơn

### Nhược điểm:
- ⚠️ Cần thêm code frontend (polling)
- ⚠️ Tăng số lượng requests (polling)

### Tối ưu trong tương lai:
- WebSocket cho real-time updates
- Server-Sent Events (SSE) cho progress streaming
- Background job queue (Celery, RQ) cho async processing

---

## 🧪 Testing

```bash
# 1. Start processing (get session_id)
curl -X POST http://localhost:8000/process \
  -H "Accept: application/json" \
  -F "file=@roster.xlsx"

# Response:
# {"success": true, "session_id": "session_1234567890", ...}

# 2. Check status
curl "http://localhost:8000/api/v1/results/status?session_id=session_1234567890"

# Response:
# {"status": "completed", "results": {...}, ...}
```

---

**Version:** 1.2.0  
**Last Updated:** 2025-12-13  
**Status:** Production Ready

---

## 🔗 Related Documentation

- **Deployment Guide**: `README.md` - Section "🚀 Production Deployment"
- **API Specification**: `docs/API_SPEC.md` - Complete API documentation
- **Deployment Context**: `docs/CONTEXT_SESSION.md` - Quick reference


