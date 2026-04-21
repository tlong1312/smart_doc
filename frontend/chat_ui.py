import html
import hashlib

import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000/api"
SESSIONS_API_URL = f"{BACKEND_URL}/sessions/"
CLEAR_VECTOR_STORE_API_URL = f"{BACKEND_URL}/admin/vector-store/clear/"
AUTO_SUMMARY_PROMPT = (
    "Hãy tóm tắt ngắn gọn nội dung chính của các tài liệu vừa tải lên bằng tiếng Việt. "
    "Chỉ dùng thông tin có trong tài liệu; nếu thiếu thông tin thì nêu rõ phần còn thiếu."
)


def _queue_files_from_inline_uploader(uploader_key):
    selected_files = st.session_state.get(uploader_key) or []
    if not selected_files:
        return
    st.session_state["staged_files"] = list(selected_files)
    st.session_state["auto_upload_files"] = True
    st.session_state["modal_uploader_nonce"] = st.session_state.get("modal_uploader_nonce", 0) + 1


def _extract_error_message(response):
    try:
        payload = response.json()
    except ValueError:
        return f"HTTP {response.status_code}"

    return payload.get("error") or payload.get("detail") or f"HTTP {response.status_code}"


def refresh_session_history(force=False):
    if not force and not st.session_state.get("session_history_dirty", True):
        return st.session_state.get("session_history", [])

    try:
        response = requests.get(SESSIONS_API_URL, timeout=30)
    except requests.RequestException:
        st.session_state["session_api_error"] = "Không thể tải danh sách hội thoại từ backend."
        return st.session_state.get("session_history", [])

    if response.status_code != 200:
        st.session_state["session_api_error"] = _extract_error_message(response)
        return st.session_state.get("session_history", [])

    payload = response.json()
    sessions = payload.get("sessions", [])
    st.session_state["session_history"] = sessions
    st.session_state["session_history_dirty"] = False
    st.session_state["session_api_error"] = None
    return sessions


def load_session_messages(session_id):
    try:
        response = requests.get(f"{SESSIONS_API_URL}{session_id}/messages/", timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError("Không thể tải nội dung hội thoại. Kiểm tra backend.") from exc

    if response.status_code != 200:
        raise RuntimeError(_extract_error_message(response))

    payload = response.json()
    messages = payload.get("messages", [])
    parsed_messages = []
    for message in messages:
        sender = str(message.get("sender", "")).upper()
        role = "assistant" if sender == "AI" else "user"
        sources = message.get("sources") if isinstance(message.get("sources"), list) else []
        parsed_messages.append(
            {
                "role": role,
                "content": message.get("message", ""),
                "sources": sources,
            }
        )
    return parsed_messages


def open_session(session_id, documents=None):
    history_messages = load_session_messages(session_id)
    st.session_state["messages"] = history_messages
    st.session_state["session_id"] = session_id
    st.session_state["active_session_id"] = session_id
    st.session_state["pending_auto_summary"] = False

    docs = documents or []
    st.session_state["document_ids"] = [doc.get("id") for doc in docs if doc.get("id")]
    st.session_state["uploaded_file_names"] = [doc.get("file_name") for doc in docs if doc.get("file_name")]


def delete_session(session_id):
    try:
        response = requests.delete(f"{SESSIONS_API_URL}{session_id}/", timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError("Không thể xóa hội thoại. Kiểm tra backend.") from exc

    if response.status_code != 200:
        raise RuntimeError(_extract_error_message(response))

    if st.session_state.get("active_session_id") == session_id:
        st.session_state["messages"] = []
        st.session_state["session_id"] = None
        st.session_state["active_session_id"] = None
        st.session_state["document_ids"] = []
        st.session_state["uploaded_file_names"] = []
    st.session_state["session_history_dirty"] = True


def delete_all_sessions():
    sessions = refresh_session_history(force=True)
    session_ids = [session.get("session_id") for session in sessions if session.get("session_id")]

    if not session_ids:
        st.session_state["session_history"] = []
        st.session_state["session_history_dirty"] = False
        return

    errors = []
    for session_id in session_ids:
        try:
            response = requests.delete(f"{SESSIONS_API_URL}{session_id}/", timeout=30)
        except requests.RequestException:
            errors.append(str(session_id))
            continue

        if response.status_code != 200:
            errors.append(str(session_id))

    if errors:
        raise RuntimeError("Không thể xóa toàn bộ lịch sử hội thoại. Hãy thử lại.")

    st.session_state["messages"] = []
    st.session_state["session_id"] = None
    st.session_state["active_session_id"] = None
    st.session_state["document_ids"] = []
    st.session_state["uploaded_file_names"] = []
    st.session_state["pending_auto_summary"] = False
    st.session_state["pending_user_question"] = None
    st.session_state["session_history"] = []
    st.session_state["session_history_dirty"] = True
    st.session_state["session_api_error"] = None


def delete_messages_in_active_session():
    active_session_id = st.session_state.get("active_session_id")
    if not active_session_id:
        raise RuntimeError("Chưa có phiên hội thoại để xóa nội dung.")

    try:
        response = requests.delete(f"{SESSIONS_API_URL}{active_session_id}/messages/delete/", timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError("Không thể xóa nội dung hội thoại. Kiểm tra backend.") from exc

    if response.status_code != 200:
        raise RuntimeError(_extract_error_message(response))

    st.session_state["messages"] = []
    st.session_state["pending_user_question"] = None
    st.session_state["session_history_dirty"] = True


def clear_vector_store():
    try:
        response = requests.delete(CLEAR_VECTOR_STORE_API_URL, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError("Không thể xóa Vector Store. Kiểm tra backend.") from exc

    if response.status_code != 200:
        raise RuntimeError(_extract_error_message(response))

    st.session_state["document_ids"] = []
    st.session_state["uploaded_file_names"] = []
    st.session_state["pending_auto_summary"] = False
    st.session_state["pending_user_question"] = None
    st.session_state["messages"] = []
    st.session_state["session_id"] = None
    st.session_state["active_session_id"] = None
    st.session_state["session_history_dirty"] = True


def upload_documents(uploaded_files, backend_url, on_progress=None):
    summary = {
        "total_files": len(uploaded_files),
        "success_count": 0,
        "document_ids": [],
        "successful_files": [],
        "failed_files": [],
    }

    for index, file in enumerate(uploaded_files, start=1):
        if on_progress:
            on_progress(index, summary["total_files"], file.name)

        files_payload = {
            "file": (file.name, file.getvalue(), file.type or "application/octet-stream")
        }

        try:
            response = requests.post(
                f"{backend_url}/documents/upload/",
                files=files_payload,
                timeout=180,
            )
        except requests.RequestException:
            summary["failed_files"].append(f"{file.name}: Không thể kết nối backend.")
            continue

        if response.status_code == 200:
            data = response.json()
            document_id = data.get("document_id")
            if document_id:
                summary["document_ids"].append(document_id)
            summary["success_count"] += 1
            summary["successful_files"].append(file.name)
        else:
            error_message = _extract_error_message(response)
            summary["failed_files"].append(f"{file.name}: {error_message}")

    return summary


def ask_documents(question, document_ids, session_id, backend_url):
    payload = {
        "message": question,
        "document_ids": document_ids,
        "session_id": session_id,
    }

    try:
        response = requests.post(
            f"{backend_url}/chats/",
            json=payload,
            timeout=180,
        )
    except requests.RequestException as exc:
        raise RuntimeError("Không thể kết nối backend chat. Kiểm tra server ở cổng 8000.") from exc

    if response.status_code != 200:
        raise RuntimeError(_extract_error_message(response))

    data = response.json()
    return {
        "answer": data.get("answer", "").strip() or "AI chưa trả về nội dung.",
        "session_id": data.get("session_id"),
        "sources": data.get("sources", []),
    }


def _build_source_key(scope_key, index, file_name, page, content):
    raw = f"{scope_key}|{index}|{file_name}|{page}|{content[:120]}"
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"src_{digest}"


def render_sources(sources, scope_key="default"):
    with st.expander("Nguồn tham chiếu"):
        if not sources:
            st.caption("Chưa có nguồn tham chiếu cho câu trả lời này.")
            return

        for index, source in enumerate(sources, start=1):
            if isinstance(source, dict):
                file_name = str(source.get("file_name") or "Tài liệu không tên").strip() or "Tài liệu không tên"
                page = str(source.get("page") or "Không rõ trang").strip() or "Không rõ trang"
                content = str(source.get("content") or "").strip()
            else:
                file_name = "Nguồn tham chiếu"
                page = "Không rõ trang"
                content = str(source or "").strip()

            source_key = _build_source_key(scope_key, index, file_name, page, content)
            toggle_key = f"{source_key}_open"
            is_open = bool(st.session_state.get(toggle_key, False))

            st.markdown(f"**Nguồn {index}**")
            col_meta, col_action = st.columns([6, 2], gap="small")

            with col_meta:
                st.markdown(f"**{html.escape(file_name)}** · Trang {html.escape(page)}")

            with col_action:
                has_context = bool(content)
                label = "Ẩn ngữ cảnh" if is_open else "Xem ngữ cảnh"
                if st.button(
                    label,
                    key=f"{source_key}_btn",
                    use_container_width=True,
                    disabled=not has_context,
                ):
                    is_open = not is_open
                    st.session_state[toggle_key] = is_open

            if not content:
                st.caption("Nguồn này chưa có đoạn ngữ cảnh chi tiết.")
            elif is_open:
                st.markdown(
                    f'<div class="source-context-box">{html.escape(content)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                preview = content if len(content) <= 140 else f"{content[:137]}..."
                st.caption(f"Ngữ cảnh: {preview}")

            st.divider()


def _hien_thi_lich_su_tin_nhan():
    for msg_index, tin_nhan in enumerate(st.session_state["messages"]):
        role = tin_nhan["role"]
        with st.container(key=f"chat_{role}_message_{msg_index}"):
            with st.chat_message(role):
                if tin_nhan.get("auto_generated"):
                    st.markdown(
                        '<div class="auto-summary-label">Tóm tắt tự động sau khi tải tài liệu</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(tin_nhan["content"])
                if tin_nhan.get("sources"):
                    render_sources(tin_nhan["sources"], scope_key=f"history_{msg_index}")


def _xu_ly_tom_tat_tu_dong():
    if not st.session_state.get("pending_auto_summary") or not st.session_state.get("document_ids"):
        return

    with st.container(key="chat_assistant_auto_summary_live"):
        with st.chat_message("assistant"):
            st.markdown(
                '<div class="auto-summary-label">Tóm tắt tự động sau khi tải tài liệu</div>',
                unsafe_allow_html=True,
            )
            with st.spinner("Đang đọc tài liệu và tạo câu trả lời đầu tiên..."):
                try:
                    ket_qua = ask_documents(
                        question=AUTO_SUMMARY_PROMPT,
                        document_ids=st.session_state["document_ids"],
                        session_id=st.session_state.get("session_id"),
                        backend_url=BACKEND_URL,
                    )
                except RuntimeError as exc:
                    st.error(str(exc))
                    st.session_state["pending_auto_summary"] = False
                    return

            st.markdown(ket_qua["answer"])
            if ket_qua["sources"]:
                render_sources(ket_qua["sources"], scope_key="live_auto_summary")

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": ket_qua["answer"],
                "sources": ket_qua["sources"],
                "auto_generated": True,
            }
        )
        st.session_state["session_id"] = ket_qua["session_id"]
        st.session_state["active_session_id"] = ket_qua["session_id"]
        st.session_state["pending_auto_summary"] = False
        st.session_state["session_history_dirty"] = True


def _hien_thi_o_nhap_cau_hoi():
    with st.container(key="chat_composer_shell"):
        col_attach, col_input = st.columns([1, 15], gap="small")

        with col_attach:
            uploader_nonce = st.session_state.get("modal_uploader_nonce", 0)
            uploader_key = f"inline_attach_{uploader_nonce}"
            with st.popover("+", use_container_width=True):
                st.file_uploader(
                    "Tệp đính kèm",
                    type=["pdf", "docx"],
                    accept_multiple_files=True,
                    key=uploader_key,
                    label_visibility="collapsed",
                    on_change=_queue_files_from_inline_uploader,
                    args=(uploader_key,),
                )

        with col_input:
            return st.chat_input(
                "Hỏi bất kỳ điều gì",
                disabled=not bool(st.session_state.get("document_ids")),
            )

    return None


def _xu_ly_cau_hoi_dang_cho():
    cau_hoi = (st.session_state.get("pending_user_question") or "").strip()
    if not cau_hoi:
        return

    st.session_state["pending_user_question"] = None

    st.session_state["messages"].append({"role": "user", "content": cau_hoi})

    with st.container(key="chat_user_live"):
        with st.chat_message("user"):
            st.markdown(cau_hoi)

    with st.container(key="chat_assistant_live"):
        with st.chat_message("assistant"):
            with st.spinner("Đang tìm câu trả lời trong tài liệu..."):
                try:
                    ket_qua = ask_documents(
                        question=cau_hoi,
                        document_ids=st.session_state["document_ids"],
                        session_id=st.session_state.get("session_id"),
                        backend_url=BACKEND_URL,
                    )
                except RuntimeError as exc:
                    st.error(str(exc))
                    return

            st.markdown(ket_qua["answer"])
            if ket_qua["sources"]:
                render_sources(ket_qua["sources"], scope_key="live_user_answer")

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": ket_qua["answer"],
            "sources": ket_qua["sources"],
        }
    )
    st.session_state["session_id"] = ket_qua["session_id"]
    st.session_state["active_session_id"] = ket_qua["session_id"]
    st.session_state["session_history_dirty"] = True


def render_chat_interface():
    _hien_thi_lich_su_tin_nhan()
    _xu_ly_tom_tat_tu_dong()
    _xu_ly_cau_hoi_dang_cho()

    cau_hoi_moi = _hien_thi_o_nhap_cau_hoi()
    if cau_hoi_moi:
        st.session_state["pending_user_question"] = cau_hoi_moi
        st.rerun()
