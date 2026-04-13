# 🔄 API DELETE /api/clear-all/ - Reset Factory Implementation

## 📋 Tóm tắt công việc đã hoàn thành

Đã triển khai thành công API endpoint `DELETE /api/clear-all/` để thực hiện Reset Factory toàn hệ thống.

---

## ✅ Chi tiết thay đổi

### 1. **Backend - views.py** 
   📁 `C:\Users\ADMIN\Desktop\smart_doc\backend\chat_app\views.py`

   **Thêm:**
   - Import library `shutil` (dòng 2)
   - Hàm `clear_all_data()` (dòng 102-134)

   **Chức năng:**
   ```python
   @api_view(['DELETE'])
   def clear_all_data(request):
       # 1. Xóa tất cả bản ghi từ database
       Document.objects.all().delete()          # Xóa tất cả tài liệu
       ChatSession.objects.all().delete()       # Xóa tất cả phiên chat
       ChatMessage.objects.all().delete()       # Xóa tất cả tin nhắn
       
       # 2. Xóa thư mục uploads
       # Dùng shutil.rmtree() để xóa toàn bộ thư mục
       # Tạo lại thư mục trống
       
       # 3. Xóa thư mục global_index (Vector Store)
       # Dùng shutil.rmtree() để xóa FAISS index
       # Tạo lại thư mục trống
   ```

---

### 2. **URL Configuration - urls.py**
   📁 `C:\Users\ADMIN\Desktop\smart_doc\backend\chat_app\urls.py`

   **Thêm route mới:**
   ```python
   path('clear-all/', views.clear_all_data, name='clear_all_data'),
   ```

   **URL cuối cùng:** `DELETE /api/clear-all/`

---

### 3. **Frontend - app.py (Streamlit)**
   📁 `C:\Users\ADMIN\Desktop\smart_doc\frontend\app.py`

   **Thêm:**
   - Nút "🗑️ Clear Vector Store" (dòng 84)
   - Giao diện 3 cột (col1, col2, col3) để căn giữa nút
   - Xử lý response từ Backend

   **Tính năng:**
   - Hiển thị thông báo thành công khi reset
   - Reset `session_state['document_ids']` về rỗng
   - Gọi `st.rerun()` để reload giao diện

---

## 🔧 API Endpoint

### **DELETE /api/clear-all/**

**Request:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/clear-all/
```

**Response (Success):**
```json
{
    "message": "✅ Reset toàn bộ hệ thống thành công! Vector Store đã được xóa sạch."
}
```
- Status Code: `200 OK`

**Response (Error):**
```json
{
    "error": "Lỗi khi reset hệ thống: [chi tiết lỗi]"
}
```
- Status Code: `500 INTERNAL_SERVER_ERROR`

---

## 🗑️ Xóa những gì?

### **Database:**
- ✅ Tất cả `Document` records
- ✅ Tất cả `ChatSession` records
- ✅ Tất cả `ChatMessage` records

### **File System:**
- ✅ Thư mục `backend/uploads/` (xóa rồi tạo lại trống)
- ✅ Thư mục `backend/faiss_index/global_index/` (xóa rồi tạo lại trống)

---

## 🎯 Cách sử dụng

### **Frontend (Streamlit):**
1. Mở giao diện SmartDoc AI
2. Tìm nút "🗑️ Clear Vector Store" ở giữa màn hình
3. Click nút → Xác nhận reset
4. Thấy thông báo thành công ✅ → Hệ thống đã reset hoàn toàn

### **API Direct:**
```bash
# Via curl
curl -X DELETE http://127.0.0.1:8000/api/clear-all/

# Via Python requests
import requests
response = requests.delete("http://127.0.0.1:8000/api/clear-all/")
print(response.json())
```

---

## ⚠️ Lưu ý quan trọng

1. **Không thể hoàn tác:** Bấm "Clear Vector Store" sẽ xóa vĩnh viễn toàn bộ dữ liệu
2. **Xóa toàn bộ:** Cả database lẫn file hệ thống
3. **Bảo mật:** Nên thêm authentication nếu dùng production
4. **MEDIA_ROOT:** Hiện tại code sử dụng `settings.BASE_DIR` để tìm đường dẫn uploads

---

## 📊 Các thư viện sử dụng

- `os` - Xử lý đường dẫn file
- `shutil` - Xóa thư mục recursive (rmtree)
- `Django ORM` - Xóa database records (.delete())
- `Django REST Framework` - @api_view decorator

---

## ✨ Hoàn thành!

**Files đã chỉnh sửa:**
- ✅ `backend/chat_app/views.py` - Thêm hàm clear_all_data()
- ✅ `backend/chat_app/urls.py` - Thêm route clear-all/
- ✅ `frontend/app.py` - Thêm nút Clear Vector Store

**Status:** 🟢 Ready to use

