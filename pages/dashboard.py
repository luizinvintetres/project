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

    # Criar o DataFrame original mesclado ANTES de aplicar qualquer filtro
    df_original = (
        tx
        .merge(acc, on="acct_id", how="left")
        .merge(funds, on="fund_id", how="left")
        .rename(columns={"nickname": "account", "name": "fund"})
    )

    if "fund" not in df_original.columns or "account" not in df_original.columns:
         st.warning("Erro ao preparar os dados: verifique se há contas e fundos corretamente relacionados.")
         return

    # --- Filtros ---
    # Gerar opções de filtro a partir do DataFrame original
    all_funds = sorted(df_original["fund"].dropna().unique())
    all_accounts = sorted(df_original["account"].dropna().unique())
    min_date_original, max_date_original = df_original["date"].min().date(), df_original["date"].max().date()

    sel_fund = st.multiselect("Fundos", all_funds)
    if not sel_fund:
        st.info("Selecione ao menos um fundo para visualizar os dados.")
        return

    sel_acct = st.multiselect("Contas", all_accounts)

    start, end = st.slider(
        "Período de Visualização",
        min_value=min_date_original,
        max_value=max_date_original,
        value=(min_date_original, max_date_original)
    )

    # --- Aplicar filtros simultaneamente ---
    # Criar máscaras booleanas para cada filtro no DataFrame original
    fund_mask = df_original["fund"].isin(sel_fund)

    # A máscara de conta deve considerar o caso onde nenhum conta é selecionada (mostrar todas)
    if sel_acct:
        account_mask = df_original["account"].isin(sel_acct)
    else:
        account_mask = pd.Series(True, index=df_original.index) # Máscara True para todas as linhas se nenhuma conta for selecionada

    # A máscara de data
    date_mask = (df_original["date"].dt.date >= start) & (df_original["date"].dt.date <= end)

    # Combinar todas as máscaras para obter o DataFrame final filtrado
    df_filtered = df_original[fund_mask & account_mask & date_mask]

    # --- Verificar se há dados após a aplicação dos filtros ---
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado para a combinação de filtros selecionada.")
        return

    # --- Continuar com as visualizações usando df_filtered ---

    # Métricas
    _metrics(df_filtered)

    # Agrupar por data e somar entradas/saídas (usando df_filtered)
    df_daily = (
        df_filtered.groupby("date")["amount"]
        .sum()
        .reset_index()
        .sort_values("date")
    )

    # Gráfico (usando df_daily)
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

    # Tabela (usando df_filtered)
    st.dataframe(df_filtered[["date", "fund", "account", "description", "amount"]])