# components/admin_panel.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import importlib
from services.supabase_client import supabase
from utils.transforms import clean_statement, filter_already_imported_by_file


def render() -> None:
    st.header("⚙️ Administração")

    # ➕ Novo Fundo
    st.subheader("➕ Novo Fundo")
    fund_name = st.text_input("Nome do Fundo", key="admin_fund_name")
    fund_cnpj = st.text_input("CNPJ", key="admin_fund_cnpj")
    fund_admin = st.text_input("Administrador", key="admin_fund_admin")
    if st.button("Adicionar Fundo", key="admin_add_fund") and fund_name:
        supabase.from_("funds").insert(
            {"name": fund_name, "cnpj": fund_cnpj, "administrator": fund_admin}
        ).execute()
        st.success("Fundo adicionado!")

    st.divider()

    # ➕ Nova Conta
    st.subheader("➕ Nova Conta")
    funds = supabase.from_("funds").select("fund_id,name").execute().data or []
    if not funds:
        st.info("Cadastre um fundo antes de criar contas.")
    else:
        fund_options = {row['name']: row['fund_id'] for row in funds}
        sel_fund_name = st.selectbox(
            "Fundo", list(fund_options.keys()), key="admin_sel_fund"
        )
        bank = st.text_input("Banco", key="admin_bank")
        agency = st.text_input("Agência", key="admin_agency")
        number = st.text_input("Número da Conta", key="admin_number")
        nickname = st.text_input("Apelido", key="admin_nickname")
        if st.button("Adicionar Conta", key="admin_add_acct") and bank:
            supabase.from_("accounts").insert(
                {
                    "fund_id": fund_options[sel_fund_name],
                    "bank": bank,
                    "agency": agency,
                    "number": number,
                    "nickname": nickname or f"{bank}-{number}",
                }
            ).execute()
            st.success("Conta adicionada!")

    st.divider()

    # 📥 Upload de Extrato
    st.subheader("📥 Upload de Extrato")
    accounts = supabase.from_("accounts").select("acct_id,nickname").execute().data or []
    if not accounts:
        st.info("Cadastre contas para habilitar uploads.")
    else:
        acct_opts = {row['nickname']: row['acct_id'] for row in accounts}
        sel_acct_nick = st.selectbox(
            "Conta", list(acct_opts.keys()), key="admin_sel_acct"
        )
        model_options = {"Arbi": "arbi"}
        sel_model = st.selectbox(
            "Modelo de Extrato", list(model_options.keys()), key="admin_sel_model"
        )
        file = st.file_uploader("Extrato", type=["csv", "xlsx", "xls"], key="admin_file")

        if file and st.button("Enviar agora", key="admin_upl_send"):
            try:
                parser = importlib.import_module(
                    f"components.modelos_extratos.{model_options[sel_model]}"
                )
                df_raw = parser.read(file)
                df_new = filter_already_imported_by_file(
                    df_raw, acct_opts[sel_acct_nick], file.name
                )
                if df_new.empty:
                    st.warning("Todas as datas deste extrato já foram importadas.")
                else:
                    for _, row in df_new.iterrows():
                        supabase.from_("transactions").insert(
                            {
                                "acct_id": acct_opts[sel_acct_nick],
                                "date": row["date"].strftime("%Y-%m-%d"),
                                "description": row["description"],
                                "amount": float(row["amount"]),
                                "liquidation": bool(row["liquidation"]),
                                "filename": file.name,
                            }
                        ).execute()
                    st.success(
                        f"{len(df_new)} novas transações enviadas com sucesso!"
                    )
            except Exception as e:
                st.error(f"Erro ao importar extrato: {e}")

    st.divider()

    # 🧾 Arquivos importados
    st.subheader("🧾 Arquivos importados")
    logs = supabase.from_("import_log").select("filename").execute().data or []
    if not logs:
        st.info("Nenhum arquivo foi importado ainda.")
    else:
        filenames = sorted({row["filename"] for row in logs if row.get("filename")})
        for f in filenames:
            col1, col2 = st.columns([6, 1])
            col1.write(f)
            if col2.button("❌", key=f"admin_del_{f}"):
                supabase.from_("import_log").delete().eq("filename", f).execute()
                st.success(f"Registros do arquivo '{f}' apagados.")
