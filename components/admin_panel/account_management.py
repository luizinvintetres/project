import streamlit as st
from services.supabase_client import supabase

def render_account_management(user_email: str) -> None:
    st.subheader("➕ Nova Conta")
    funds = supabase.from_("funds").select("fund_id,name").execute().data or []
    if not funds:
        st.info("Cadastre um fundo antes de criar contas.")
        return
    options = {row['name']: row['fund_id'] for row in funds}
    sel = st.selectbox("Fundo", list(options.keys()), key="admin_sel_fund")
    bank = st.text_input("Banco", key="admin_bank")
    agency = st.text_input("Agência", key="admin_agency")
    number = st.text_input("Número da Conta", key="admin_number")
    nickname = st.text_input("Apelido", key="admin_nickname")
    if st.button("Adicionar Conta", key="admin_add_acct") and bank:
        supabase.from_("accounts").insert(
            {
                "fund_id": options[sel],
                "bank": bank,
                "agency": agency,
                "number": number,
                "nickname": nickname or f"{bank}-{number}",
            }
        ).execute()
        st.success("Conta adicionada!")