import importlib
from datetime import datetime, date
import streamlit as st
from services.supabase_client import supabase, get_saldos, get_transactions
from utils.transforms import filter_already_imported_by_file, filter_new_transactions

def render_upload_panel(user_email: str) -> None:
    st.subheader("📥 Upload de Extrato")
    accounts = supabase.from_("accounts").select("acct_id,nickname").execute().data or []
    if not accounts:
        st.info("Cadastre contas para habilitar uploads.")
        return
    acct_opts = {r['nickname']: r['acct_id'] for r in accounts}
    sel_acct = st.selectbox("Conta", list(acct_opts.keys()), key="admin_sel_acct")
    model_map = {"Arbi": "arbi"}
    sel_model = st.selectbox("Modelo de Extrato", list(model_map.keys()), key="admin_sel_model")
    file = st.file_uploader("Extrato", type=["csv","xlsx","xls"], key="admin_file")

    if file and st.button("Enviar agora", key="admin_upl_send"):
        try:
            parser = importlib.import_module(f"components.modelos_extratos.{model_map[sel_model]}")
            tx_df, bal_df = parser.read(file)
            # upsert saldos
            for _, r in bal_df.iterrows():
                d = r['date']
                date_str = d.strftime("%Y-%m-%d") if isinstance(d, (datetime, date)) else str(d)
                payload = {
                    "acct_id": acct_opts[sel_acct],
                    "date": date_str,
                    "opening_balance": float(r["opening_balance"]),
                    "filename": file.name,
                    "uploader_email": user_email,
                }
                supabase.from_("saldos").upsert([payload]).execute()
            get_saldos.clear()
            st.success(f"{len(bal_df)} saldos de abertura cadastrados.")

            # insert transactions
            df_file = filter_already_imported_by_file(tx_df, acct_opts[sel_acct], file.name, user_email)
            df_final = filter_new_transactions(df_file, acct_opts[sel_acct])
            if df_final.empty:
                st.warning("Nenhuma transação nova: todas já importadas.")
            else:
                for _, row in df_final.iterrows():
                    supabase.from_("transactions").insert({
                        "acct_id": acct_opts[sel_acct],
                        "date": str(row["date"]),
                        "description": row["description"],
                        "amount": float(row["amount"]),
                        "liquidation": bool(row["liquidation"]),
                        "filename": file.name,
                        "uploader_email": user_email,
                    }).execute()
                st.success(f"{len(df_final)} transações importadas com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar extrato: {e}")