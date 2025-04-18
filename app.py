"""
Ponto de entrada da aplicação Streamlit
---------------------------------------

– Navegação na sidebar
– Cada página é um módulo separado
– Administração agora é uma tela própria (não um expander)
"""
import streamlit as st
from components.sidebar import show_sidebar
from pages import dashboard, relatorio_semanal
from components import admin_panel

#<<<<<<< HEAD
# ----------------------------------------------------------------------------- #
# Configuração geral do app
# ----------------------------------------------------------------------------- #
st.set_page_config(
    page_title="PLGN Tesouraria",
    layout="wide",
    page_icon="💼",
)
st.title("🏦 PLGN Tesouraria")

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
=======
st.set_page_config(page_title="Bank Statement Manager", layout="wide", page_icon="💼")
st.title("🏦 Bank Statement Manager")

page = show_sidebar()

if page == "Dashboard":
    dashboard.render()
else:
    relatorio_semanal.render()

