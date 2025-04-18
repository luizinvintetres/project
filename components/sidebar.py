# components/sidebar.py
from __future__ import annotations
import streamlit as st

def show_sidebar() -> str:
    st.sidebar.title("app")
    page = st.sidebar.radio(
        label="",
        options=["Dashboard", "Relatório Semanal", "Administração"],
        index=0,
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")
    return page
