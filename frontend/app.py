import streamlit as st
import requests

# Cấu hình đường dẫn API Backend của bạn
BACKEND_URL = " http://127.0.0.1:8000/api"

st.set_page_config(page_title="SmartDoc AI", page_icon="📄")

st.title("🤖 SmartDoc AI - Intelligent Document Q&A System")

# Nơi tải file lên
uploaded_file = st.file_uploader("Tải lên tài liệu PDF hoặc DOCX", type=['pdf', 'docx'])

if st.button("Xử lý tài liệu"):
    if uploaded_file is not None:
        with st.spinner('Đang tải lên và xử lý dữ liệu (AI đang đọc)...'):
            # Chuẩn bị file để gửi qua API Django
            files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

            try:
                response = requests.post(f"{BACKEND_URL}/upload/",
                                         files=files)  # Trỏ đúng tên API trong urls.py
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Thành công! {data.get('message', '')}")
                    # Lưu lại ID tài liệu vào session_state để lát nữa hỏi đáp
                    st.session_state['document_id'] = data.get('document_id')
                else:
                    st.error(f"Lỗi hệ thống: {response.json().get('error', 'Không xác định')}")
            except Exception as e:
                st.error("Không thể kết nối đến Backend Server. Hãy chắc chắn Django đang chạy ở port 8000!")
    else:
        st.warning("Vui lòng chọn một file trước khi bấm xử lý.")

st.divider()
st.write("*(Khu vực Chat UI team FE sẽ code tiếp ở đây...)*")