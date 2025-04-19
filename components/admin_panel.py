"""
components/admin_panel.py
"""
from __future__ import annotations

import importlib
from datetime import datetime, date

import streamlit as st 

from services.supabase_client import (
    supabase,
    get_saldos,
    get_transactions,
    delete_file_records,
)
from utils.transforms import filter_already_imported_by_file, filter_new_transactions


def render() -> None:
    st.header("⚙️ Administração")

    # Captura e-mail do usuário
    user_email = st.session_state.user.email

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

    # 📥 Upload de Extrato e inserção de saldos e transações
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

    st.divider()

    # 🧾 Meus Arquivos importados
    st.subheader("🧾 Meus Arquivos importados")
    logs = (
        supabase.from_("import_log")
        .select("filename")
        .eq("uploader_email", user_email)
        .execute()
        .data
        or []
    )
    if not logs:
        st.info("Você ainda não importou nenhum arquivo.")
    else:
        filenames = sorted({r["filename"] for r in logs if r.get("filename")})
        for f in filenames:
            col1, col2 = st.columns([6, 1])
            col1.write(f)
            if col2.button("❌", key=f"admin_del_{f}"):
                # Usa lógica centralizada para apagar todos os registros do arquivo
                delete_file_records(filename=f, uploader_email=user_email)
                st.success(f"Registros do arquivo '{f}' foram apagados.")
                return

    # — Transação Manual —
        st.markdown("**Transação Manual**")
        manual_date = st.date_input("Data", key="manual_tx_date")

        funds = supabase.from_("funds").select("fund_id,name").execute().data or []
        fund_options = {row["name"]: row["fund_id"] for row in funds}
        manual_fund = st.selectbox("Fundo (Transação)", list(fund_options.keys()), key="manual_tx_fund")

        accounts = supabase.from_("accounts").select("acct_id,nickname").execute().data or []
        acct_options = {row["nickname"]: row["acct_id"] for row in accounts}
        manual_acct = st.selectbox("Conta (Transação)", list(acct_options.keys()), key="manual_tx_acct")

        manual_amount = st.text_input("Valor (use vírgula para decimal)", key="manual_tx_amount")
        manual_desc   = st.text_input("Descrição", key="manual_tx_desc")

        if st.button("Adicionar Transação", key="manual_tx_add"):
            val = float(manual_amount.replace(".", "").replace(",", "."))
            supabase.from_("transactions").insert({
                "acct_id":       acct_options[manual_acct],
                "date":          manual_date.isoformat(),
                "description":   manual_desc,
                "amount":        val,
                "liquidation":   False,
                "filename":      None,
                "uploader_email": user_email,
            }).execute()
            # limpa cache para refletir imediatamente
            get_transactions.clear()
            st.success("Transação adicionada manualmente.")

        # — Saldo Manual —
        st.markdown("**Saldo Manual**")
        manual_saldo_date   = st.date_input("Data", key="manual_saldo_date")
        manual_saldo_fund   = st.selectbox("Fundo (Saldo)", list(fund_options.keys()), key="manual_saldo_fund")
        manual_saldo_acct   = st.selectbox("Conta (Saldo)", list(acct_options.keys()), key="manual_saldo_acct")
        manual_saldo_amount = st.text_input("Valor (use vírgula para decimal)", key="manual_saldo_amount")

        if st.button("Adicionar Saldo", key="manual_saldo_add"):
            sbal = float(manual_saldo_amount.replace(".", "").replace(",", "."))
            supabase.from_("saldos").upsert([{
                "acct_id":         acct_options[manual_saldo_acct],
                "date":            manual_saldo_date.isoformat(),
                "opening_balance": sbal,
                "filename":        None,
                "uploader_email":  user_email,
            }]).execute()
            # limpa cache para refletir imediatamente
            get_saldos.clear()
            st.success("Saldo adicionado manualmente.")

        # 📜 Histórico de Inserções Manuais
        st.divider()
        if st.button("📜 Histórico de Inserções Manuais"):
            st.subheader("📜 Inserções Manuais Recentes")

            # — Transações Manuais do Usuário —
            tx_hist = (
                supabase
                .from_("transactions")
                .select("id,date,description,amount,liquidation")
                .eq("uploader_email", user_email)
                .is_("filename", "is.null")
                .execute()
                .data
                or []
            )
            if tx_hist:
                st.markdown("**Transações Manuais**")
                for row in tx_hist:
                    cols = st.columns([1.5, 3, 2, 1, 0.5])
                    cols[0].write(f"📅 {row['date']}")
                    cols[1].write(f"📝 {row['description']}")
                    cols[2].write(f"💰 R$ {row['amount']:,.2f}")
                    cols[3].write("✅" if row["amount"] > 0 else "🔻")
                    if cols[4].button("❌", key=f"del_manual_tx_{row['id']}"):
                        supabase.from_("transactions").delete().eq("id", row["id"]).execute()
                        get_transactions.clear()
                        st.success("Transação removida.")
                        st.experimental_rerun()
            else:
                st.info("Nenhuma transação manual encontrada.")

            st.markdown("---")

            # — Saldos Manuais do Usuário —
            sal_hist = (
                supabase
                .from_("saldos")
                .select("id,date,opening_balance")
                .eq("uploader_email", user_email)
                .is_("filename", "is.null")
                .execute()
                .data
                or []
            )
            if sal_hist:
                st.markdown("**Saldos Manuais**")
                for row in sal_hist:
                    cols = st.columns([2, 3, 0.5])
                    cols[0].write(f"📅 {row['date']}")
                    cols[1].write(f"💼 R$ {row['opening_balance']:,.2f}")
                    if cols[2].button("❌", key=f"del_manual_sal_{row['id']}"):
                        supabase.from_("saldos").delete().eq("id", row["id"]).execute()
                        get_saldos.clear()
                        st.success("Saldo removido.")
                        st.experimental_rerun()
            else:
                st.info("Nenhum saldo manual encontrado.")
