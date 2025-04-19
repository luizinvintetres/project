from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from datetime import date
from services.supabase_client import (
    get_funds,
    get_accounts,
    get_transactions,
    get_saldos,
)


def _metrics(df: pd.DataFrame, start_date: date, saldos_df: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    total_in = df.loc[df["amount"] > 0, "amount"].sum()
    total_out = df.loc[df["amount"] < 0, "amount"].sum()
    net = total_in + total_out
    col1.metric("Entradas", f"R$ {total_in:,.2f}")
    col2.metric("Saídas", f"R$ {abs(total_out):,.2f}")
    col3.metric("Saldo Líquido", f"R$ {net:,.2f}")
    opening = saldos_df.loc[saldos_df["date"] == start_date, "opening_balance"].sum()
    col4.metric("Saldo Abertura", f"R$ {opening:,.2f}")


def render() -> None:
    st.header("🗓️ Relatório Semanal — Resumo por Fundo")

    # Botão de atualização manual para invalidar cache e recarregar dados
    if st.button("🔄 Atualizar Dados", key="refresh_weekly"):
        _load_joined_transactions.clear()
        _load_joined_saldos.clear()
        # limpar caches subjacentes
        get_transactions.clear()
        get_accounts.clear()
        get_funds.clear()
        get_saldos.clear()
        return

    # Carrega transações e checa
    tx = _load_joined_transactions()
    if tx.empty:
        st.info("Sem transações para relatório.")
        return

    # Controle de navegação semanal
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.button("◀", help="Semana anterior", key="prev_week"):
            st.session_state.week_offset -= 1
            return  # força recarregar com novo offset
    start, end = _week_window(st.session_state.week_offset)
    with cols[2]:
        if st.button("▶", disabled=(st.session_state.week_offset == 0), help="Próxima semana", key="next_week"):
            st.session_state.week_offset += 1
            return  # força recarregar com novo offset
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

    # Carrega saldos e filtra período
    sal_df = _load_joined_saldos()
    sal_df = sal_df.copy()
    sal_df["date"] = pd.to_datetime(sal_df["date"]).dt.date
    sal_period = sal_df[(sal_df["date"] >= start) & (sal_df["date"] <= end)]

    # Calcula saldo de abertura pelo saldo informado na tabela
    abertura = (
        sal_df[sal_df["date"] == start]
        .groupby("fund_id")["opening_balance"]
        .sum()
        .rename("Saldo de Abertura")
    )

    # Métricas semanais por fundo
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
