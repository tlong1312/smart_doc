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
    min-height: 3rem !important;
    justify-content: flex-start !important;
    padding: 0 1rem !important;
    border-radius: 16px !important;
    border: 1px solid rgba(15, 23, 42, 0.08) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.9)) !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05) !important;
    transition:
        background-color 0.16s ease,
        border-color 0.16s ease,
        transform 0.16s ease,
        box-shadow 0.16s ease !important;
}
[data-testid="stSidebar"] .st-key-new_chat_primary button:hover {
    background: #ffffff !important;
    border-color: rgba(15, 23, 42, 0.12) !important;
    transform: translateY(-1px);
    box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08) !important;
}
[data-testid="stSidebar"] .st-key-new_chat_primary button:active {
    background: #eef2f7 !important;
    border-color: rgba(15, 23, 42, 0.1) !important;
    transform: translateY(0);
    box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05) !important;
}
[data-testid="stSidebar"] .st-key-new_chat_primary button p {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    margin: 0 !important;
    text-align: left !important;
}

/* Hide Streamlit popover arrow icon while keeping label (\"⋮\", \"📎\") */
[data-testid="stPopover"] > button svg {
    display: none !important;
}

/* Flat, round popover trigger buttons */
[data-testid="stPopover"] > button {
    border-radius: 12px !important;
    width: auto !important;
    height: 32px !important;
    min-width: 2.8rem !important;
    padding: 0 0.62rem !important;
    border: 1px solid rgba(15, 23, 42, 0.02) !important;
    display: inline-flex !important;
    justify-content: center !important;
    align-items: center !important;
    background-color: transparent !important;
    color: #64748b !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
    transition:
        background-color 0.16s ease,
        border-color 0.16s ease,
        color 0.16s ease,
        transform 0.16s ease !important;
}
[data-testid="stPopover"] > button:hover {
    background-color: rgba(255, 255, 255, 0.82) !important;
    border-color: rgba(15, 23, 42, 0.08) !important;
    color: #0f172a !important;
    transform: translateY(-1px);
}

/* Conversation buttons in sidebar */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    text-align: left !important;
    font-weight: 500 !important;
    color: #334155 !important;
    padding: 0.7rem 0.8rem !important;
    border-radius: 14px !important;
    width: 100% !important;
    transition:
        background-color 0.18s ease,
        border-color 0.18s ease,
        transform 0.18s ease,
        color 0.18s ease,
        box-shadow 0.18s ease;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background-color: rgba(255, 255, 255, 0.78) !important;
    border-color: rgba(15, 23, 42, 0.06) !important;
    color: #0f172a !important;
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04) !important;
}

/* Sidebar utility buttons look less plain and stay left aligned */
[data-testid="stSidebar"] .st-key-clear_history_btn button,
[data-testid="stSidebar"] .st-key-clear_vector_store_btn button {
    justify-content: flex-start !important;
    text-align: left !important;
    min-height: 3rem !important;
    padding: 0 1rem !important;
    border-radius: 16px !important;
    border: 1px solid rgba(15, 23, 42, 0.08) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.9)) !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05) !important;
    transition:
        background-color 0.16s ease,
        border-color 0.16s ease,
        transform 0.16s ease,
        box-shadow 0.16s ease !important;
}
[data-testid="stSidebar"] .st-key-toggle_recent_sessions button {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    width: 100% !important;
    min-height: 1.5rem !important;
    padding: 0 0 0 0.7rem !important;
    border: none !important;
    background: transparent !important;
    color: var(--sidebar-text-soft) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] .st-key-toggle_recent_sessions {
    margin-top: 1.15rem !important;
    margin-bottom: 0.45rem !important;
}
[data-testid="stSidebar"] .st-key-clear_all_sessions_btn {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
    margin-top: 1.04rem !important;
    margin-bottom: 0.45rem !important;
}
[data-testid="stSidebar"] .st-key-toggle_recent_sessions button > div {
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .st-key-toggle_recent_sessions button p {
    width: 100% !important;
    margin: 0 !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    line-height: 1.2 !important;
    text-align: left !important;
}
[data-testid="stSidebar"] .st-key-toggle_recent_sessions button:hover {
    background: transparent !important;
    color: var(--sidebar-text-soft) !important;
    transform: none !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .st-key-toggle_recent_sessions button:active {
    background: transparent !important;
    transform: none !important;
}
[data-testid="stSidebar"] .st-key-clear_all_sessions_btn button {
    justify-content: center !important;
    text-align: center !important;
    width: 2rem !important;
    height: 1.9rem !important;
    min-height: 1.9rem !important;
    min-width: 2rem !important;
    padding: 0 !important;
    border-radius: 999px !important;
    border: none !important;
    background: transparent !important;
    color: #94a3b8 !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition:
        background-color 0.16s ease,
        border-color 0.16s ease,
        color 0.16s ease,
        transform 0.16s ease !important;
}
[data-testid="stSidebar"] .st-key-clear_all_sessions_btn button p {
    width: 100% !important;
    margin: 0 !important;
    text-align: center !important;
    line-height: 1 !important;
}
[data-testid="stSidebar"] .st-key-clear_all_sessions_btn button:hover {
    background: rgba(239, 68, 68, 0.08) !important;
    color: #b91c1c !important;
    transform: translateY(-1px);
}
[data-testid="stSidebar"] .st-key-clear_all_sessions_btn button:active {
    background: rgba(239, 68, 68, 0.12) !important;
    transform: translateY(0);
}
[data-testid="stSidebar"] .st-key-clear_history_btn button:hover,
[data-testid="stSidebar"] .st-key-clear_vector_store_btn button:hover {
    background: #ffffff !important;
    border-color: rgba(15, 23, 42, 0.12) !important;
    transform: translateY(-1px);
    box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08) !important;
}
[data-testid="stSidebar"] .st-key-clear_history_btn button:active,
[data-testid="stSidebar"] .st-key-clear_vector_store_btn button:active {
    background: #eef2f7 !important;
    border-color: rgba(15, 23, 42, 0.1) !important;
    transform: translateY(0);
    box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05) !important;
}
[data-testid="stSidebar"] .st-key-clear_vector_store_btn button:hover {
    background: rgba(239, 68, 68, 0.08) !important;
    border-color: rgba(239, 68, 68, 0.16) !important;
    color: #b91c1c !important;
    box-shadow: 0 14px 28px rgba(239, 68, 68, 0.08) !important;
}

/* History rows: flat list style like chat sidebar */
[data-testid="stSidebar"] [class*="st-key-session_row_"],
[data-testid="stSidebar"] [class*="st-key-active_session_row_"] {
    margin-bottom: 0.08rem;
}
[data-testid="stSidebar"] [class*="st-key-session_row_"] [data-testid="stHorizontalBlock"],
[data-testid="stSidebar"] [class*="st-key-active_session_row_"] [data-testid="stHorizontalBlock"] {
    align-items: center;
    border-radius: 12px;
    padding: 0.12rem;
    transition:
        background-color 0.16s ease,
        box-shadow 0.16s ease;
}
[data-testid="stSidebar"] [class*="st-key-session_row_"]:hover [data-testid="stHorizontalBlock"],
[data-testid="stSidebar"] [class*="st-key-active_session_row_"]:hover [data-testid="stHorizontalBlock"] {
    background: rgba(255, 255, 255, 0.62) !important;
    box-shadow: 0 10px 18px rgba(15, 23, 42, 0.03);
}
[data-testid="stSidebar"] [class*="st-key-active_session_row_"] [data-testid="stHorizontalBlock"] {
    background: rgba(255, 255, 255, 0.78) !important;
}
[data-testid="stSidebar"] [class*="st-key-open_session_"] button {
    justify-content: flex-start !important;
    text-align: left !important;
    min-height: 2.25rem !important;
    padding: 0.16rem 0.38rem !important;
    border-radius: 10px !important;
    border: none !important;
    background: transparent !important;
    color: #0f172a !important;
    box-shadow: none !important;
    transition:
        background-color 0.16s ease,
        color 0.16s ease,
        transform 0.16s ease !important;
}
[data-testid="stSidebar"] [class*="st-key-open_session_"] button:hover {
    background: transparent !important;
    color: #020617 !important;
    transform: translateX(1px);
}
[data-testid="stSidebar"] [class*="st-key-open_session_"] button:active {
    background: rgba(241, 245, 249, 0.95) !important;
    transform: translateX(0);
}
[data-testid="stSidebar"] [class*="st-key-open_session_"] button p {
    text-align: left !important;
    color: #0f172a !important;
    font-size: 0.95rem !important;
    font-weight: 400 !important;
    line-height: 1.32 !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
[data-testid="stSidebar"] [class*="st-key-active_session_row_"] [class*="st-key-open_session_"] button {
    background: transparent !important;
}
[data-testid="stSidebar"] [class*="st-key-active_session_row_"] [class*="st-key-open_session_"] button p {
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [class*="st-key-delete_session_sidebar_"] {
    opacity: 0;
    transform: translateX(6px);
    pointer-events: none;
    transition:
        opacity 0.16s ease,
        transform 0.16s ease;
}
[data-testid="stSidebar"] [class*="st-key-session_row_"]:hover [class*="st-key-delete_session_sidebar_"],
[data-testid="stSidebar"] [class*="st-key-active_session_row_"]:hover [class*="st-key-delete_session_sidebar_"] {
    opacity: 1;
    transform: translateX(0);
    pointer-events: auto;
}
[data-testid="stSidebar"] [class*="st-key-delete_session_sidebar_"] button {
    width: 2rem !important;
    min-width: 2rem !important;
    min-height: 2rem !important;
    padding: 0 !important;
    border-radius: 999px !important;
    border: none !important;
    background: transparent !important;
    color: #94a3b8 !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] [class*="st-key-delete_session_sidebar_"] button p {
    width: 100% !important;
    margin: 0 !important;
    text-align: center !important;
    line-height: 1 !important;
}
[data-testid="stSidebar"] [class*="st-key-delete_session_sidebar_"] button:hover {
    background: rgba(239, 68, 68, 0.08) !important;
    color: #b91c1c !important;
    transform: none !important;
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


st.markdown(MANDATORY_FLAT_CSS, unsafe_allow_html=True)

hien_thi_thanh_ben()


hien_thi_tieu_de_trang()
xu_ly_tai_lieu_tam()

if not st.session_state["messages"] and not st.session_state["pending_auto_summary"]:
    hien_thi_trang_trong()

hien_thi_tai_lieu_da_tai()

import chat_ui
chat_ui.render_chat_interface()
