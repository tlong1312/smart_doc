import streamlit as st


GIA_TRI_MAC_DINH = {
    "document_ids": [],
    "uploaded_file_names": [],
    "messages": [],
    "session_id": None,
    "recent_chats": [],
    "show_upload_modal": True,
    "modal_uploader_nonce": 0,
    "staged_files": [],
    "auto_upload_files": False,
    "pending_auto_summary": False,
}


def _sao_chep_gia_tri(gia_tri):
    if isinstance(gia_tri, list):
        return list(gia_tri)
    if isinstance(gia_tri, dict):
        return dict(gia_tri)
    if isinstance(gia_tri, set):
        return set(gia_tri)
    return gia_tri


def khoi_tao_trang_thai():
    for khoa, gia_tri in GIA_TRI_MAC_DINH.items():
        if khoa not in st.session_state:
            st.session_state[khoa] = _sao_chep_gia_tri(gia_tri)


def lam_moi_phien_chat():
    st.session_state["document_ids"] = []
    st.session_state["session_id"] = None
    st.session_state["messages"] = []
    st.session_state["uploaded_file_names"] = []
    st.session_state["staged_files"] = []
    st.session_state["auto_upload_files"] = False
    st.session_state["pending_auto_summary"] = False
    st.session_state["show_upload_modal"] = True
    st.session_state["modal_uploader_nonce"] += 1


def lay_ten_tai_lieu_dang_ket_noi():
    document_ids = st.session_state["document_ids"]
    uploaded_file_names = st.session_state["uploaded_file_names"]

    labels = []
    for index, _document_id in enumerate(document_ids, start=1):
        if index - 1 < len(uploaded_file_names) and uploaded_file_names[index - 1]:
            labels.append(uploaded_file_names[index - 1])
        else:
            labels.append(f"Tài liệu {index}")

    return labels
