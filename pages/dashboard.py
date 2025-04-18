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
    acc = db.get_accounts()[["acct_id", "nickname", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]]

    if tx.empty or acc.empty or funds.empty:
        st.info("Cadastre fundos, contas e transações para visualizar o dashboard.")
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
    if not sel_fund:
        st.info("Selecione ao menos um fundo para visualizar os dados.")
        return

    df = df[df["fund"].isin(sel_fund)]

    sel_acct = st.multiselect("Contas", sorted(df["account"].dropna().unique()))
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

    if df.empty:
        st.warning("Nenhuma transação encontrada no período selecionado.")
        return

    # Métricas
    _metrics(df)

    # Agrupar por data e tipo de transação
    df["tipo"] = df["amount"].apply(lambda x: "Entrada" if x > 0 else "Saída")
    df_grouped = (
        df.groupby([df["date"].dt.date, "tipo"])["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "Data", "amount": "Valor", "tipo": "Tipo"})
    )

    # Gráfico de barras lado a lado
    chart = alt.Chart(df_grouped).mark_bar().encode(
        x=alt.X("Data:T", title="Data"),
        y=alt.Y("Valor:Q", title="Valor"),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Entrada", "Saída"], range=["steelblue", "crimson"])),
        tooltip=["Data:T", "Tipo:N", "Valor:Q"]
    ).properties(height=350)

    st.altair_chart(chart, use_container_width=True)

    # Tabela
    st.dataframe(df[["date", "fund", "account", "description", "amount"]].sort_values("date"))
    