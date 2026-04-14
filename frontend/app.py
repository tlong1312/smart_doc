import streamlit as st
import requests

import chat_ui

# Cấu hình đường dẫn API Backend của bạn
BACKEND_URL = "http://127.0.0.1:8000/api"
UPLOAD_API_URL = f"{BACKEND_URL}/documents/upload/"

# ==========================================
# 1. KHỞI TẠO BỘ NHỚ LƯU ID TÀI LIỆU
# ==========================================
# Phải là mảng [] để tích lũy dần mỗi khi user up thêm file
if 'document_ids' not in st.session_state:
    st.session_state['document_ids'] = []

st.set_page_config(page_title="SmartDoc AI", page_icon="📄")
st.title("🤖 SmartDoc AI - Intelligent Document Q&A System")

# ==========================================
# 2. KHU VỰC UPLOAD (Cho phép chọn nhiều file)
# ==========================================
uploaded_files = st.file_uploader(
    "Tải lên tài liệu PDF hoặc DOCX (Có thể chọn nhiều file)",
    type=['pdf', 'docx'],
    accept_multiple_files=True
)

if st.button("Xử lý tài liệu"):
    if uploaded_files:
        # Giao diện loading xịn xò
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_files = len(uploaded_files)
        success_count = 0

        # ==========================================
        # 3. VÒNG LẶP UPLOAD TỪNG FILE XUỐNG BACKEND
        # ==========================================
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Đang xử lý {i + 1}/{total_files}: {file.name}...")

            # Đóng gói đúng 1 file cho mỗi lần gọi API (khớp với BE của bạn)
            files_payload = {'file': (file.name, file.getvalue(), file.type)}

            try:
                # Bắn request POST
                response = requests.post(UPLOAD_API_URL, files=files_payload)

                if response.status_code == 200:
                    data = response.json()
                    new_id = data.get('document_id')  # Lấy ID Backend trả về

                    if new_id:
                        # TUYỆT CHIÊU: Nhét ID mới vào kho lưu trữ chung
                        st.session_state['document_ids'].append(new_id)
                    success_count += 1
                else:
                    st.error(f"Lỗi file {file.name}: {response.json().get('error', 'Lỗi không xác định')}")

            except Exception as e:
                st.error(f"Không thể kết nối Backend khi up file {file.name}! Kiểm tra port 8000.")

            # Tăng thanh tiến trình lên (ví dụ up 1/2 file thì thanh chạy 50%)
            progress_bar.progress((i + 1) / total_files)

        # ==========================================
        # 4. DỌN DẸP & THÔNG BÁO HOÀN TẤT
        # ==========================================
        # Xóa các ID trùng lặp phòng trường hợp user up 1 file 2 lần
        st.session_state['document_ids'] = list(set(st.session_state['document_ids']))

        status_text.text(f"Hoàn tất! Đã đọc thành công {success_count}/{total_files} tài liệu.")

    else:
        st.warning("Vui lòng chọn ít nhất 1 file trước khi bấm xử lý.")

st.divider()

# ==========================================
# 5. HIỂN THỊ TRẠNG THÁI CHO USER BIẾT
# ==========================================
if st.session_state['document_ids']:
    st.info(
        f"📚 Hệ thống đang ghi nhớ **{len(st.session_state['document_ids'])}** tài liệu. Đã sẵn sàng để trả lời câu hỏi!")
else:
    st.write("*(Chưa có tài liệu nào trong bộ nhớ...)*")
chat_ui.render_sidebar_tools()
chat_ui.render_chat_ui()
