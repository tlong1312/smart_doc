import html
import re

import streamlit as st

import chat_ui
from state import lam_moi_phien_chat, lay_ten_tai_lieu_dang_ket_noi
from upload import hien_thi_nut_tai_tai_lieu_ngay


@st.dialog("Xác nhận xóa")
def confirm_delete_dialog(session_id):
    st.write("Bạn có chắc muốn xóa hội thoại này? Hành động này không thể hoàn tác.")
    col_cancel, col_confirm = st.columns(2, gap="small")

    if col_cancel.button("Hủy", key=f"cancel_delete_session_{session_id}", use_container_width=True):
        st.rerun()

    if col_confirm.button(
        "Xác nhận xóa",
        key=f"confirm_delete_session_{session_id}",
        use_container_width=True,
    ):
        try:
            chat_ui.delete_session(session_id)
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


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

    max_len = 24
    if len(title) <= max_len:
        return f"Tóm: {title}"

    truncated = title[: max_len + 1].rsplit(" ", 1)[0].strip()
    if len(truncated) < 12:
        truncated = title[:max_len].strip()
    return f"Tóm: {truncated}..."


def _hien_thi_danh_sach_hoi_thoai():
    st.markdown('<div class="sidebar-section">Gần đây</div>', unsafe_allow_html=True)
    if st.button("Làm mới danh sách hội thoại", key="refresh_session_list", use_container_width=True):
        st.session_state["session_history_dirty"] = True

    sessions = chat_ui.refresh_session_history()
    active_session_id = st.session_state.get("active_session_id")

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

        with st.container(key=f"session_row_{session_id}"):
            col_open, col_delete = st.columns([6, 1], gap="small")
            open_label = f"{'● ' if is_active else ''}{title}"

            if col_open.button(open_label, key=f"open_session_{session_id}", use_container_width=True):
                try:
                    chat_ui.open_session(session_id, documents=documents)
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))

            with col_delete:
                with st.popover("⋮", use_container_width=True):
                    if st.button(
                        "Xóa 🗑️",
                        key=f"delete_session_{session_id}",
                        use_container_width=True,
                    ):
                        confirm_delete_dialog(session_id)


def hien_thi_thanh_ben():
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <span class="sidebar-brand__icon">&#128218;</span>
                <span>SmartDoc AI</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("+ Cuộc trò chuyện mới", key="new_chat_primary", use_container_width=True):
            lam_moi_phien_chat()
            st.rerun()

        hien_thi_nut_tai_tai_lieu_ngay()

        st.markdown('<div class="sidebar-section">Dự án</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="project-card">Trợ lý đọc và hỏi đáp tài liệu</div>',
            unsafe_allow_html=True,
        )

        ten_tai_lieu = lay_ten_tai_lieu_dang_ket_noi()
        so_tai_lieu = len(ten_tai_lieu)

        if ten_tai_lieu:
            danh_sach_tai_lieu = "".join(
                f'<div class="connection-chip">&#128196; {html.escape(file_name)}</div>'
                for file_name in ten_tai_lieu
            )
            st.markdown(
                f"""
                <div class="connection-card">
                    <div class="connection-card__title">Đang kết nối với {so_tai_lieu} tài liệu</div>
                    <div class="connection-card__hint">Các tài liệu này đang được gắn với phiên chat hiện tại.</div>
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
                    <div class="connection-card__title">Đang kết nối với 0 tài liệu</div>
                    <div class="connection-empty">Chưa có tài liệu nào được gắn vào phiên chat hiện tại.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


        _hien_thi_danh_sach_hoi_thoai()

        if st.button("Clear History", key="clear_history_btn", use_container_width=True):
            confirm_clear_history_dialog()

        if st.button("Clear Vector Store", key="clear_vector_store_btn", use_container_width=True):
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


def main():
    if "uploaded_file_names" not in st.session_state:
        st.session_state["uploaded_file_names"] = []
    if "modal_uploader_nonce" not in st.session_state:
        st.session_state["modal_uploader_nonce"] = 0
    if "document_ids" not in st.session_state:
        st.session_state["document_ids"] = []

    hien_thi_thanh_ben()
    hien_thi_tieu_de_trang()
    hien_thi_tai_lieu_da_tai()
    hien_thi_trang_trong()


if __name__ == "__main__":
    main()