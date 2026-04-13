import html

import requests
import streamlit as st


BACKEND_URL = "http://127.0.0.1:8000/api"
UPLOAD_API_URL = f"{BACKEND_URL}/upload/"
CHAT_API_URL = f"{BACKEND_URL}/chat/"
AUTO_SUMMARY_PROMPT = (
    "Hãy tóm tắt ngắn gọn nội dung chính của các tài liệu vừa tải lên bằng tiếng Việt. "
    "Trình bày rõ ràng, súc tích và bám đúng nội dung tài liệu."
)


def _extract_error_message(response):
    try:
        payload = response.json()
    except ValueError:
        return f"HTTP {response.status_code}"

    return payload.get("error") or payload.get("detail") or f"HTTP {response.status_code}"


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
                f"{backend_url}/upload/",
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
            f"{backend_url}/chat/",
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


def render_sources(sources):
    with st.expander("Nguồn tham chiếu"):
        for source in sources:
            if isinstance(source, dict):
                file_name = html.escape(str(source.get("file_name") or "Tài liệu"))
                page = html.escape(str(source.get("page") or "?"))
                content = html.escape(str(source.get("content") or ""))
                st.markdown(f"**{file_name}** · Trang {page}")
                if content:
                    st.caption(content)
            else:
                st.markdown(html.escape(str(source)))
            st.divider()


def push_recent_prompt(prompt):
    title = " ".join(prompt.split())
    if len(title) > 52:
        title = f"{title[:49]}..."

    recent_chats = [item for item in st.session_state["recent_chats"] if item != title]
    recent_chats.insert(0, title)
    st.session_state["recent_chats"] = recent_chats[:8]


def _hien_thi_lich_su_tin_nhan():
    for tin_nhan in st.session_state["messages"]:
        with st.chat_message(tin_nhan["role"]):
            if tin_nhan.get("auto_generated"):
                st.markdown(
                    '<div class="auto-summary-label">Tóm tắt tự động sau khi tải tài liệu</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(tin_nhan["content"])
            if tin_nhan.get("sources"):
                render_sources(tin_nhan["sources"])


def _xu_ly_tom_tat_tu_dong():
    if not st.session_state.get("pending_auto_summary") or not st.session_state.get("document_ids"):
        return

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
            render_sources(ket_qua["sources"])

        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": ket_qua["answer"],
                "sources": ket_qua["sources"],
                "auto_generated": True,
            }
        )
        st.session_state["session_id"] = ket_qua["session_id"]
        st.session_state["pending_auto_summary"] = False


def _xu_ly_cau_hoi_nguoi_dung():
    cau_hoi = st.chat_input(
        "Hỏi bất kỳ điều gì về tài liệu của bạn",
        disabled=not bool(st.session_state.get("document_ids")),
    )

    if not cau_hoi:
        return

    push_recent_prompt(cau_hoi)
    st.session_state["messages"].append({"role": "user", "content": cau_hoi})

    with st.chat_message("user"):
        st.markdown(cau_hoi)

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
            render_sources(ket_qua["sources"])

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": ket_qua["answer"],
            "sources": ket_qua["sources"],
        }
    )
    st.session_state["session_id"] = ket_qua["session_id"]


def render_chat_interface():
    _hien_thi_lich_su_tin_nhan()
    _xu_ly_tom_tat_tu_dong()
    _xu_ly_cau_hoi_nguoi_dung()
