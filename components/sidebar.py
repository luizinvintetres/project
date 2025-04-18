# components/sidebar.py
import streamlit as st

def show_sidebar() -> str:
    """Sidebar enxuta com menu de navegação."""
    page = st.sidebar.radio(
        label="Navegação",
        options=["Dashboard", "Relatório Semanal", "Administração"],
        index=0,
    )
    return page
