# 🔄 API DELETE /api/clear-all/ - Backend Implementation

## 📋 Tóm tắt

Triển khai thành công API endpoint `DELETE /api/clear-all/` để Reset Factory toàn hệ thống ở **phía Backend**.

---

## ✅ Thay đổi Backend

### 1. **chat_app/views.py**
   📁 `C:\Users\ADMIN\Desktop\smart_doc\backend\chat_app\views.py`

   **Thêm:**
   - Import library `shutil` (dòng 2)
   - Hàm `clear_all_data()` (dòng 105-147)
   - Fix exception handling trong `chat_with_document()` (dòng 62-66)

   **Chức năng clear_all_data():**
   ```python
   @api_view(['DELETE'])
   def clear_all_data(request):
       # 1. Xóa tất cả bản ghi từ database (theo thứ tự CASCADE)
       ChatMessage.objects.all().delete()
       ChatSession.objects.all().delete()
       Document.objects.all().delete()
       
       # 2. Xóa thư mục uploads
       # Dùng shutil.rmtree() để xóa toàn bộ thư mục
       # Tạo lại thư mục trống với exist_ok=True
       
       # 3. Xóa thư mục global_index (FAISS Vector Store)
       # Dùng shutil.rmtree() để xóa FAISS index
       # Tạo lại thư mục trống với exist_ok=True
   ```

### 2. **chat_app/urls.py**
   📁 `C:\Users\ADMIN\Desktop\smart_doc\backend\chat_app\urls.py`

   **Thêm route mới:**
   ```python
   path('clear-all/', views.clear_all_data, name='clear_all_data'),
   ```

   **Endpoint:** `DELETE /api/clear-all/`

### 3. **chat_app/models.py**
   📁 `C:\Users\ADMIN\Desktop\smart_doc\backend\chat_app\models.py`

   **Fix ChatSession.__str__():**
   - ❌ Cũ: `return f"Session for {self.document.file_name}"` → Lỗi!
   - ✅ Mới: Kiểm tra `self.documents.all()` (ManyToMany)

---

## 🔧 API Endpoint

### **DELETE /api/clear-all/**

**Mô tả:** Xóa sạch toàn bộ dữ liệu hệ thống (Database + File System)

**Request:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/clear-all/
```

**Response (Success - 200):**
```json
{
    "message": "✅ Reset toàn bộ hệ thống thành công! Vector Store đã được xóa sạch."
}
```

**Response (Error - 500):**
```json
{
    "error": "Lỗi khi reset hệ thống: [chi tiết lỗi]"
}
```

---

## 🗑️ Xóa những gì?

### **Database (ORM):**
- ✅ Tất cả `ChatMessage` records
- ✅ Tất cả `ChatSession` records
- ✅ Tất cả `Document` records

### **File System (shutil.rmtree):**
- ✅ Thư mục `backend/uploads/` → xóa rồi tạo lại trống
- ✅ Thư mục `backend/faiss_index/global_index/` → xóa rồi tạo lại trống

---

## 🛡️ Error Handling

**Robust error handling:**
- Xóa database trước (3 tables theo CASCADE order)
- Wrap xóa thư mục trong try-except riêng
- Nếu xóa uploads fail → không dừng process
- Nếu xóa global_index fail → không dừng process
- Log lỗi ra console nhưng vẫn trả về 200 OK

---

## 📊 Các thư viện sử dụng

```python
import os              # Xử lý đường dẫn file
import shutil          # Xóa thư mục recursive (rmtree)
from django.conf import settings
from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
```

---

## 🚀 Cách sử dụng (Backend Only)

### **Test API via cURL:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/clear-all/
```

### **Test API via Python:**
```python
import requests
response = requests.delete("http://127.0.0.1:8000/api/clear-all/")
print(response.json())
```

### **Test API via Postman:**
1. Method: `DELETE`
2. URL: `http://127.0.0.1:8000/api/clear-all/`
3. Send

---

## ⚠️ Lưu ý quan trọng

1. **Không thể hoàn tác:** Bấm endpoint này sẽ xóa **vĩnh viễn** toàn bộ dữ liệu
2. **Xóa toàn bộ:** Cả database lẫn file hệ thống
3. **Production:** Nên thêm authentication (permission, token)
4. **Logging:** Nên log lại action này cho audit trail

---

## 📝 Cấu trúc code

```
backend/chat_app/
├── views.py          ← Thêm clear_all_data() function
├── urls.py           ← Thêm path('clear-all/', ...)
├── models.py         ← Fix ChatSession.__str__()
└── migrations/       ← (Không cần migration)
```

---

## ✨ Hoàn thành!

**Files đã chỉnh sửa:**
- ✅ `backend/chat_app/views.py` - clear_all_data() + exception handling
- ✅ `backend/chat_app/urls.py` - Route clear-all/
- ✅ `backend/chat_app/models.py` - Fix ChatSession model

**Frontend:** 🔵 Không thay đổi (người khác sẽ implement)

**Status:** 🟢 Backend Ready to use!

