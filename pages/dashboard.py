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

    # Carrega transações e converte data
    tx = db.get_transactions()
    if tx.empty:
        st.info("Nenhuma transação disponível.")
        return
    tx['date'] = pd.to_datetime(tx['date'])

    # Carrega contas e fundos
    acc = db.get_accounts()[["acct_id", "nickname", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]].drop_duplicates()
    if acc.empty or funds.empty:
        st.warning("Você precisa cadastrar fundos e contas antes de visualizar o dashboard.")
        return

    # Faz merge apenas de registros válidos (inner) para garantir fund关联
    df = (
        tx
        .merge(acc, on="acct_id", how="inner")
        .merge(funds, on="fund_id", how="inner")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    # Filtro de fundos usando todos os fundos cadastrados
    all_funds = sorted(funds['name'].tolist())
    sel_fund = st.multiselect("Fundos", all_funds)
    if not sel_fund:
        st.info("Selecione ao menos um fundo para visualizar os dados.")
        return
    df = df[df["fund"].isin(sel_fund)]

    # Filtro de contas, opcional
    all_accounts = sorted(df["account"].unique().tolist())
    sel_acct = st.multiselect("Contas", all_accounts)
    if sel_acct:
        df = df[df["account"].isin(sel_acct)]

    # Slider de período com base no dataframe filtrado
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    start_date, end_date = st.slider(
        "Período de Visualização",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )
    df = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]

    if df.empty:
        st.warning("Não há dados para o período e filtros selecionados.")
        return

    # Exibe métricas
    _metrics(df)

    # Prepara dados diários para o gráfico
    df_daily = (
        df
        .groupby(df["date"].dt.date)["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "date", "amount": "amount"})
        .sort_values("date")
    )

    # Gráfico de barras
    chart = alt.Chart(df_daily).mark_bar().encode(
        x=alt.X("date:T", title="Data"),
        y=alt.Y("amount:Q", title="Valor"),
        color=alt.condition(
            "datum.amount >= 0",
            alt.value("steelblue"),
            alt.value("crimson")
        ),
        tooltip=["date:T", "amount:Q"]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    # Tabela de transações filtradas
    st.dataframe(df[["date", "fund", "account", "description", "amount"]])
