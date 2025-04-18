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

    if acc.empty or funds.empty:
        st.warning("Você precisa cadastrar fundos e contas antes de visualizar o dashboard.")
        return

    df = (
        tx
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    if "fund" not in df.columns or "account" not in df.columns:
        st.warning("Erro ao preparar os dados: verifique se há contas e fundos corretamente relacionados.")
        return

    # Filtros
    sel_fund = st.multiselect("Fundos", sorted(df["fund"].dropna().unique()))
    if sel_fund:
        df = df[df["fund"].isin(sel_fund)]

    sel_acct = st.multiselect("Contas", sorted(df["account"].dropna().unique()))
    if sel_acct:
        df = df[df["account"].isin(sel_acct)]

    if df.empty:
        st.warning("Nenhuma transação encontrada para os filtros aplicados.")
        return

    # Filtro por período (slider)
    min_date, max_date = df["date"].min(), df["date"].max()
    start, end = st.slider(
        "Período de Visualização",
        min_value=min_date.date(),
        max_value=max_date.date(),
        value=(min_date.date(), max_date.date())
    )
    df = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)]

    if df.empty:
        st.warning("Nenhuma transação no intervalo selecionado.")
        return

    _metrics(df)

    # Agrupar por data e somar entradas/saídas
    df_daily = (
        df.groupby("date")["amount"]
        .sum()
        .reset_index()
        .sort_values("date")
    )

    # Gráfico de barras coloridas (positivo = azul, negativo = vermelho)
    chart = alt.Chart(df_daily).mark_bar().encode(
        x=alt.X("date:T", title="Data"),
        y=alt.Y("amount:Q", title="Valor"),
        color=alt.Color("type:N", scale=alt.Scale(domain=["Entrada", "Saída"], range=["steelblue", "crimson"])),
        column=alt.Column("type:N", header=alt.Header(labelOrient="bottom")),
        tooltip=["date:T", "amount:Q", "type:N"]
    ).properties(height=300).configure_axisX(labelAngle=-45)

    st.altair_chart(chart, use_container_width=True)

    st.dataframe(df[["date", "fund", "account", "description", "amount"]])
