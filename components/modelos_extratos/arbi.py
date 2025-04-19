import pandas as pd
from typing import Tuple

def read(file) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lê o extrato Arbi e retorna duas DataFrames:
      - transactions: colunas ['date','description','amount','liquidation']
      - balances: colunas ['date','opening_balance']

    Os saldos de abertura são extraídos da coluna index 1 do arquivo bruto,
    agrupados por dia (primeiro valor do dia).
    """
    # Leitura bruta
    raw = pd.read_excel(file, header=7)

    # Extrai saldos de abertura
    # coluna 4 = data, coluna 1 = valor do saldo
    date_series = pd.to_datetime(
        raw.iloc[:, 4], dayfirst=True, errors="coerce"
    ).dt.date
    balance_series = raw.iloc[:, 1]
    df_balances = pd.DataFrame({
        "date": date_series,
        "opening_balance": balance_series
    })
    df_balances = df_balances.dropna(subset=["date", "opening_balance"])
    df_balances = df_balances.groupby("date", as_index=False).first()

    # Prepara DataFrame de transações
    df = raw.rename(columns={
        raw.columns[4]: "date",
        raw.columns[9]: "agencia",
        raw.columns[8]: "amount",
        raw.columns[6]: "nature",
        raw.columns[14]: "nome_contraparte",
        raw.columns[0]: "conta_corrente"
    })
    # Descrição customizada
    df["description"] = (
        df["agencia"].astype(str).str.strip() + " - " +
        df["conta_corrente"].astype(str).str.strip() + " - " +
        df["nome_contraparte"].astype(str).str.strip()
    )
    df = df[["date", "description", "amount", "nature"]]

    # Converte valores para float (R$ 10.000,50 -> 10000.50)
    df["amount"] = (
        df["amount"].astype(str)
           .str.replace(".", "", regex=False)
           .str.replace(",", ".", regex=False)
    )
    df = df[df["amount"].str.replace(".", "", regex=False).str.isnumeric()]
    df["amount"] = df["amount"].astype(float)

    # Ajusta débitos para negativos
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
