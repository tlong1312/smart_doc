import html
import re

import streamlit as st

import chat_ui
from state import lam_moi_phien_chat, lay_ten_tai_lieu_dang_ket_noi
from upload import hien_thi_nut_tai_tai_lieu_ngay


@st.dialog("Xác nhận xóa lịch sử")
def confirm_clear_history_dialog():
    st.write("Bạn có chắc muốn xóa toàn bộ nội dung phiên đang mở không?")
    col_cancel, col_confirm = st.columns(2, gap="small")

    if col_cancel.button("Hủy", key="cancel_clear_history", use_container_width=True):
        st.rerun()

    if col_confirm.button("Xác nhận xóa", key="confirm_clear_history", use_container_width=True):
        try:
            chat_ui.delete_messages_in_active_session()
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


@st.dialog("Xác nhận xóa Vector Store")
def confirm_clear_vector_store_dialog():
    st.write("Thao tác này sẽ xóa toàn bộ tài liệu đã tải lên và index tìm kiếm. Bạn có chắc muốn tiếp tục?")
    col_cancel, col_confirm = st.columns(2, gap="small")

    if col_cancel.button("Hủy", key="cancel_clear_vector_store", use_container_width=True):
        st.rerun()

    if col_confirm.button("Xác nhận xóa", key="confirm_clear_vector_store", use_container_width=True):
        try:
            chat_ui.clear_vector_store()
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


@st.dialog("Xác nhận xóa tất cả")
def confirm_delete_all_sessions_dialog():
    st.write("Bạn có chắc muốn xóa toàn bộ lịch sử hội thoại không? Hành động này không thể hoàn tác.")
    col_cancel, col_confirm = st.columns(2, gap="small")

    if col_cancel.button("Hủy", key="cancel_delete_all_sessions", use_container_width=True):
        st.rerun()

    if col_confirm.button("Xóa hết", key="confirm_delete_all_sessions", use_container_width=True):
        try:
            chat_ui.delete_all_sessions()
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


@st.dialog("Xác nhận xóa đoạn chat")
def confirm_delete_session_dialog(session_id):
    st.write("Bạn có chắc muốn xóa đoạn chat này không? Hành động này không thể hoàn tác.")

    col_cancel, col_confirm = st.columns(2, gap="small")

    if col_cancel.button("Hủy", key=f"cancel_delete_session_{session_id}", use_container_width=True):
        st.rerun()

    if col_confirm.button("Xóa", key=f"confirm_delete_session_{session_id}", use_container_width=True):
        try:
            chat_ui.delete_session(session_id)
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


def _tom_tat_ngan_cho_sidebar(raw_preview):
    if not raw_preview:
        return "Phiên hội thoại mới"

    preview = " ".join(str(raw_preview).split())
    if not preview:
        return "Phiên hội thoại mới"

    preview = re.sub(r"^(?:Nguoi dung|Người dùng|AI|Assistant|User)\s*:\s*", "", preview, flags=re.IGNORECASE)
    preview = preview.strip("`*_>- ")

    first_clause = re.split(r"[.!?\n]", preview, maxsplit=1)[0].strip()
    title = first_clause or preview

    if title.lower().startswith("tài liệu cung cấp không chứa thông tin"):
        title = "Không có thông tin trong tài liệu"

    max_len = 34
    if len(title) <= max_len:
        return title

    truncated = title[: max_len + 1].rsplit(" ", 1)[0].strip()
    if len(truncated) < 12:
        truncated = title[:max_len].strip()
    return f"{truncated}..."


def _hien_thi_danh_sach_hoi_thoai():
    da_mo = st.session_state.setdefault("recent_sessions_expanded", True)
    nhan_header = "Gần đây ▾" if da_mo else "Gần đây ▸"
    sessions = chat_ui.refresh_session_history()
    active_session_id = st.session_state.get("active_session_id")

    col_header, col_clear = st.columns([4.2, 2], gap="small")
    with col_header:
        if st.button(nhan_header, key="toggle_recent_sessions", use_container_width=True):
            st.session_state["recent_sessions_expanded"] = not da_mo
            st.rerun()

    with col_clear:
        if sessions and st.button("🗑", key="clear_all_sessions_btn", use_container_width=True):
            confirm_delete_all_sessions_dialog()

    if not st.session_state.get("recent_sessions_expanded", True):
        return

    if st.session_state.get("session_api_error"):
        st.caption(st.session_state["session_api_error"])

    if not sessions:
        st.caption("Chưa có session nào trên backend.")
        return

    for session in sessions[:12]:
        session_id = session.get("session_id")
        if not session_id:
            continue

        preview = session.get("last_message_preview")
        title = _tom_tat_ngan_cho_sidebar(preview)
        documents = session.get("documents", [])
        is_active = active_session_id == session_id

        row_key = f"{'active_session_row' if is_active else 'session_row'}_{session_id}"
        with st.container(key=row_key):
            col_open, col_delete = st.columns([6.4, 1.6], gap="small")

            with col_open:
                if st.button(title, key=f"open_session_{session_id}", use_container_width=True):
                    try:
                        chat_ui.open_session(session_id, documents=documents)
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))

            with col_delete:
                if st.button("🗑", key=f"delete_session_sidebar_{session_id}", use_container_width=True):
                    confirm_delete_session_dialog(session_id)


def hien_thi_thanh_ben():
    with st.sidebar:
        if st.button("Đoạn chat mới", key="new_chat_primary", use_container_width=True):
            lam_moi_phien_chat()
            st.rerun()

        hien_thi_nut_tai_tai_lieu_ngay()

        ten_tai_lieu = lay_ten_tai_lieu_dang_ket_noi()
        so_tai_lieu = len(ten_tai_lieu)

        if ten_tai_lieu:
            danh_sach_tai_lieu = "".join(
                f'<div class="connection-chip">{html.escape(file_name)}</div>'
                for file_name in ten_tai_lieu
            )
            st.markdown(
                f"""
                <div class="connection-card">
                    <div class="connection-card__label">Tài liệu trong phiên</div>
                    <div class="connection-card__title">{so_tai_lieu} tài liệu đang kết nối</div>
                    <div class="connection-card__hint">Các file này sẽ được dùng làm ngữ cảnh trả lời.</div>
                    <div class="connection-chip-list">
                        {danh_sach_tai_lieu}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="connection-card">
                    <div class="connection-card__label">Tài liệu trong phiên</div>
                    <div class="connection-card__title">Chưa có tài liệu nào được chọn</div>
                    <div class="connection-empty">Tải PDF hoặc DOCX để bắt đầu một cuộc trò chuyện có ngữ cảnh.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


        _hien_thi_danh_sach_hoi_thoai()

        st.markdown('<div class="sidebar-section">Quản lý</div>', unsafe_allow_html=True)

        if st.button("Xóa lịch sử phiên", key="clear_history_btn", use_container_width=True):
            confirm_clear_history_dialog()

        if st.button("Xóa toàn bộ vector store", key="clear_vector_store_btn", use_container_width=True):
            confirm_clear_vector_store_dialog()


def hien_thi_tieu_de_trang():
    st.markdown(
        """
        <div class="topbar">
            <div class="topbar__badge">&#128218; SmartDoc AI • RAG Workspace</div>
            <h3>Trợ lý hỏi đáp tài liệu theo chuẩn báo cáo</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hien_thi_trang_trong():
    st.markdown(
        """
        <div class="empty-state">
            <h2>Khi bạn sẵn sàng, chúng ta có thể bắt đầu.</h2>
            <p>
                Tải tài liệu PDF hoặc DOCX để AI đọc nội dung, tự tạo tóm tắt ban đầu
                và trả lời các câu hỏi tiếp theo ngay trong cùng một khung chat.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hien_thi_tai_lieu_da_tai():
    file_names = st.session_state["uploaded_file_names"]
    if not file_names:
        return

    pills = "".join(
        f'<div class="doc-pill">&#128196; {html.escape(file_name)}</div>'
        for file_name in file_names
    )
    st.markdown(f'<div class="doc-strip">{pills}</div>', unsafe_allow_html=True)
