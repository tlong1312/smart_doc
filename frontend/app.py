from pathlib import Path

import streamlit as st

from main import (
    hien_thi_tai_lieu_da_tai,
    hien_thi_thanh_ben,
    hien_thi_tieu_de_trang,
    hien_thi_trang_trong,
)
from state import khoi_tao_trang_thai
from upload import xu_ly_tai_lieu_tam

BASE_CSS = Path(__file__).with_name("style.css").read_text(encoding="utf-8")

MANDATORY_FLAT_CSS = (
    "<style>\n"
    + BASE_CSS
    + """

/* Primary button: + Cuoc tro chuyen moi */
[data-testid="stSidebar"] .st-key-new_chat_primary button {
    border-radius: 20px !important;
    border: 1px solid rgba(15, 23, 42, 0.12) !important;
    background: #ffffff !important;
    color: #111827 !important;
    font-weight: 700 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .st-key-new_chat_primary button:hover {
    background: #eaf3ff !important;
    border-color: rgba(0, 123, 255, 0.22) !important;
}

/* Hide Streamlit popover arrow icon while keeping label (\"⋮\", \"📎\") */
[data-testid="stPopover"] > button svg {
    display: none !important;
}

/* Flat, round popover trigger buttons */
[data-testid="stPopover"] > button {
    border-radius: 999px !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
    border: 1px solid transparent !important;
    display: inline-flex !important;
    justify-content: center !important;
    align-items: center !important;
    background-color: transparent !important;
    color: #6b7280 !important;
}
[data-testid="stPopover"] > button:hover {
    background-color: rgba(150, 150, 150, 0.15) !important;
    border-color: #e5e7eb !important;
    color: #1f2937 !important;
}

/* Keep 3-dot menu hidden until conversation row is hovered */
[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] [data-testid="stPopover"] {
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
}
[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:hover [data-testid="stPopover"] {
    opacity: 1;
}

/* Conversation buttons in sidebar */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: left !important;
    font-weight: 500 !important;
    padding: 6px 10px !important;
    width: 100% !important;
    transition: background-color 0.2s ease;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background-color: rgba(150, 150, 150, 0.1) !important;
    border-radius: 10px !important;
}

/* Sidebar utility buttons look less plain and stay left aligned */
[data-testid="stSidebar"] .st-key-refresh_session_list button,
[data-testid="stSidebar"] .st-key-clear_history_btn button,
[data-testid="stSidebar"] .st-key-clear_vector_store_btn button {
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 12px !important;
    border: 1px solid rgba(15, 23, 42, 0.12) !important;
    background: #ffffff !important;
    color: #1f2937 !important;
}
[data-testid="stSidebar"] .st-key-refresh_session_list button:hover,
[data-testid="stSidebar"] .st-key-clear_history_btn button:hover,
[data-testid="stSidebar"] .st-key-clear_vector_store_btn button:hover {
    background: #f7fbff !important;
}

/* History rows: subtle bordered cards, no weird center/indent feeling */
[data-testid="stSidebar"] [class*="st-key-session_row_"] [data-testid="stHorizontalBlock"] {
    border: 1px solid rgba(15, 23, 42, 0.1);
    border-radius: 12px;
    background: #ffffff;
    padding: 4px;
    margin-bottom: 8px;
}
[data-testid="stSidebar"] [class*="st-key-session_row_"] [data-testid="column"]:first-child button {
    justify-content: flex-start !important;
    text-align: left !important;
    border: none !important;
    background: transparent !important;
    min-height: 34px !important;
    padding-left: 8px !important;
}
[data-testid="stSidebar"] [class*="st-key-session_row_"] [data-testid="column"]:first-child button p {
    text-align: left !important;
}

/* Sidebar smooth scrolling for long session list */
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    overflow-y: auto !important;
    scroll-behavior: smooth;
    overscroll-behavior: contain;
}

/* Chat input docked and full width to align with chat thread */
div[data-testid="stChatInput"] {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
}

/* Keep dialog centered and buttons visually aligned */
div[data-testid="stDialog"] section[role="dialog"] {
    width: min(480px, 90vw) !important;
    min-width: min(480px, 90vw) !important;
    max-width: min(480px, 90vw) !important;
}

/* Source context card in citation expander */
.source-context-box {
    border: 1px solid rgba(0, 123, 255, 0.16);
    background: rgba(234, 243, 255, 0.45);
    border-radius: 10px;
    padding: 10px 12px;
    color: #334155;
    font-size: 0.9rem;
    line-height: 1.6;
}

</style>"""
)

st.set_page_config(
    page_title="SmartDoc AI",
    page_icon=":blue_book:",
    layout="wide",
    initial_sidebar_state="expanded",
)

khoi_tao_trang_thai()
# Luôn tắt popup upload tự động; upload chỉ qua nút/ghim đính kèm.
st.session_state["show_upload_modal"] = False


st.markdown(MANDATORY_FLAT_CSS, unsafe_allow_html=True)

hien_thi_thanh_ben()


hien_thi_tieu_de_trang()
xu_ly_tai_lieu_tam()

if not st.session_state["messages"] and not st.session_state["pending_auto_summary"]:
    hien_thi_trang_trong()

hien_thi_tai_lieu_da_tai()

import chat_ui
chat_ui.render_chat_interface()