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

# -----------------------------------------------------------------------------
# Cached data loaders
# -----------------------------------------------------------------------------
@st.cache_data(ttl= 20,show_spinner=False)
def _load_transactions() -> pd.DataFrame:
    return get_transactions()

@st.cache_data(ttl= 20,show_spinner=False)
def _load_accounts() -> pd.DataFrame:
    return get_accounts()[["acct_id", "nickname", "fund_id"]]

@st.cache_data(ttl= 20,show_spinner=False)
def _load_funds() -> pd.DataFrame:
    return get_funds()[["fund_id", "name"]]

@st.cache_data(ttl= 20,show_spinner=False)
def _load_saldos() -> pd.DataFrame:
    sal = get_saldos()
    if sal is not None and not sal.empty:
        sal["date"] = pd.to_datetime(sal["date"]).dt.date
    return sal


# -----------------------------------------------------------------------------
# Métricas principais
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Renderização
# -----------------------------------------------------------------------------
def render() -> None:
    st.header("📊 Dashboard Geral")

    # Carrega dados com cache
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

    # Monta DataFrame principal
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

    # Filtro de período
    df["date"] = pd.to_datetime(df["date"])
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    start, end = st.slider(
        "Período de Visualização",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )
    df = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)]
    sal_df = sal_df[(sal_df["date"] >= start) & (sal_df["date"] <= end)]

    if df.empty:
        st.warning("Nenhuma transação no intervalo selecionado.")
        return

    # Métricas
    _metrics(df, start, sal_df)

    # Gráfico de barras por tipo
    df["type"] = df["amount"].apply(lambda x: "Entrada" if x > 0 else "Saída")
    df_daily = (
        df.groupby(["date", "type"])["amount"]
        .sum()
        .reset_index()
        .sort_values("date")
    )
    chart = (
        alt.Chart(df_daily)
        .mark_bar()
        .encode(
            x=alt.X("date:T", title="Data"),
            y=alt.Y("amount:Q", title="Valor"),
            color=alt.Color(
                "type:N",
                scale=alt.Scale(domain=["Entrada", "Saída"], range=["steelblue", "crimson"]),
                title="Tipo"
            ),
            tooltip=["date:T", "amount:Q", "type:N"]
        )
        .properties(height=300)
        .configure_axisX(labelAngle=-45)
    )
    st.altair_chart(chart, use_container_width=True)

    # Saldos de Abertura
    st.subheader("Saldos de Abertura")
    st.dataframe(
        sal_df[["date", "fund", "account", "opening_balance"]],
        use_container_width=True
    )

    # Transações
    st.subheader("Transações")
    st.dataframe(
        df[["date", "fund", "account", "description", "amount"]],
        use_container_width=True
    )
