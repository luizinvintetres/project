# 📜 Histórico de Inserções Manuais
import streamlit as st
from services.supabase_client import supabase, get_transactions, get_saldos

def render_history_panel(user_email: str) -> None:
    st.divider()
    with st.expander("📜 Histórico de Inserções Manuais", expanded=True):
        st.subheader("📜 Inserções Manuais Recentes")

        # Carrega contas e fundos para referência
        accounts = supabase.table("accounts").select("acct_id,nickname,fund_id").execute().data or []
        funds = supabase.table("funds").select("fund_id,name").execute().data or []
        acct_map = {a["acct_id"]: a["nickname"] for a in accounts}
        fund_map = {f["fund_id"]: f["name"] for f in funds}
        acct_to_fund = {a["acct_id"]: fund_map.get(a["fund_id"], "—") for a in accounts}

        # — Transações Manuais —
        tx_hist = (
            supabase.table("transactions")
            .select("acct_id,date,description,amount")
            .eq("uploader_email", user_email)
            .is_("filename", "null")
            .execute()
            .data or []
        )

        if tx_hist:
            st.markdown("**Transações Manuais**")
            for idx, tx in enumerate(tx_hist):
                cols = st.columns([1.5, 3, 2, 2, 0.7])
                cols[0].write(f"📅 {tx['date']}")
                cols[1].write(f"📝 {tx['description']}")
                cols[2].write(f"🏦 {acct_map.get(tx['acct_id'], '—')}")
                cols[3].write(f"📁 {acct_to_fund.get(tx['acct_id'], '—')}")
                if cols[4].button("❌", key=f"del_tx_{idx}"):
                    supabase.from_("transactions") \
                        .delete() \
                        .eq("acct_id", tx["acct_id"]) \
                        .eq("date", tx["date"]) \
                        .eq("description", tx["description"]) \
                        .eq("amount", tx["amount"]) \
                        .eq("uploader_email", user_email) \
                        .execute()
                    get_transactions.clear()
                    st.success("Transação removida.")
        else:
            st.info("Nenhuma transação manual encontrada.")

        st.markdown("---")

        # — Saldos Manuais —
        sal_hist = (
            supabase.table("saldos")
            .select("acct_id,date,opening_balance")
            .eq("uploader_email", user_email)
            .is_("filename", "null")
            .execute()
            .data or []
        )

        if sal_hist:
            st.markdown("**Saldos Manuais**")
            for idx, sal in enumerate(sal_hist):
                cols = st.columns([1.5, 2.5, 2, 0.7])
                cols[0].write(f"📅 {sal['date']}")
                cols[1].write(f"💼 R$ {sal['opening_balance']:,.2f}")
                cols[2].write(f"🏦 {acct_map.get(sal['acct_id'], '—')}")
                if cols[3].button("❌", key=f"del_sal_{idx}"):
                    supabase.from_("saldos") \
                        .delete() \
                        .eq("acct_id", sal["acct_id"]) \
                        .eq("date", sal["date"]) \
                        .eq("uploader_email", user_email) \
                        .execute()
                    get_saldos.clear()
                    st.success("Saldo removido.")
                    st.experimental_rerun()
        else:
            st.info("Nenhum saldo manual encontrado.")
