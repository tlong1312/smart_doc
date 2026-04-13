import streamlit as st

from main import (
    hien_thi_tai_lieu_da_tai,
    hien_thi_thanh_ben,
    hien_thi_tieu_de_trang,
    hien_thi_trang_trong,
)
from layout import ap_dung_phong_cach
from state import khoi_tao_trang_thai
from upload import hien_thi_hop_tai_len, xu_ly_tai_lieu_tam


st.set_page_config(
    page_title="SmartDoc AI",
    page_icon=":blue_book:",
    layout="wide",
    initial_sidebar_state="expanded",
)


khoi_tao_trang_thai()
ap_dung_phong_cach()
hien_thi_thanh_ben()

if st.session_state["show_upload_modal"]:
    hien_thi_hop_tai_len()

hien_thi_tieu_de_trang()
xu_ly_tai_lieu_tam()

if not st.session_state["messages"] and not st.session_state["pending_auto_summary"]:
    hien_thi_trang_trong()

hien_thi_tai_lieu_da_tai()

import chat_ui

chat_ui.render_chat_interface()
