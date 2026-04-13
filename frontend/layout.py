from pathlib import Path

import streamlit as st


DUONG_DAN_CSS = Path(__file__).with_name("style.css")


def ap_dung_phong_cach():
    noi_dung_css = DUONG_DAN_CSS.read_text(encoding="utf-8")
    st.markdown(f"<style>{noi_dung_css}</style>", unsafe_allow_html=True)
