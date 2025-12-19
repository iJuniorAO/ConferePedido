import pandas as pd
import io

# ---------------- FUNÇÕES ---------------- #

def limpa_dataframe(df):
    return (
        df[df["Codigo"].notna()]
        .drop(columns=["Sigla", "Peso"])
        .assign(Codigo=lambda x: x["Codigo"].astype(str).str.rjust(13))
    )


def prepara_df(df, loja):
    df = df[df[loja] > 0].copy()

    df["QtCx"] = df[loja] * df["conv"]
    df["QtCx"] = df["QtCx"].apply(
        lambda x: f"{x:09.3f}".replace(".", ",") if pd.notna(x) else "E"
    )

    df.insert(0, loja, df["Codigo"])

    return df[[loja, "QtCx"]]


def converter_txt(df):
    output = io.StringIO()
    df.to_csv(output, sep="\t", index=False, decimal=",")
    return output.getvalue()


# ---------------- EXECUÇÃO ---------------- #

df = limpa_dataframe(xl("Produtos!A1:H800", headers=True))

loja = xl("Pedido1!G2")

# separa por tipo de forma dinâmica
dfs_por_tipo = {
    tipo: df[(df["Tipo"] == tipo) & df[loja].notna()]
    for tipo in ["S", "C", "P"]
}

dfsecoLoja = prepara_df(dfs_por_tipo["S"], loja)
txt_seco = converter_txt(dfsecoLoja)
