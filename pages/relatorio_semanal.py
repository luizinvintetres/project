"""
Relatório automático dos últimos 7 dias
"""
from __future__ import annotations

from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from services import supabase_client as db

def render() -> None:
    st.header("🗓️ Relatório Semanal")
    tx = db.get_transactions()
    if tx.empty:
        st.info("Sem transações para relatório.")
        return

    today = datetime.today().date()
    start = today - timedelta(days=6)
    weekly = tx[(tx["date"].dt.date >= start) & (tx["date"].dt.date <= today)]
    if weekly.empty:
        st.warning("Nenhuma transação nos últimos 7 dias.")
        return

    # Saldo de abertura
    df_sorted = tx.sort_values("date").assign(balance=lambda d: d["amount"].cumsum())
    prev = df_sorted[df_sorted["date"].dt.date < start]
    abertura = prev["balance"].iloc[-1] if not prev.empty else 0.0

    entradas = weekly.loc[weekly["amount"] > 0, "amount"].sum()
    saidas   = weekly.loc[weekly["amount"] < 0, "amount"].sum()
    liquida  = weekly.loc[weekly["liquidation"], "amount"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo de Abertura", f"R$ {abertura:,.2f}")
    c2.metric("Entradas (7 d)",    f"R$ {entradas:,.2f}")
    c3.metric("Saídas (7 d)",      f"R$ {saidas:,.2f}")
    c4.metric("Liquidações",       f"R$ {liquida:,.2f}")

    # Enriquecimento p/ tabela
    acc  = db.get_accounts()[["acct_id", "nickname", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]]
    tbl = (
        weekly
        .merge(acc,  on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    st.dataframe(tbl[["date", "fund", "account", "description", "amount", "liquidation"]])
