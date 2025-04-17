"""
Ponto de entrada da aplicação Streamlit
"""
import streamlit as st
from components.sidebar import show_sidebar
from pages import dashboard, relatorio_semanal

st.set_page_config(page_title="Bank Statement Manager", layout="wide", page_icon="💼")
st.title("🏦 Bank Statement Manager")

page = show_sidebar()

if page == "Dashboard":
    dashboard.render()
else:
    relatorio_semanal.render()
