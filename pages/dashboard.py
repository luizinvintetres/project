"""
Renderiza o dashboard geral
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from services import supabase_client as db

def _metrics(df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)
    total_in  = df.loc[df["amount"] > 0, "amount"].sum()
    total_out = df.loc[df["amount"] < 0, "amount"].sum()
    net       = total_in + total_out
    col1.metric("Entradas",       f"R$ {total_in:,.2f}")
    col2.metric("Saídas",         f"R$ {total_out:,.2f}")
    col3.metric("Saldo Líquido",  f"R$ {net:,.2f}")

def render() -> None:
    st.header("📊 Dashboard Geral")
    tx = db.get_transactions()
    if tx.empty:
        st.info("Nenhuma transação disponível.")
        return

    # Enriquecimento • join em conta + fundo
    acc  = db.get_accounts()[["acct_id", "nickname", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]]
    df = (
        tx
        .merge(acc,  on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    # Filtros interativos
    sel_fund = st.multiselect("Fundos", sorted(df["fund"].unique()))
    if sel_fund:
        df = df[df["fund"].isin(sel_fund)]
    sel_acct = st.multiselect("Contas", sorted(df["account"].unique()))
    if sel_acct:
        df = df[df["account"].isin(sel_acct)]

    # Métricas
    _metrics(df)

    # Gráfico de saldo acumulado
    plot_df = df.sort_values("date").assign(balance=lambda d: d["amount"].cumsum())
    chart = alt.Chart(plot_df).mark_line().encode(
        x="date:T",
        y="balance:Q",
        tooltip=["date:T", "balance:Q"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    st.dataframe(df[["date", "fund", "account", "description", "amount"]])
