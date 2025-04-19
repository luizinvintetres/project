"""
Sidebar com:
1. Cadastro de fundos/contas
2. Upload de extratos
3. Navegação entre páginas
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from services import supabase_client as db
from utils.transforms import clean_statement

# ----------------------------------------------------------------------------- 
# Formulário: Fundo
# -----------------------------------------------------------------------------
def _form_fund() -> None:
    st.sidebar.subheader("➕ Novo Fundo")
    name  = st.sidebar.text_input("Nome do Fundo", key="fund_name")
    cnpj  = st.sidebar.text_input("CNPJ",           key="fund_cnpj")
    admin = st.sidebar.text_input("Administrador", key="fund_admin")
    if st.sidebar.button("Adicionar Fundo", key="add_fund") and name:
        db.insert_fund({"name": name, "cnpj": cnpj, "administrator": admin})
        st.sidebar.success("Fundo adicionado!")

# ----------------------------------------------------------------------------- 
# Formulário: Conta
# -----------------------------------------------------------------------------
def _form_account() -> None:
    st.sidebar.subheader("➕ Nova Conta")
    funds = db.get_funds()
    if funds.empty:
        st.sidebar.info("Cadastre um fundo primeiro.")
        return

    fund_dict = dict(zip(funds["name"], funds["fund_id"]))
    sel_name  = st.sidebar.selectbox("Fundo", fund_dict.keys(), key="acct_fund")
    bank   = st.sidebar.text_input("Banco",    key="acct_bank")
    agency = st.sidebar.text_input("Agência",  key="acct_agency")
    number = st.sidebar.text_input("Número",   key="acct_number")
    nick   = st.sidebar.text_input("Apelido",  key="acct_nick")

    if st.sidebar.button("Adicionar Conta", key="add_acct") and bank:
        db.insert_account({
            "fund_id": fund_dict[sel_name],
            "bank": bank, "agency": agency,
            "number": number,
            "nickname": nick or f"{bank}-{number}"
        })
        st.sidebar.success("Conta adicionada!")

# ----------------------------------------------------------------------------- 
# Formulário: Upload de Extrato
# -----------------------------------------------------------------------------
def _form_upload() -> None:
    st.sidebar.subheader("⬆️ Upload de Extrato")

    accounts = db.get_accounts()
    if accounts.empty:
        st.sidebar.info("Cadastre contas para habilitar uploads.")
        return

    acct_dict = dict(zip(accounts["nickname"], accounts["acct_id"]))
    sel_nick  = st.sidebar.selectbox("Conta", acct_dict.keys(), key="upl_acct")

    file = st.sidebar.file_uploader("CSV ou XLSX", type=["csv", "xlsx", "xls"], key="upl_file")
    send = st.sidebar.button("Enviar agora", key="upl_send")

    if send and file:
        df_raw = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        df = clean_statement(df_raw)

        acct_id = acct_dict[sel_nick]
        imported = db.get_imported_dates(acct_id)

        # Filtra fora os dias já importados
        mask_new = ~df["date"].dt.date.isin(imported)
        df_new   = df[mask_new]

        if df_new.empty:
            st.sidebar.warning("Nenhuma linha nova: todas as datas já estavam no banco.")
            return

        # Insere transações novas
        for _, row in df_new.iterrows():
            db.insert_transaction({
                "acct_id": acct_id,
                "date": row["date"].strftime("%Y-%m-%d"),
                "description": row["description"],
                "amount": float(row["amount"]),
                "liquidation": bool(row["liquidation"])
            })

        # Marca essas datas como importadas
        db.add_import_log(acct_id, set(df_new["date"].dt.date))

        st.sidebar.success(f"{len(df_new)} transações inseridas "
                           f"({len(df) - len(df_new)} ignoradas).")

# ----------------------------------------------------------------------------- 
# Função que compõe a Sidebar inteira e devolve a página selecionada
# -----------------------------------------------------------------------------
from services.supabase_client import supabase

def show_sidebar() -> str:
    with st.sidebar:
        # 1) Logout / usuário
        if "user" in st.session_state:
            st.write(f"👤 {st.session_state.user.email}")
            if st.button("Sair", key="logout_sidebar"):
                supabase.auth.sign_out()
                del st.session_state.user
                st.rerun()

        # 2) Logo e menu
        st.image("static/plgn_logo.png", width=240)
        st.markdown("## Navegação")
        page = st.radio("", ["Dashboard", "Relatório Semanal", "Administração"], key="menu_radio")

        # 3) Formulários só para admin
        if page == "Administração":
            _form_fund()
            _form_account()
            _form_upload()

    return page
