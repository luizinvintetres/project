"""
Conexão e wrappers de cache para o Supabase
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from supabase import create_client, Client
from datetime import date

# -----------------------------------------------------------------------------
# Conexão única
# -----------------------------------------------------------------------------
_url: str = st.secrets["SUPABASE_URL"]
_key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(_url, _key)

# -----------------------------------------------------------------------------
# Helpers de leitura (cacheados)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_funds() -> pd.DataFrame:
    resp = supabase.table("funds").select("*").execute()
    return pd.DataFrame(resp.data or [])

@st.cache_data(show_spinner=False)
def get_accounts() -> pd.DataFrame:
    resp = supabase.table("accounts").select("*").execute()
    return pd.DataFrame(resp.data or [])

@st.cache_data(show_spinner=False)
def get_transactions() -> pd.DataFrame:
    resp = supabase.table("transactions").select("*").execute()
    df = pd.DataFrame(resp.data or [])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data(show_spinner=False)
def get_saldos() -> pd.DataFrame:
    """
    Recupera saldos de abertura do banco.
    Columns: acct_id, date (date), opening_balance (float), uploader_email
    """
    resp = supabase.table("saldos").select("*").execute()
    df = pd.DataFrame(resp.data or [])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])  # keep datetime for merging
    return df

# -----------------------------------------------------------------------------
# Helpers de escrita (limpam caches)
# -----------------------------------------------------------------------------
def insert_fund(data: dict) -> None:
    supabase.table("funds").insert(data).execute()
    get_funds.clear()

def insert_account(data: dict) -> None:
    supabase.table("accounts").insert(data).execute()
    get_accounts.clear()

def insert_transaction(data: dict) -> None:
    supabase.table("transactions").insert(data).execute()
    get_transactions.clear()

# -----------------------------------------------------------------------------
# Import logs e saldos
# -----------------------------------------------------------------------------

def get_imported_dates(acct_id: str) -> set[date]:
    resp = (
        supabase
        .table("import_log")
        .select("import_date")
        .eq("acct_id", acct_id)
        .execute()
    )
    return {date.fromisoformat(r["import_date"]) for r in (resp.data or [])}


def add_import_log(
    acct_id: str,
    dates: set[date],
    filename: str,
    uploader_email: str
) -> None:
    if not dates:
        return
    payload = [
        {
            "acct_id": acct_id,
            "import_date": d.isoformat(),
            "filename": filename,
            "uploader_email": uploader_email,
        }
        for d in dates
    ]
    supabase.table("import_log").upsert(payload).execute()
    get_import_logs.clear()

@st.cache_data(show_spinner=False)
def get_import_logs() -> pd.DataFrame:
    resp = supabase.table("import_log").select("*").execute()
    return pd.DataFrame(resp.data or [])


def delete_file_records(filename: str, uploader_email: str | None = None) -> None:
    # Apaga transações associadas ao arquivo
    supabase.table("transactions").delete().eq("filename", filename).execute()
    # Apaga logs de importação, opcionalmente filtrando por usuário
    query = supabase.table("import_log").delete().eq("filename", filename)
    if uploader_email:
        query = query.eq("uploader_email", uploader_email)
    query.execute()
    get_transactions.clear()
    get_import_logs.clear()
