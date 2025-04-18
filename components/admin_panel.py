# components/admin_panel.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import importlib
from services import supabase_client as db

def render() -> None:
    st.subheader("➕ Novo Fundo")
    fund_name = st.text_input("Nome do Fundo", key="fund_name")
    fund_cnpj = st.text_input("CNPJ", key="fund_cnpj")
    fund_admin = st.text_input("Administrador", key="fund_admin")
    if st.button("Adicionar Fundo", key="add_fund") and fund_name:
        db.insert_fund(fund_name, fund_cnpj, fund_admin)
        st.success("Fundo adicionado!")

    st.divider()

    st.subheader("➕ Nova Conta")
    funds = db.get_funds()
    if funds.empty:
        st.info("Cadastre um fundo antes de criar contas.")
    else:
        fund_options = {row['name']: row['fund_id'] for _, row in funds.iterrows()}
        sel_fund_name = st.selectbox("Fundo", list(fund_options.keys()))
        bank = st.text_input("Banco", key="bank")
        agency = st.text_input("Agência", key="agency")
        number = st.text_input("Número da Conta", key="number")
        nickname = st.text_input("Apelido", key="nickname")
        if st.button("Adicionar Conta", key="add_acct") and bank:
            db.add_account(
                fund_id=fund_options[sel_fund_name],
                bank=bank, agency=agency, number=number, nickname=nickname
            )
            st.success("Conta adicionada!")

    st.divider()

    st.subheader("📥 Upload de Extrato")
    accounts = db.get_accounts()
    if accounts.empty:
        st.info("Cadastre contas para habilitar uploads.")
    else:
        acct_opts = {row['nickname']: row['acct_id'] for _, row in accounts.iterrows()}
        sel_acct_nick = st.selectbox("Conta", list(acct_opts.keys()))
        
        # NOVO: seleção do tipo de extrato
        model_options = {
            "Bradesco": "bradesco",
            "Itaú": "itau",
            "Genérico CSV": "generic_csv"
        }
        sel_model = st.selectbox("Modelo de Extrato", list(model_options.keys()))
        file = st.file_uploader("Extrato", type=["csv", "xlsx", "xls"])

        if file:
            try:
                module_name = f"components.modelos_extratos.{model_options[sel_model]}"
                parser = importlib.import_module(module_name)
                df_new = parser.read(file)
                acct_id = acct_opts[sel_acct_nick]
                for _, row in df_new.iterrows():
                    db.add_transaction(
                        acct_id=acct_id,
                        date=row["date"],
                        description=row["description"],
                        amount=row["amount"],
                        liquidation=row["liquidation"]
                    )
                st.success(f"{len(df_new)} transações enviadas com sucesso!")
            except Exception as e:
                st.error(f"Erro ao importar extrato: {e}")
