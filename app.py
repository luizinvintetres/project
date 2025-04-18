"""
Ponto de entrada da aplicação Streamlit
---------------------------------------

– Navegação na sidebar
– Cada página é um módulo separado
– Administração agora é uma tela própria (não um expander)
"""
from __future__ import annotations

import streamlit as st
from components.sidebar import show_sidebar
from pages import dashboard, relatorio_semanal
from components import admin_panel

# ----------------------------------------------------------------------------- #
# Configuração geral do app
# ----------------------------------------------------------------------------- #
st.set_page_config(
    page_title="PLGN Tesouraria",
    layout="wide",
    page_icon="💼",
)
st.title("🏦 Bank Statement Manager")

# ----------------------------------------------------------------------------- #
# Sidebar e roteamento
# ----------------------------------------------------------------------------- #
page = show_sidebar()  # retorna: "Dashboard", "Relatório Semanal", "Administração"

# ----------------------------------------------------------------------------- #
# Router de páginas
# ----------------------------------------------------------------------------- #
if page == "Dashboard":
    dashboard.render()

elif page == "Relatório Semanal":
    relatorio_semanal.render()

elif page == "Administração":
    # Exibe o painel completo de cadastro e upload
    st.subheader("⚙️ Painel de Administração")
    st.markdown("Gerencie fundos, contas e importe extratos.")
    admin_panel.render()

else:
    st.warning("Página não encontrada.")
