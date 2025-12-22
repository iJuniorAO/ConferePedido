import pandas as pd

#CONST INICIAÇÃO
colunas_Pedidos = [
    "QtCx",
    "Sigla",
    "Descricao"
]


def importa_pedido_loja(caminho_arquivo):
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\Brigadeiro2.txt"
    df_Import_loja = pd.read_csv(caminho_arquivo, sep="|", header=None, encoding="latin1")

    #Importa e prepara o df
    df_Import_loja[colunas_Pedidos] = (
        df_Import_loja[0]
        .astype(str)
        .str.split(" ", n=2, expand=True)
    )

    df_Import_loja = df_Import_loja.drop(columns=[0,"Sigla"])

    #Separa os pedidos em 2 df um com erros e outro sem erros
    num = pd.to_numeric(df_Import_loja["QtCx"], errors="coerce")
    df_ok = df_Import_loja[num.notna()]
    df_erro = df_Import_loja[num.isna()]
    df_ok.loc[:,"QtCx"] = df_ok["QtCx"].astype(float)
    
    return df_ok, df_erro


caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\Brigadeiro2.txt"
df_Pedido_Loja, df_Erro_Loja = importa_pedido_loja(caminho_arquivo)

print(f"\n🟢 Pedido Lojas:\n{df_Pedido_Loja}\n\n")
if not df_Erro_Loja.empty:
    print(f"\n❌ Linhas com Erro:\n{df_Erro_Loja}\n\n")