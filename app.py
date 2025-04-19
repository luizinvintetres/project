import streamlit as st
from services.supabase_client import supabase
from components.sidebar import show_sidebar
from pages_custom import dashboard, relatorio_semanal
from components import admin_panel

# -----------------------------------------------------------------------------
# 1) CONFIGURAÇÃO INICIAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PLGN Tesouraria",
    layout="wide",
    page_icon="💼",
)

# -----------------------------------------------------------------------------
# 2) TELA DE LOGIN COM ROLE
# -----------------------------------------------------------------------------
def login():
    st.title("🔒 Login")
    with st.form("login_form"):
        email = st.text_input("E‑mail")
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            try:
                # Autenticação Supabase Auth V2
                resp = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                user = getattr(resp, "user", None)
                if user:
                    # Busca o role na tabela profiles
                    prof = (
                        supabase
                        .from_("profiles")
                        .select("role")
                        .eq("id", user.id)
                        .single()
                        .execute()
                    )
                    role = None
                    if hasattr(prof, "data") and prof.data:
                        role = prof.data.get("role")
                    # Default para 'user' se não houver role
                    st.session_state.user = user
                    st.session_state.role = role or "user"
                    st.rerun()
                else:
                    st.error("Falha ao autenticar, usuário não retornado.")
            except Exception as err:
                st.error(f"Erro ao autenticar: {err}")

# Somente login (com role) antes de prosseguir
if "user" not in st.session_state:
    login()
    st.stop()

# -----------------------------------------------------------------------------
# 3) LOGOUT E EXIBIÇÃO DE E‑MAIL/ROLE
# -----------------------------------------------------------------------------
st.sidebar.write(f"👤 {st.session_state.user.email} ({st.session_state.role})")
if st.sidebar.button("Sair", key="logout_app"):
    supabase.auth.sign_out()
    del st.session_state.user
    del st.session_state.role
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
    admin_panel.render()
else:
    st.warning("Página não encontrada.")
