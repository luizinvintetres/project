"""
Funções auxiliares de ETL para uploads de extratos
"""
from __future__ import annotations
import pandas as pd

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
    df = df[["date", "description", "amount"]]        # dropa o resto
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["liquidation"] = df["description"].str.contains("liquid", case=False, na=False)
    return df.dropna(subset=["date", "amount"])

from services import supabase_client as db

def filter_already_imported(df: pd.DataFrame, acct_id: str) -> pd.DataFrame:
    """
    Remove do DataFrame as linhas com datas já registradas em import_log para a conta.
    Registra as novas datas no log após o filtro.
    """
    # Garante que a coluna date é do tipo datetime.date
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Datas já importadas
    imported = db.get_imported_dates(acct_id)

    # Filtra
    df_new = df[~df["date"].isin(imported)]

    # Atualiza log
    if not df_new.empty:
        db.add_import_log(acct_id, set(df_new["date"]))

    return df_new
