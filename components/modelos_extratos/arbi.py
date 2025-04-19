import pandas as pd
from typing import Tuple

def read(file) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lê o extrato Arbi e retorna duas DataFrames:
      - transactions: colunas ['date','description','amount','liquidation']
      - balances: colunas ['date','opening_balance']

    Os saldos de abertura são extraídos da coluna index 1 do arquivo bruto,
    convertidos para float, agrupados por dia (primeiro valor do dia).
    """
    # Leitura bruta do arquivo
    raw = pd.read_excel(file, header=7)

    # --- Extrai e limpa saldos de abertura ---
    date_series = pd.to_datetime(
        raw.iloc[:, 4], dayfirst=True, errors="coerce"
    ).dt.date
    balance_raw = raw.iloc[:, 1].astype(str)
    # Remove separadores de milhar e ajusta vírgula decimal
    balance_clean = (
        balance_raw
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    # Filtra apenas valores numéricos válidos
    mask_bal = balance_clean.str.replace(".", "", regex=False).str.isnumeric()
    df_balances = pd.DataFrame({
        "date": date_series[mask_bal],
        "opening_balance": balance_clean[mask_bal].astype(float)
    })
    # Agrupa por data e pega o primeiro saldo de cada dia
    df_balances = df_balances.groupby("date", as_index=False).first()

    # --- Prepara transações ---
    df = raw.rename(columns={
        raw.columns[4]: "date",
        raw.columns[9]: "agencia",
        raw.columns[8]: "amount",
        raw.columns[6]: "nature",
        raw.columns[14]: "nome_contraparte",
        raw.columns[0]: "conta_corrente"
    })
    df["description"] = (
        df["agencia"].astype(str).str.strip() + " - " +
        df["conta_corrente"].astype(str).str.strip() + " - " +
        df["nome_contraparte"].astype(str).str.strip()
    )
    df = df[["date", "description", "amount", "nature"]]

    # Converte valores para float (R$ 10.000,50 -> 10000.50)
    amt_raw = df["amount"].astype(str)
    amt_clean = (
        amt_raw
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df = df[amt_clean.str.replace(".", "", regex=False).str.isnumeric()]
    df["amount"] = amt_clean[amt_clean.str.replace(".", "", regex=False).str.isnumeric()].astype(float)

    # Ajusta débitos para valores negativos
    df["amount"] = df.apply(
        lambda row: -row["amount"]
        if str(row["nature"]).strip().upper() == "D"
        else row["amount"],
        axis=1
    )

    # Converte data e define liquidação
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["liquidation"] = df["description"].str.contains(
        "liquid", case=False, na=False
    )

    # Limpa objeto 'nature' e removendo nulos
    transactions = df.drop(columns=["nature"]).dropna(
        subset=["date", "amount", "description"]
    )

    return transactions, df_balances