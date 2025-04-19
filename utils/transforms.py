"""
Funções auxiliares de ETL para uploads de extratos
"""
from __future__ import annotations
import pandas as pd
from services import supabase_client as db

# Mapeia variações de nomes de coluna → padrão
_COL_MAP = {
    "date": "date", "data": "date",
    "descricao": "description", "desc": "description",
    "valor": "amount", "amount": "amount",
}

def clean_statement(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe DataFrame vindo de CSV/XLSX, padroniza colunas e
    devolve colunas esperadas: date, description, amount, liquidation
    """
    df = df_raw.copy()
    df.columns = df.columns.str.lower().str.strip()
    df = df.rename(columns={c: _COL_MAP.get(c, c) for c in df.columns})
    df = df[["date", "description", "amount"]]
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["liquidation"] = df["description"].str.contains("liquid", case=False, na=False)
    return df.dropna(subset=["date", "amount"])


def filter_already_imported_by_file(
    df: pd.DataFrame,
    acct_id: str,
    filename: str,
    uploader_email: str
) -> pd.DataFrame:
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"]).dt.date

    # agora passa também o filename
    imported = db.get_imported_dates(acct_id, filename)
    df_new = df2[~df2["date"].isin(imported)]

    if not df_new.empty:
        db.add_import_log(
            acct_id,
            set(df_new["date"]),
            filename,
            uploader_email
        )
    return df_new
