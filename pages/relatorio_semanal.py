from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from services import supabase_client as db


@st.cache_data(show_spinner=False)
def _load_joined_transactions() -> pd.DataFrame:
    tx = db.get_transactions()
    if tx.empty:
        return tx

    accounts = db.get_accounts()[["acct_id", "fund_id"]]
    funds = db.get_funds()[["fund_id", "name"]]
    return (
        tx.merge(accounts, on="acct_id", how="left")
          .merge(funds, on="fund_id", how="left")
    )


def _week_window(offset: int) -> tuple[datetime.date, datetime.date]:
    """Dado um deslocamento em semanas (0 = semana atual),
    devolve (segunda, domingo) do intervalo."""
    today = datetime.today().date()
    monday = today - timedelta(days=today.weekday())          # segunda desta semana
    start = monday + timedelta(weeks=offset)
    end   = start + timedelta(days=6)
    return start, end


def render() -> None:
    st.header("🗓️ Relatório Semanal — Resumo por Fundo")

    tx = _load_joined_transactions()
    if tx.empty:
        st.info("Sem transações para relatório.")
        return

    # -----------------------------------------------------------------
    # Navegação entre semanas  ◀  ▶
    # -----------------------------------------------------------------
    if "week_offset" not in st.session_state:
        st.session_state.week_offset = 0          # 0 = semana atual

    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.button("◀", help="Semana anterior"):
            st.session_state.week_offset -= 1

    # calcula intervalo da semana desejada
    start, end = _week_window(st.session_state.week_offset)

    with cols[2]:
        disable_next = st.session_state.week_offset == 0
        if st.button("▶", disabled=disable_next, help="Próxima semana"):
            st.session_state.week_offset += 1     # só habilita se não for futuro

    # título central com o intervalo
    cols[1].markdown(
        f"<div style='text-align:center; font-weight:600;'>"
        f"{start.strftime('%d/%m/%Y')} ➜ {end.strftime('%d/%m/%Y')}</div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------
    # Filtro de transações da semana selecionada
    # -----------------------------------------------------------------
    weekly = tx[(tx["date"].dt.date >= start) & (tx["date"].dt.date <= end)]
    if weekly.empty:
        st.warning("Nenhuma transação nesse intervalo.")
        return

    # -----------------------------------------------------------------
    # Saldo de abertura = saldo acumulado até o dia anterior ao início
    # -----------------------------------------------------------------
    df_sorted = (
        tx.sort_values("date")
          .assign(balance=lambda d: d.groupby("fund_id")["amount"].cumsum())
    )
    abertura = (
        df_sorted[df_sorted["date"].dt.date < start]
        .groupby("fund_id")["balance"]
        .last()
        .rename("Saldo de Abertura")
    )

    # -----------------------------------------------------------------
    # Métricas dos sete dias
    # -----------------------------------------------------------------
    entradas = (
        weekly[weekly["amount"] > 0]
        .groupby("fund_id")["amount"].sum()
        .rename("Entradas (7 d)")
    )
    saidas = (
        weekly[weekly["amount"] < 0]
        .groupby("fund_id")["amount"].sum()
        .rename("Saídas (7 d)")
    )
    liquida = (
        weekly[weekly["liquidation"]]
        .groupby("fund_id")["amount"].sum()
        .rename("Liquidações")
    )

    # -----------------------------------------------------------------
    # Resumo final
    # -----------------------------------------------------------------
    summary = pd.concat([abertura, entradas, saidas, liquida], axis=1).fillna(0)

    funds_all = db.get_funds()[["fund_id", "name"]]
    summary = (
        summary
        .merge(funds_all, on="fund_id")
        .rename(columns={"name": "Nome do fundo"})
    )[
        ["Nome do fundo", "Saldo de Abertura", "Entradas (7 d)",
         "Saídas (7 d)", "Liquidações"]
    ].reset_index(drop=True)

    # -----------------------------------------------------------------
    # Formatação
    # -----------------------------------------------------------------
    currency_cols = ["Saldo de Abertura", "Entradas (7 d)",
                     "Saídas (7 d)", "Liquidações"]
    display_df = summary.copy()
    for col in currency_cols:
        display_df[col] = display_df[col].map(lambda x: f"R$ {x:,.2f}")

    st.dataframe(display_df, use_container_width=True)
