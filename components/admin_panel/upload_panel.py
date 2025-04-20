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
    else:
        acct_opts = {row['nickname']: row['acct_id'] for row in accounts}
        sel_acct = st.selectbox("Conta", list(acct_opts.keys()), key="admin_sel_acct")
        model_options = {"Arbi": "arbi"}
        sel_model = st.selectbox(
            "Modelo de Extrato", list(model_options.keys()), key="admin_sel_model"
        )
        file = st.file_uploader("Extrato", type=["csv", "xlsx", "xls"], key="admin_file")

        if file and st.button("Enviar agora", key="admin_upl_send"):
            try:
                # Parser retorna (transactions, balances)
                parser = importlib.import_module(
                    f"components.modelos_extratos.{model_options[sel_model]}"
                )
                tx_df, bal_df = parser.read(file)

                # Insere saldos de abertura (upsert)
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

                # Limpa cache de saldos para refletir imediatamente
                get_saldos.clear()
                st.success(f"{len(bal_df)} saldos de abertura cadastrados.")

                # Filtra e insere transações novas
                # primeiro filtra por arquivo (opcional, se quiser manter o log por filename)
                df_file_filtered = filter_already_imported_by_file(
                    tx_df,
                    acct_opts[sel_acct],
                    file.name,
                    user_email
                )
                # depois filtra transação a transação contra o banco
                df_final = filter_new_transactions(
                    df_file_filtered,
                    acct_opts[sel_acct]
                )
                df_new = df_final
                if df_new.empty:
                    st.warning("Nenhuma transação nova: todas já importadas.")
                else:
                    for _, row in df_new.iterrows():
                        supabase.from_("transactions").insert(
                            {
                                "acct_id": acct_opts[sel_acct],
                                "date": str(row["date"]),
                                "description": row["description"],
                                "amount": float(row["amount"]),
                                "liquidation": bool(row["liquidation"]),
                                "filename": file.name,
                                "uploader_email": user_email,
                            }
                        ).execute()
                    st.success(f"{len(df_new)} transações importadas com sucesso!")

            except Exception as e:
                st.error(f"Erro ao importar extrato: {e}")