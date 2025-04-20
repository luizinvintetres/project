from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from datetime import date, datetime, timedelta

from services.supabase_client import (
    get_funds,
    get_accounts,
    get_transactions,
    get_saldos,
)

# ---------------------------------
# Helper: Formatação BR
# ---------------------------------
def format_currency_br(value: float) -> str:
    s = f"{value:,.2f}"
    # troca separadores: ',' -> temporário, '.' -> ',', temporário -> '.'
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------------------------
# Cached data loaders
# ---------------------------------
@st.cache_data(ttl=20, show_spinner=False)
def _load_transactions() -> pd.DataFrame:
    return get_transactions()

@st.cache_data(ttl=20, show_spinner=False)
def _load_accounts() -> pd.DataFrame:
    return get_accounts()[["acct_id", "nickname", "fund_id"]]

@st.cache_data(ttl=20, show_spinner=False)
def _load_funds() -> pd.DataFrame:
    return get_funds()[["fund_id", "name"]]

@st.cache_data(ttl=20, show_spinner=False)
def _load_saldos() -> pd.DataFrame:
    sal = get_saldos()
    if sal is not None and not sal.empty:
        sal["date"] = pd.to_datetime(sal["date"]).dt.date
    return sal

# ---------------------------------
# Métricas principais
# ---------------------------------
def _metrics(df: pd.DataFrame, start_date: date, saldos_df: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    total_in = df.loc[df["amount"] > 0, "amount"].sum()
    total_out = df.loc[df["amount"] < 0, "amount"].sum()
    net = total_in + total_out
    col1.metric("Entradas", format_currency_br(total_in))
    col2.metric("Saídas", format_currency_br(abs(total_out)))
    col3.metric("Saldo Líquido", format_currency_br(net))

    opening = saldos_df.loc[saldos_df["date"] == start_date, "opening_balance"].sum()
    col4.metric("Saldo Abertura", format_currency_br(opening))

# ---------------------------------
# Renderização
# ---------------------------------
def render() -> None:
    st.header("📊 Dashboard Geral")

    # Carrega dados
    tx = _load_transactions()
    acc = _load_accounts()
    funds = _load_funds()
    sal = _load_saldos()

    if tx.empty:
        st.info("Nenhuma transação disponível.")
        return
    if sal is None or sal.empty:
        st.warning("Tabela de saldos não disponível.")
        return

    # Monta DataFrame
    df = (
        tx
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )
    sal_df = (
        sal
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    # Filtros de fundo e conta
    sel_fund = st.multiselect("Fundos", sorted(df["fund"].dropna().unique()))
    if sel_fund:
        df = df[df["fund"].isin(sel_fund)]
        sal_df = sal_df[sal_df["fund"].isin(sel_fund)]

    sel_acct = st.multiselect("Contas", sorted(df["account"].dropna().unique()))
    if sel_acct:
        df = df[df["account"].isin(sel_acct)]
        sal_df = sal_df[sal_df["account"].isin(sel_acct)]

    if df.empty:
        st.warning("Nenhuma transação encontrada para os filtros aplicados.")
        return

    # Ajusta datas
    df["date"] = pd.to_datetime(df["date"]).dt.date
    min_date, max_date = df["date"].min(), df["date"].max()

    # Menu de período
    period = st.selectbox(
        "Período de Visualização",
        [
            "Últimos 7 dias",
            "Últimos 15 dias",
            "Últimos 30 dias",
            "Últimos 60 dias",
            "Definir intervalo",
        ],
        index=2,
    )

    if period != "Definir intervalo":
        dias = int(period.split()[1])
        end = date.today()
        start = end - timedelta(days=dias)
        # limita ao intervalo disponível
        start = max(start, min_date)
        end = min(end, max_date)
    else:
        start, end = st.date_input(
            "Selecione intervalo",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(start, tuple):
            start, end = start

    # Filtra por data
    mask = (df["date"] >= start) & (df["date"] <= end)
    df = df.loc[mask]
    sal_df = sal_df.loc[(sal_df["date"] >= start) & (sal_df["date"] <= end)]

    if df.empty:
        st.warning("Nenhuma transação no intervalo selecionado.")
        return

    # Métricas
    _metrics(df, start, sal_df)

    # Prepara dados para gráfico
    df["type"] = df["amount"].apply(lambda x: "Entrada" if x > 0 else "Saída")
    df_daily = (
        df.groupby(["date", "type"])["amount"]
        .sum()
        .reset_index()
        .sort_values("date")
    )

    if df_daily.empty:
        st.warning("Não há dados suficientes para gerar o gráfico.")
    else:
        chart = (
            alt.Chart(df_daily)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="Data"),
                y=alt.Y("amount:Q", title="Valor"),
                color=alt.Color("type:N", title="Tipo"),
                tooltip=[
                    alt.Tooltip("date:T", title="Data"),
                    alt.Tooltip("amount:Q", title="Valor", format=",.2f"),
                    alt.Tooltip("type:N", title="Tipo"),
                ],
            )
            .properties(height=300)
            .configure_axisX(labelAngle=-45)
        )
        st.altair_chart(chart, use_container_width=True)

    # Exibição de tabelas com formatação BR
    st.subheader("Saldos de Abertura")
    df_saldo = sal_df[["date", "fund", "account", "opening_balance"]].copy()
    df_saldo["opening_balance"] = df_saldo["opening_balance"].apply(format_currency_br)
    st.dataframe(df_saldo, use_container_width=True)

    st.subheader("Transações")
    df_tx = df[["date", "fund", "account", "description", "amount"]].copy()
    df_tx["amount"] = df_tx["amount"].apply(format_currency_br)
    st.dataframe(df_tx, use_container_width=True)
