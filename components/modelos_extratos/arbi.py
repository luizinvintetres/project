# components/modelos_extratos/arbi.py
import pandas as pd

def read(file) -> pd.DataFrame:
    # Carrega com cabeçalho na linha 7
    df = pd.read_excel(file, header=7)

    # Renomear colunas úteis
    df = df.rename(columns={
        df.columns[4]: "date",
        df.columns[10]: "description",
        df.columns[8]: "amount",
        df.columns[7]: "nature"
    })

    # Limpeza
    df = df[["date", "description", "amount", "nature"]]
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    # Débitos serão negativos
    df["amount"] = df.apply(
        lambda row: -row["amount"] if row["nature"].strip().upper() == "D" else row["amount"],
        axis=1
    )

    # Campo de liquidação inferido por palavra-chave
    df["liquidation"] = df["description"].str.contains("liquid", case=False, na=False)

    return df.drop(columns=["nature"]).dropna(subset=["date", "amount"])
