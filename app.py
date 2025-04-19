import streamlit as st
from services.supabase_client import supabase
from components.sidebar import show_sidebar
from pages_custom import dashboard, relatorio_semanal
from components import admin_panel

# -----------------------------------------------------------------------------
# 1) CONFIGURAÇÃO INICIAL (sempre antes de qualquer st.*)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PLGN Tesouraria",
    layout="wide",
    page_icon="💼",
)

# -----------------------------------------------------------------------------
# 2) TELA DE LOGIN
# -----------------------------------------------------------------------------
def login():
    st.title("🔒 Login")
    with st.form("login_form"):
        email = st.text_input("E‑mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            try:
                # Autenticação via Supabase Auth V2
                resp = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                # Em caso de sucesso, resp.user contém o usuário
                user = getattr(resp, "user", None)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Falha ao autenticar, usuário não retornado.")
            except Exception as err:
                # Captura e mostra erros (ex: senha inválida, usuário não existe)
                st.error(f"Erro ao autenticar: {err}")

# Se não estiver logado, mostra o login e interrompe o restante
if "user" not in st.session_state:
    login()
    st.stop()

# -----------------------------------------------------------------------------
# 3) LOGOUT NA SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.write(f"👤 {st.session_state.user.email}")
# botão de logout com key única para evitar duplicação
if st.sidebar.button("Sair", key="logout_app"):
    supabase.auth.sign_out()
    del st.session_state.user
    st.rerun()

# -----------------------------------------------------------------------------
# 4) RESTANTE DO APP
# -----------------------------------------------------------------------------
st.title(" PLGN Tesouraria")

page = show_sidebar()
if page == "Dashboard":
    dashboard.render()
elif page == "Relatório Semanal":
    relatorio_semanal.render()
elif page == "Administração":
    st.subheader("⚙️ Painel de Administração")
    admin_panel.render()
else:
    st.warning("Página não encontrada.")
