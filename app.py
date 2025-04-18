"""
Ponto de entrada da aplicação Streamlit
---------------------------------------

– Navegação na sidebar (Dashboard | Relatório Semanal)
– Painel ⚙️ Administração exibido dentro da página
  (por enquanto visível a todos; depois basta
   limitar pelo campo `is_admin` do usuário em sessão)
"""
from __future__ import annotations

import streamlit as st
from components.sidebar import show_sidebar
from components import admin_panel
from pages import dashboard, relatorio_semanal

# ----------------------------------------------------------------------------- #
# Configuração geral do app
# ----------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Bank Statement Manager",
    layout="wide",
    page_icon="💼",
)
st.title("🏦 Bank Statement Manager")

# ----------------------------------------------------------------------------- #
# Sidebar e seleção de página
# ----------------------------------------------------------------------------- #
page = show_sidebar()   # retorna "Dashboard" ou "Relatório Semanal"

# ----------------------------------------------------------------------------- #
# Painel de administração (visível enquanto não há autenticação)
# ----------------------------------------------------------------------------- #
# Quando o sistema de login estiver pronto, troque a condição para:
# if st.session_state.get("user", {}).get("is_admin", False):
with st.expander("⚙️ Administração", expanded=False):
    admin_panel.render()

# ----------------------------------------------------------------------------- #
# Roteamento de páginas
# ----------------------------------------------------------------------------- #
if page == "Dashboard":
    dashboard.render()
elif page == "Relatório Semanal":
    relatorio_semanal.render()
else:
    st.write("Página não encontrada.")
