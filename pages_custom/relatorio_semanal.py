# pages_custom/relatorio_semanal.py
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


@st.cache_data(show_spinner=False)
def _load_joined_transactions() -> pd.DataFrame:
    tx = get_transactions()
    if tx.empty:
        return tx
    acc = get_accounts()[["acct_id", "fund_id"]]
    funds = get_funds()[["fund_id", "name"]]
    return (
        tx.merge(acc, on="acct_id", how="left")
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
        sal.merge(acc, on="acct_id", how="left")
           .merge(funds, on="fund_id", how="left")
    )


def _week_window(offset: int) -> tuple[date, date]:
    """Retorna a segunda e o domingo da semana (offset)"""
    today = datetime.today().date()
    monday = today - timedelta(days=today.weekday())
    start = monday + timedelta(weeks=offset)
    end = start + timedelta(days=6)
    return start, end


def render() -> None:
    st.header("🗓️ Relatório Semanal — Resumo por Fundo")
    user_email = st.session_state.user.email

    tx = _load_joined_transactions()
    # filtra pelo usuário
    if "uploader_email" in tx.columns:
        tx = tx[tx["uploader_email"] == user_email]
    if tx.empty:
        st.info("Sem transações para relatório.")
        return

    # controle de semana via session_state
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.button("◀", help="Semana anterior"):
            st.session_state.week_offset -= 1
    start, end = _week_window(st.session_state.week_offset)
    with cols[2]:
        disable_next = st.session_state.week_offset == 0
        if st.button("▶", disabled=disable_next, help="Próxima semana"):
            st.session_state.week_offset += 1
    cols[1].markdown(
        f"<div style='text-align:center; font-weight:600;'>"
        f"{start.strftime('%d/%m/%Y')} ➜ {end.strftime('%d/%m/%Y')}"  
        f"</div>", unsafe_allow_html=True
    )

    # filtra transações da semana
    tx = tx.copy()
    tx["date"] = pd.to_datetime(tx["date"]).dt.date
    weekly = tx[(tx["date"] >= start) & (tx["date"] <= end)]
    if weekly.empty:
        st.warning("Nenhuma transação nesse intervalo.")
        return

    # carrega saldos e filtra usuário e período
    sal_df = _load_joined_saldos()
    if "uploader_email" in sal_df.columns:
        sal_df = sal_df[sal_df["uploader_email"] == user_email]
    sal_df = sal_df.copy()
    sal_df["date"] = pd.to_datetime(sal_df["date"]).dt.date

    # abertura via saldos na data de início
    abertura = (
        sal_df[sal_df["date"] == start]
        .groupby("fund_id")["opening_balance"]
        .sum()
        .rename("Saldo de Abertura")
    )

    # métricas semanais
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

    # concatena resumo
    summary = pd.concat([abertura, entradas, saidas, liquida], axis=1).fillna(0)
    funds_all = get_funds()[["fund_id", "name"]]
    summary = (
        summary
        .reset_index()
        .merge(funds_all, on="fund_id")
        .rename(columns={
            "name": "Nome do fundo"
        })
        [["Nome do fundo", "Saldo de Abertura", "Entradas (7 d)", "Saídas (7 d)", "Liquidações"]]
    )

    # formata valores
    for col in ["Saldo de Abertura", "Entradas (7 d)", "Saídas (7 d)", "Liquidações"]:
        summary[col] = summary[col].map(lambda x: f"R$ {x:,.2f}")

    st.dataframe(summary, use_container_width=True)
