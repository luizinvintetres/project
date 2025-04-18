from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from services import supabase_client as db

def _metrics(df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)
    total_in = df.loc[df["amount"] > 0, "amount"].sum()
    total_out = df.loc[df["amount"] < 0, "amount"].sum()
    net = total_in + total_out
    col1.metric("Entradas", f"R$ {total_in:,.2f}")
    col2.metric("Saídas", f"R$ {total_out:,.2f}")
    col3.metric("Saldo Líquido", f"R$ {net:,.2f}")

def render() -> None:
    st.header("📊 Dashboard Geral")
    tx = db.get_transactions()
    if tx.empty:
        st.info("Nenhuma transação disponível.")
        return

    acc = db.get_accounts()[["acct_id", "nickname", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]]
    df = (
        tx
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    # Filtros
    sel_fund = st.multiselect("Fundos", sorted(df["fund"].unique()))
    if sel_fund:
        df = df[df["fund"].isin(sel_fund)]
    sel_acct = st.multiselect("Contas", sorted(df["account"].unique()))
    if sel_acct:
        df = df[df["account"].isin(sel_acct)]

    # Slider de datas
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    start, end = st.slider(
        "Período de Visualização",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )
    df = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)]

    # Métricas
    _metrics(df)

    # Agrupar por data e somar entradas/saídas
    df_daily = (
        df.groupby("date")["amount"]
        .sum()
        .reset_index()
        .sort_values("date")
    )

    # Gráfico de barras empilhadas (positivas e negativas)
    chart = alt.Chart(df_daily).mark_bar().encode(
        x=alt.X("date:T", title="Data"),
        y=alt.Y("amount:Q", title="Valor"),
        color=alt.condition(
            "datum.amount >= 0",
            alt.value("steelblue"),  # Entradas
            alt.value("crimson")     # Saídas
        ),
        tooltip=["date:T", "amount:Q"]
    ).properties(height=300)

    st.altair_chart(chart, use_container_width=True)

    # Tabela
    st.dataframe(df[["date", "fund", "account", "description", "amount"]])
