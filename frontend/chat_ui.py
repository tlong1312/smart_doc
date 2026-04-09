import streamlit as st
import requests
import json

CHAT_API_URL = "http://127.0.0.1:8000/api/chat/"

def render_chat_ui():
    st.markdown("---")
    
    with st.sidebar:
        st.divider()
        debug_mode = st.checkbox("Kiểm tra JSON (Gửi/Nhận)", value=False)

    st.subheader("Trải nghiệm hỏi đáp thông minh")

    # KHỞI TẠO STATE 
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "last_debug_json" not in st.session_state:
        st.session_state.last_debug_json = None

    # hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # hiển thị nguồn cho tin nhắn của Assistant 
            if "sources" in message and message["sources"]:
                with st.expander("Xem nguồn tài liệu tham chiếu"):
                    for src in message["sources"]:
                        if isinstance(src, dict):
                            f_name = src.get('file_name', 'Tài liệu')
                            page = src.get('page', '?')
                            content = src.get('content', '')
                            st.markdown(f"**{f_name}** — *Trang {page}*")
                            if content: st.info(content)
                        else:
                            # Nếu nguồn chỉ là chuỗi text
                            st.markdown(f"{src}")
                        st.divider()

    # mảng id file
    doc_ids = st.session_state.get('document_ids', [])
    is_disabled = len(doc_ids) == 0

    # HIỂN THỊ DEBUG
    if debug_mode and st.session_state.last_debug_json:
        with st.expander("Chi tiết JSON gần nhất", expanded=True):
            st.write("**Request đã gửi:**")
            st.json(st.session_state.last_debug_json['request'])
            st.write("**Response đã nhận:**")
            st.json(st.session_state.last_debug_json['response'])

    if is_disabled:
        st.warning("Chưa có tài liệu. Vui lòng upload file ở phía trên trước.")

    # nhập input
    if prompt := st.chat_input("Nhập câu hỏi tại đây...", disabled=is_disabled):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        payload = {
            "message": prompt,
            "document_ids": doc_ids,
            "session_id": st.session_state.session_id
        }

        # GỌI API & BÓC TÁCH
        with st.chat_message("assistant"):
            with st.spinner("Đang truy vấn tài liệu..."):
                try:
                    response = requests.post(CHAT_API_URL, json=payload, timeout=90)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # lưu debug
                        st.session_state.last_debug_json = {"request": payload, "response": data}

                        answer = data.get("answer", "")
                        st.session_state.session_id = data.get("session_id")
                        sources = data.get("sources", [])

                        # show câu trả lời
                        st.markdown(answer)
                        
                        # sources
                        if sources:
                            with st.expander("Xem nguồn tài liệu tham chiếu"):
                                for src in sources:
                                    if isinstance(src, dict):
                                        f_name = src.get('file_name', 'Tài liệu')
                                        page = src.get('page', '?')
                                        content = src.get('content', '')
                                        st.markdown(f"**{f_name}** — *Trang {page}*")
                                        if content: st.info(content)
                                    else:
                                        st.markdown(f"{src}")
                                    st.divider()

                        # Lưu vào lịch sử tin nhắn
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": answer,
                            "sources": sources 
                        })
                        
                        # st.rerun() 
                        
                    else:
                        st.error(f"Lỗi {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Lỗi kết nối: {str(e)}")

def render_sidebar_tools():
    with st.sidebar:
        st.title("🛠 Công cụ")
        if st.button("Xóa lịch sử Chat"):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.session_state.last_debug_json = None
            st.rerun()