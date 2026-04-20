import streamlit as st

from chat_ui import BACKEND_URL, upload_documents


def _dua_file_vao_hang_doi_tu_uploader(uploader_key):
    danh_sach_file = st.session_state.get(uploader_key) or []
    if not danh_sach_file:
        return

    st.session_state["staged_files"] = list(danh_sach_file)
    st.session_state["auto_upload_files"] = True
    st.session_state["modal_uploader_nonce"] += 1


def hien_thi_nut_tai_tai_lieu_ngay():
    uploader_key = f"sidebar_upload_{st.session_state['modal_uploader_nonce']}"
    danh_sach_file = st.file_uploader(
        " ",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key=uploader_key,
        label_visibility="collapsed",
        on_change=_dua_file_vao_hang_doi_tu_uploader,
        args=(uploader_key,),
    )

    if danh_sach_file:
        _dua_file_vao_hang_doi_tu_uploader(uploader_key)
        st.rerun()

def xu_ly_tai_lieu_tam():
    if not st.session_state["auto_upload_files"] or not st.session_state["staged_files"]:
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    def cap_nhat_tien_trinh(index, total_files, file_name):
        status_text.markdown(f"**Đang tải {index}/{total_files}:** `{file_name}`")
        progress_bar.progress(index / total_files)

    summary = upload_documents(
        uploaded_files=st.session_state["staged_files"],
        backend_url=BACKEND_URL,
        on_progress=cap_nhat_tien_trinh,
    )

    progress_bar.empty()
    status_text.empty()

    st.session_state["auto_upload_files"] = False
    st.session_state["staged_files"] = []

    if summary["success_count"] > 0:
        st.session_state["document_ids"] = list(
            dict.fromkeys(st.session_state["document_ids"] + summary["document_ids"])
        )
        st.session_state["uploaded_file_names"] = list(
            dict.fromkeys(st.session_state["uploaded_file_names"] + summary["successful_files"])
        )
        st.session_state["pending_auto_summary"] = True

        if summary["success_count"] == summary["total_files"]:
            st.success("Tài liệu đã được tải lên. AI đang chuẩn bị phần trả lời đầu tiên.")
        else:
            st.warning(
                f"Đã xử lý {summary['success_count']}/{summary['total_files']} tài liệu. "
                "AI sẽ tiếp tục với những tài liệu đã đọc thành công."
            )
    else:
        st.error("Chưa có tài liệu nào được xử lý thành công. Hãy thử tải lại.")
