# components/sidebar.py
from __future__ import annotations
import streamlit as st

def show_sidebar() -> str:
    """Desenha apenas a navegação e devolve a página escolhida."""
    st.sidebar.title("app")                    # opcional: nome ou logo
    page = st.sidebar.radio(
        label="",
        options=["Dashboard", "Relatório Semanal"],
        index=0,                               # “Dashboard” default
        label_visibility="collapsed",          # esconde o rótulo
    )
    st.sidebar.markdown("---")                 # linha divisória estética
    return page
