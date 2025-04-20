import streamlit as st
from services.supabase_client import supabase, get_transactions, get_saldos

def render_manual_entries_panel(user_email: str) -> None:
        # — Transação Manual —
        st.markdown("**Transação Manual**")
        manual_date = st.date_input("Data", key="manual_tx_date")

        funds = supabase.from_("funds").select("fund_id,name").execute().data or []
        fund_options = {row["name"]: row["fund_id"] for row in funds}
        manual_fund = st.selectbox("Fundo (Transação)", list(fund_options.keys()), key="manual_tx_fund")

        accounts = supabase.from_("accounts").select("acct_id,nickname").execute().data or []
        acct_options = {row["nickname"]: row["acct_id"] for row in accounts}
        manual_acct = st.selectbox("Conta (Transação)", list(acct_options.keys()), key="manual_tx_acct")

        manual_amount = st.text_input("Valor (use vírgula para decimal)", key="manual_tx_amount")
        manual_desc   = st.text_input("Descrição", key="manual_tx_desc")

        if st.button("Adicionar Transação", key="manual_tx_add"):
            val = float(manual_amount.replace(".", "").replace(",", "."))
            supabase.from_("transactions").insert({
                "acct_id":       acct_options[manual_acct],
                "date":          manual_date.isoformat(),
                "description":   manual_desc,
                "amount":        val,
                "liquidation":   False,
                "filename":      None,
                "uploader_email": user_email,
            }).execute()
            # limpa cache para refletir imediatamente
            get_transactions.clear()
            st.success("Transação adicionada manualmente.")

        # — Saldo Manual —
        st.markdown("**Saldo Manual**")
        manual_saldo_date   = st.date_input("Data", key="manual_saldo_date")
        manual_saldo_fund   = st.selectbox("Fundo (Saldo)", list(fund_options.keys()), key="manual_saldo_fund")
        manual_saldo_acct   = st.selectbox("Conta (Saldo)", list(acct_options.keys()), key="manual_saldo_acct")
        manual_saldo_amount = st.text_input("Valor (use vírgula para decimal)", key="manual_saldo_amount")

        if st.button("Adicionar Saldo", key="manual_saldo_add"):
            sbal = float(manual_saldo_amount.replace(".", "").replace(",", "."))
            supabase.from_("saldos").upsert([{
                "acct_id":         acct_options[manual_saldo_acct],
                "date":            manual_saldo_date.isoformat(),
                "opening_balance": sbal,
                "filename":        None,
                "uploader_email":  user_email,
            }]).execute()
            # limpa cache para refletir imediatamente
            get_saldos.clear()
            st.success("Saldo adicionado manualmente.")