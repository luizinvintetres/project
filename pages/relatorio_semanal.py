from __future__ import annotations

"""Weekly Summary Report component for Streamlit app.

Displays one row per fund with:
- Nome do fundo
- Saldo de Abertura (balance up to D‑7)
- Entradas (7 d)
- Saídas (7 d)
- Liquidações (7 d)
"""

from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from services import supabase_client as db


@st.cache_data(show_spinner=False)
def _load_joined_transactions() -> pd.DataFrame:
    """Return all transactions enriched with fund information."""
    tx = db.get_transactions()
    if tx.empty:
        return tx

    accounts = db.get_accounts()[["acct_id", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]]

    return (
        tx.merge(accounts, on="acct_id", how="left")
          .merge(funds, on="fund_id", how="left")
    )


def render() -> None:
    st.header("🗓️ Relatório Semanal — Resumo por Fundo")

    tx = _load_joined_transactions()
    if tx.empty:
        st.info("Sem transações para relatório.")
        return

    today = datetime.today().date()
    start = today - timedelta(days=6)

    # ----------------------------
    # DataFrame filtrado (últimos 7 dias)
    # ----------------------------
    weekly = tx[(tx["date"].dt.date >= start) & (tx["date"].dt.date <= today)]
    if weekly.empty:
        st.warning("Nenhuma transação nos últimos 7 dias.")
        return

    # ----------------------------
    # Saldo de abertura até D‑7 (acumulado por fundo)
    # ----------------------------
    df_sorted = (
        tx.sort_values("date")
          .assign(balance=lambda d: d.groupby("fund_id")["amount"].cumsum())
    )
    prev = df_sorted[df_sorted["date"].dt.date < start]
    abertura = prev.groupby("fund_id")["balance"].last().rename("Saldo de Abertura")

    # ----------------------------
    # Métricas dos últimos 7 dias
    # ----------------------------
    entradas = (
        weekly[weekly["amount"] > 0]
              .groupby("fund_id")["amount"].sum()
              .rename("Entradas (7 d)")
    )
    saidas = (
        weekly[weekly["amount"] < 0]
              .groupby("fund_id")["amount"].sum()
              .rename("Saídas (7 d)")
    )
    liquida = (
        weekly[weekly["liquidation"]]
              .groupby("fund_id")["amount"].sum()
              .rename("Liquidações")
    )

    # ----------------------------
    # Resumo final
    # ----------------------------
    summary = pd.concat([abertura, entradas, saidas, liquida], axis=1).fillna(0)

    funds_all = db.get_funds()[["fund_id", "name"]]
    summary = (
        summary
        .merge(funds_all, on="fund_id")
        .rename(columns={"name": "Nome do fundo"})
    )

    summary = (
        summary[[
            "Nome do fundo",
            "Saldo de Abertura",
            "Entradas (7 d)",
            "Saídas (7 d)",
            "Liquidações"
        ]]
        .reset_index(drop=True)
    )

    # ----------------------------
    # Pré‑formatar colunas numéricas como strings com R$
    # ----------------------------
    display_df = summary.copy()
    currency_cols = ["Saldo de Abertura", "Entradas (7 d)", "Saídas (7 d)", "Liquidações"]
    for col in currency_cols:
        display_df[col] = display_df[col].map(lambda x: f"R$ {x:,.2f}")

    st.dataframe(display_df, use_container_width=True)
