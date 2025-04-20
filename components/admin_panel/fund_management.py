import streamlit as st
from services.supabase_client import supabase

def render_fund_management(user_email: str) -> None:
    st.subheader("➕ Novo Fundo")
    fund_name = st.text_input("Nome do Fundo", key="admin_fund_name")
    fund_cnpj = st.text_input("CNPJ", key="admin_fund_cnpj")
    fund_admin = st.text_input("Administrador", key="admin_fund_admin")
    if st.button("Adicionar Fundo", key="admin_add_fund") and fund_name:
        supabase.from_("funds").insert(
            {"name": fund_name, "cnpj": fund_cnpj, "administrator": fund_admin}
        ).execute()
        st.success("Fundo adicionado!")