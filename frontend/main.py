import html

import streamlit as st

from state import lam_moi_phien_chat, lay_ten_tai_lieu_dang_ket_noi
from upload import hien_thi_nut_tai_tai_lieu_ngay


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

        if st.button("Làm mới Phiên Chat", use_container_width=True):
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

        st.markdown('<div class="sidebar-section">Gần đây</div>', unsafe_allow_html=True)
        recent_chats = st.session_state["recent_chats"]
        if recent_chats:
            for title in recent_chats[:8]:
                st.markdown(
                    f'<div class="recent-card">{html.escape(title)}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Chưa có lịch sử đoạn chat.")


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
