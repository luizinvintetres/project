from __future__ import annotations
from datetime import datetime, timedelta, date

import streamlit as st
import pandas as pd

from services.supabase_client import (
    get_transactions,
    get_accounts,
    get_funds,
    get_saldos,
)

# -----------------------------------------------------------------------------
# Helpers with cache
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_joined_transactions() -> pd.DataFrame:
    tx = get_transactions()
    if tx.empty:
        return tx
    acc = get_accounts()[["acct_id", "fund_id"]]
    funds = get_funds()[["fund_id", "name"]]
    return (
        tx
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
    )

@st.cache_data(show_spinner=False)
def _load_joined_saldos() -> pd.DataFrame:
    sal = get_saldos()
    if sal.empty:
        return sal
    acc = get_accounts()[["acct_id", "fund_id"]]
    funds = get_funds()[["fund_id", "name"]]
    return (
        sal
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
    )

# -----------------------------------------------------------------------------
# Week window helper
# -----------------------------------------------------------------------------
def _week_window(offset: int) -> tuple[date, date]:
    today = datetime.today().date()
    monday = today - timedelta(days=today.weekday())
    start = monday + timedelta(weeks=offset)
    end = start + timedelta(days=6)
    return start, end

# -----------------------------------------------------------------------------
# Render
# -----------------------------------------------------------------------------
def render() -> None:
    st.header("🗓️ Relatório Semanal — Resumo por Fundo")
    # Carrega transações juntadas
    tx = _load_joined_transactions()
    if tx.empty:
        st.info("Sem transações para relatório.")
        return

    # Navegação de semanas
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.button("◀", help="Semana anterior", key="prev_week"):
            st.session_state.week_offset -= 1
            return
    start, end = _week_window(st.session_state.week_offset)
    with cols[2]:
        if st.button("▶", disabled=(st.session_state.week_offset == 0), help="Próxima semana", key="next_week"):
            st.session_state.week_offset += 1
            return
    cols[1].markdown(
        f"<div style='text-align:center; font-weight:600;'>"
        f"{start.strftime('%d/%m/%Y')} ➜ {end.strftime('%d/%m/%Y')}"
        f"</div>", unsafe_allow_html=True
    )

    # Filtra transações da semana
    df = tx.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    weekly = df[(df["date"] >= start) & (df["date"] <= end)]
    if weekly.empty:
        st.warning("Nenhuma transação nesse intervalo.")
        return

    # Carrega saldos juntados
    sal_df = _load_joined_saldos()
    sal_df = sal_df.copy()
    sal_df["date"] = pd.to_datetime(sal_df["date"]).dt.date
    
    # Calcula saldo de abertura
    abertura = (
        sal_df[sal_df["date"] == start]
        .groupby("fund_id")["opening_balance"]
        .sum()
        .rename("Saldo de Abertura")
    )

    # Métricas da semana
    entradas = (
        weekly[weekly["amount"] > 0]
        .groupby("fund_id")["amount"].sum().rename("Entradas (7 d)")
    )
    saidas = (
        weekly[weekly["amount"] < 0]
        .groupby("fund_id")["amount"].sum().rename("Saídas (7 d)")
    )
    liquida = (
        weekly[weekly["liquidation"]]
        .groupby("fund_id")["amount"].sum().rename("Liquidações")
    )

    # Consolida resumo
    summary = pd.concat([abertura, entradas, saidas, liquida], axis=1).fillna(0)
    funds_all = get_funds()[["fund_id", "name"]]
    summary = (
        summary.reset_index()
        .merge(funds_all, on="fund_id")
        .rename(columns={"name": "Nome do fundo"})
        [["Nome do fundo", "Saldo de Abertura", "Entradas (7 d)", "Saídas (7 d)", "Liquidações"]]
    )

    # Formata valores
    for col in ["Saldo de Abertura", "Entradas (7 d)", "Saídas (7 d)", "Liquidações"]:
        summary[col] = summary[col].map(lambda x: f"R$ {x:,.2f}")

    st.dataframe(summary, use_container_width=True)
