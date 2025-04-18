"""
Ponto de entrada da aplicação Streamlit
---------------------------------------

– Navegação na sidebar
– Cada página é um módulo separado
– Administração agora é uma tela própria (não um expander)
"""
import streamlit as st

# -----------------------------------------------------------------------------
# Configuração geral do app (deve ser o primeiro comando Streamlit)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PLGN Tesouraria",
    layout="wide",
    page_icon="💼",
)

st.title("🏦 PLGN Tesouraria")

# -----------------------------------------------------------------------------
# Imports de módulos que utilizam comandos Streamlit devem vir após set_page_config
# -----------------------------------------------------------------------------
from components.sidebar import show_sidebar
from pages_custom import dashboard, relatorio_semanal
from components import admin_panel

# -----------------------------------------------------------------------------
# Navegação via sidebar
# -----------------------------------------------------------------------------
page = show_sidebar()  # retorna: "Dashboard", "Relatório Semanal", "Administração"

# -----------------------------------------------------------------------------
# Router de páginas
# -----------------------------------------------------------------------------
if page == "Dashboard":
    dashboard.render()
elif page == "Relatório Semanal":
    relatorio_semanal.render()
elif page == "Administração":
    st.subheader("⚙️ Painel de Administração")
    st.markdown("Gerencie fundos, contas e importe extratos.")
    admin_panel.render()
else:
    st.warning("Página não encontrada.")
